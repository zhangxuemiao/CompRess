
from __future__ import print_function

import os
import sys
import time
import torch
import torch.backends.cudnn as cudnn
import argparse
import socket



from torchvision import transforms, datasets
from util import adjust_learning_rate, AverageMeter

from models.resnet import resnet18,resnet50
from models.alexnet import AlexNet as alexnet
from models.mobilenet import MobileNetV2 as mobilenet
from nn.compress_loss import CompReSS_moco, Teacher

import pdb
import torch.nn as nn
import torch.nn.functional as F

from collections import OrderedDict


def parse_option():


    parser = argparse.ArgumentParser('argument for training')

    parser.add_argument('--print_freq', type=int, default=100, help='print frequency')
    parser.add_argument('--tb_freq', type=int, default=500, help='tb frequency')
    parser.add_argument('--save_freq', type=int, default=2, help='save frequency')
    parser.add_argument('--batch_size', type=int, default=256, help='batch_size')
    parser.add_argument('--num_workers', type=int, default=12, help='num of workers to use')
    parser.add_argument('--epochs', type=int, default=130, help='number of training epochs')

    # optimization
    parser.add_argument('--learning_rate', type=float, default=0.01, help='learning rate')
    parser.add_argument('--lr_decay_epochs', type=str, default='90,120', help='where to decay lr, can be a list')
    parser.add_argument('--lr_decay_rate', type=float, default=0.2, help='decay rate for learning rate')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='weight decay')
    parser.add_argument('--momentum', type=float, default=0.9, help='momentum')


    # model definition
    parser.add_argument('--student_model', type=str, default='alexnet',
                        choices=['alexnet' , 'resnet18' , 'resnet50', 'mobilenet'])
    parser.add_argument('--teacher_model', type=str, default='cached',
                        choices=['cached', 'resnet50'])

    # loss function
    parser.add_argument('--compress_memory_size', type=int, default=128000)
    parser.add_argument('--compress_t', type=float, default=0.04)

    # GPU setting
    parser.add_argument('--gpu', default=None, type=int, help='GPU id to use.')

    parser.add_argument('--teacher', type=str, help='teacher weights/feats')

    parser.add_argument('--data', type=str, help='first model')

    parser.add_argument('--checkpoint_path', default='output/', type=str,
                        help='where to save checkpoints. ')


    parser.add_argument('--alpha', type=float, default=0.999, help='exponential moving average weight')

    opt = parser.parse_args()



    iterations = opt.lr_decay_epochs.split(',')
    opt.lr_decay_epochs = list([])
    for it in iterations:
        opt.lr_decay_epochs.append(int(it))



    return opt





class ImageFolderEx(datasets.ImageFolder) :

    def __getitem__(self, index):
        sample, target = super(ImageFolderEx, self).__getitem__(index)
        return index , sample, target


def get_teacher_model(opt):
    teacher = None
    if opt.teacher_model == 'cached':
        # pdb.set_trace()
        train_feats, train_labels, indices = torch.load(opt.teacher)
        teacher = Teacher(cached=True , cached_feats=train_feats)
    elif opt.teacher_model == 'resnet50':
        model_t = resnet50()
        model_t.fc = nn.Sequential()
        model_t = nn.Sequential(OrderedDict([('encoder_q', model_t)]))
        model_t = torch.nn.DataParallel(model_t).cuda()
        checkpoint = torch.load(opt.teacher)
        model_t.load_state_dict(checkpoint['state_dict'], strict=False)
        model_t = model_t.module.cpu()

        for p in model_t.parameters():
            p.requires_grad = False
        teacher = Teacher(cached=False, model=model_t)

    return teacher

def get_student_model(opt):
    student = None
    student_key = None
    if opt.student_model == 'alexnet' :
        student = alexnet()
        student.fc = nn.Sequential()

        student_key = alexnet()
        student_key.fc = nn.Sequential()

    elif opt.student_model == 'mobilenet' :
        student = mobilenet()
        student.fc = nn.Sequential()

        student_key = mobilenet()
        student_key.fc = nn.Sequential()
    elif opt.student_model == 'resnet18' :
        student = resnet18()
        student.fc = nn.Sequential()

        student_key = resnet18()
        student_key.fc = nn.Sequential()
    elif opt.student_model == 'resnet50' :
        student = resnet50(fc_dim=8192)
        student_key = resnet50(fc_dim=8192)


    return student , student_key


