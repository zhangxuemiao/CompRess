


# CompRess: Self-Supervised Learning by Compressing Representations

<p align="center">
  <img src="https://user-images.githubusercontent.com/62820830/96925942-ee39c700-1482-11eb-9eb9-9cf98e5a0748.png" width="85%">
</p>

This repository is the official implementation of <a href="https://www.csee.umbc.edu/~hpirsiav/papers/compress_neurips20.pdf">CompRess: Self-Supervised Learning by Compressing Representations</a> 

Project webpage. [https://umbcvision.github.io/CompRess/
](https://umbcvision.github.io/CompRess/) 

```
@Article{abbasi2020compress,
  author  = {Koohpayegani, Soroush Abbasi and Tejankar, Ajinkya and Pirsiavash, Hamed},
  title   = {CompRess: Self-Supervised Learning by Compressing Representations},
  journal = {Advances in neural information processing systems},
  year    = {2020},
}
```

[comment]: <> (📋Optional: include a graphic explaining your approach/main result, bibtex entry, link to demos, blog posts and tutorials)

## Requirements

Install PyTorch and ImageNet dataset following the [official PyTorch ImageNet training code](https://github.com/pytorch/examples/tree/master/imagenet). We used Python 3.7 for our experiments.


- Install PyTorch ([pytorch.org](http://pytorch.org))


To run NN and Cluster Alignment, you require to install FAISS. 

FAISS: 
- Install FAISS ([https://github.com/facebookresearch/faiss/blob/master/INSTALL.md](https://github.com/facebookresearch/faiss/blob/master/INSTALL.md))





[comment]: <>  (📋Describe how to set up the environment, e.g. pip/conda/docker commands, download datasets, etc...)

## Training

Our code is based on unofficial implementation of MoCo from [https://github.com/HobbitLong/CMC](https://github.com/HobbitLong/CMC). 






To train the student(s) using pretrained teachers in the paper :


Download pretrained official MoCo ResNet50 model from [https://github.com/facebookresearch/moco](https://github.com/facebookresearch/moco).

Then train the student using pretrained model: 

```train
python train_student.py \
    --teacher_arch resnet50 \ 
    --teacher <path_to_pretrained_model or cached_features> \
    --student_arch mobilenet \
    --checkpoint_path <path_to_checkpoint_folder> \
    <path_to_imagenet_data>
```
To train the student(s) using cached teachers in the paper :


We converted TensorFlow SimCLRv1 ResNet50x4([https://github.com/google-research/simclr](https://github.com/google-research/simclr)) to PyTorch. Optionally, you can download pretrained SimCLR ResNet50x4 PyTorch model from [here](https://drive.google.com/file/d/1fZ2gfHRjVSFz9Hf2PHsPUao9ZKmUXg4z/view?usp=sharing).

First, run this command to calculate and store cached features.  
```train
python cache_feats.py \ 
    --weight <path_to_pretrained_model> \
    --save <path_to_save_folder> \
    --arch resnet50x4 \ 
    --data_pre_processing SimCLR \ 
    <path_to_imagenet_data>
```


Then train the student using cached features:  

```train
python train_student.py \
    --cache_teacher \ 
    --teacher <path_to_pretrained_model or cached_features> \
    --student_arch mobilenet \
    --checkpoint_path <path_to_checkpoint_folder> \
    <path_to_imagenet_data>
```

To train the student(s) without Momentum framework execute train_student_without_momentum.py instead of train_student.py

[comment]: <> (📋Describe how to train the models, with example commands on how to train the models in your paper, including the full training procedure and appropriate hyperparameters.)
## Evaluation

To run Nearest Neighbor evaluation on ImageNet, run:

```eval
python eval_knn.py \
    --arch alexnet \
    --weights <path_to_pretrained_model> \
    --save <path_to_save_folder> \
    <path_to_imagenet_data>
```
Note that above execution will cache features too. After first execution, you can add "--load_cache" flag to load cached features from a file.   

To run Cluster Alignment evaluation on ImageNet, run:

```eval
python eval_cluster_alignment.py  \
    --weights <path_to_pretrained_model> \
    --arch resnet18  \
    --save <path_to_save_folder> \ 
    --visualization \ 
    --confusion_matrix \ 
    <path_to_imagenet_data> 
```


To run Linear Classifier evaluation on ImageNet, run:

```eval

python eval_linear.py \
    --arch alexnet \
    --weights <path_to_pretrained_model> \
    --save <path_to_save_folder> \
    <path_to_imagenet_data>
```





## Results

<p align="center">
  <img src="https://user-images.githubusercontent.com/62820830/96926014-04e01e00-1483-11eb-87c5-82b4100d56b5.png" width="100%">
</p>

"SOTA Self-Supervised" refers to SimCLR for RexNet50x4 and MoCo for all other architectures.

Our model achieves the following performance on ImageNet:


| Model name         | Teacher | Top-1 Linear Classifier Accuracy | Top-1 Nearest Neighbor Accuracy | Top-1 Cluster Alignment Accuracy| Pre-trained |
| ------------------ | --------- |----------------------------------| ----------------- | ------- | ----------------- |
| CompRess(Resnet50) | SimCLR ResNet50x4(cached) |               71.6%              |        63.4%        | 42.0% | [Pre-trained Resnet50](https://drive.google.com/file/d/15rzzSkcedEuCE7Cm8yLXopA5PqHUQscb/view?usp=sharing) |
| CompRess(Mobilenet)| MoCoV2 ResNet50 |               63.0%              |        54.4%        | 35.5% | [Pre-trained Mobilenet](https://drive.google.com/file/d/1gNkO48iREh6M6uuLd8TGqaOm3ChWiAdc/view?usp=sharing) |
| CompRess(Resnet18) | MoCoV2 ResNet50 |               61.7%              |        53.4%        | 34.7% | [Pre-trained Resnet18](https://drive.google.com/file/d/1L-RCmD4gMeicxJhIeqNKU09_sH8R3bwS/view?usp=sharing) | 
| CompRess(Alexnet)  | SimCLR ResNet50x4(cached) |               57.6%              |        52.3%        | 33.3% | [Pre-trained Alexnet](https://drive.google.com/file/d/1wiEdfk6unXKtYRL1faIMoZMXnShaxBMU/view?usp=sharing) |





## License

This project is under the MIT license.