def get_train_loader(opt):
    data_folder = os.path.join(opt.data, 'train')
    image_size = 224
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    normalize = transforms.Normalize(mean=mean, std=std)

    train_dataset = ImageFolderEx(
        data_folder,
        transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            normalize,
        ]))

    print(len(train_dataset))
    train_sampler = None
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=opt.batch_size, shuffle=(train_sampler is None),
        num_workers=opt.num_workers, pin_memory=True, sampler=train_sampler)

    return train_loader


def moment_update(model, model_ema, m):
    """ model_ema = m * model_ema + (1 - m) model """
    for p1, p2 in zip(model.parameters(), model_ema.parameters()):
        p2.data.mul_(m).add_(1-m, p1.detach().data)

def main():

    args = parse_option()
    os.makedirs(args.checkpoint_path, exist_ok=True)

    if args.gpu is not None:
        print("Use GPU: {} for training".format(args.gpu))


    train_loader = get_train_loader(args)

    teacher = get_teacher_model(args)
    student , student_key = get_student_model(args)

    data = torch.randn(16, 3, 224, 224)
    teacher.eval()
    student.eval()

    feat_t = teacher.forward(data, 0)
    feat_s = student(data)

    student_feats_dim = feat_s.shape[-1]
    teacher_feats_dim = feat_t.shape[-1]

    compress = CompReSS_moco(teacher_feats_dim , student_feats_dim , args.compress_memory_size , args.compress_t)

    student = torch.nn.DataParallel(student).cuda()
    student_key = torch.nn.DataParallel(student_key).cuda()
    teacher.gpu()

    optimizer = torch.optim.SGD(student.parameters(),
                                lr=args.learning_rate,
                                momentum=args.momentum,
                                weight_decay=args.weight_decay)

    cudnn.benchmark = True

    args.start_epoch = 1
    moment_update(student, student_key, 0)

    # routine
    for epoch in range(args.start_epoch, args.epochs + 1):

        adjust_learning_rate(epoch, args, optimizer)
        print("==> training...")

        time1 = time.time()
        loss = train_student(epoch, train_loader, teacher, student, student_key, compress, optimizer, args)

        time2 = time.time()
        print('epoch {}, total time {:.2f}'.format(epoch, time2 - time1))



        # saving the model
        if epoch % args.save_freq == 0:
            print('==> Saving...')
            state = {
                'opt': args,
                'model': student.state_dict(),
                'optimizer': optimizer.state_dict(),
                'epoch': epoch,
            }

            save_file = os.path.join(args.checkpoint_path, 'ckpt_epoch_{epoch}.pth'.format(epoch=epoch))
            torch.save(state, save_file)

            # help release GPU memory
            del state
            torch.cuda.empty_cache()




def train_student(epoch, train_loader , teacher , student , student_key, compress, optimizer, opt):
    """
    one epoch training for CompReSS
    """
    student_key.eval()
    student.train()

    def set_bn_train(m):
        classname = m.__class__.__name__
        if classname.find('BatchNorm') != -1:
            m.train()
    student_key.apply(set_bn_train)

    batch_time = AverageMeter()
    data_time = AverageMeter()
    loss_meter = AverageMeter()


    end = time.time()
    for idx, (index , inputs, _) in enumerate(train_loader):
        data_time.update(time.time() - end)

        bsz = inputs.size(0)

        inputs = inputs.float()
        if opt.gpu is not None:
            inputs = inputs.cuda(opt.gpu, non_blocking=True)
        else:
            inputs = inputs.cuda()

        # ===================forward=====================

        teacher_feats = teacher.forward(inputs , index)
        student_feats = student(inputs)

        with torch.no_grad():
            student_feats_key = student_key(inputs)
            student_feats_key = student_feats_key.detach()

        loss = compress(teacher_feats , student_feats , student_feats_key)


        # ===================backward=====================
        optimizer.zero_grad()

        loss.backward()
        optimizer.step()

        # ===================meters=====================
        loss_meter.update(loss.item(), bsz)

        moment_update(student, student_key, opt.alpha)

        torch.cuda.synchronize()
        batch_time.update(time.time() - end)
        end = time.time()

        # print info
        if (idx + 1) % opt.print_freq == 0:
            print('Train: [{0}][{1}/{2}]\t'
                  'BT {batch_time.val:.3f} ({batch_time.avg:.3f})\t'
                  'DT {data_time.val:.3f} ({data_time.avg:.3f})\t'
                  'loss {loss.val:.3f} ({loss.avg:.3f})\t'.format(
                   epoch, idx + 1, len(train_loader), batch_time=batch_time,
                   data_time=data_time, loss=loss_meter))
            sys.stdout.flush()

    return loss_meter.avg


if __name__ == '__main__':
    main()
