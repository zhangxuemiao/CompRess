

# CompReSS: Compressing Representations for Self-Supervised Learning

<p align="center">
  <img src="https://user-images.githubusercontent.com/62820830/85651425-f2d9a480-b675-11ea-99e8-8fcf32d0a266.png" width="300">
</p>


This repository is the official implementation of [CompReSS: Compressing Representations for Self-Supervised Learning
](https://arxiv.org/). 

## Abstract

Self-supervised learning aims to learn good representations with unlabeled data. Recent works have shown that larger models benefit more from self-supervised learning than smaller models. As a result, the gap between the supervised and self-supervised learning has been greatly reduced for larger models. In this work, we focus on self-supervised learning for low capacity models that has various applications (e.g., edge computation). We compress a deep teacher model so that the student mimics the relative distances between the datapoints in the teacher embeddings. For ResNet-50, our method outperforms SOTA self-supervised models marginally on ImageNet linear evaluation and with a large margin on nearest neighbor evaluation (by 6 points). For AlexNet, our method outperforms all previous methods including the fully supervised model on ImageNet linear evaluation (57.6% compared to 56.5%) and by a large margin on nearest neighbor evaluation (52.3% compared to 41.4%). This is the first time a self-supervised AlexNet has outperformed supervised one on ImageNet classification.



[comment]: <> (📋Optional: include a graphic explaining your approach/main result, bibtex entry, link to demos, blog posts and tutorials)

## Requirements

To install requirements:

FAISS: 
```setup
# CPU version only
conda install faiss-cpu -c pytorch

# GPU version
conda install faiss-gpu cudatoolkit=10.0 -c pytorch # For CUDA10
```

PyTorch:
```setup
conda install pytorch torchvision cudatoolkit=10.1 -c pytorch
```


[comment]: <>  (📋Describe how to set up the environment, e.g. pip/conda/docker commands, download datasets, etc...)

## Training

To train the student(s) using cached teachers in the paper, run this command:

```train
python train_student_moco.py \
    --teacher_model cached \ 
    --teacher <path_to_cached_features> \
    --student_model alexnet \
    --checkpoint_path <path_to_checkpoint_folder> \
    --data <path_to_imagenet_data>

```


To train the student(s) using pretrained teachers in the paper, run this command:

```train
python train_student_moco.py \
    --teacher_model resnet50 \ 
    --teacher <path_to_pretrained_model> \
    --student_model mobilenet \
    --checkpoint_path <path_to_checkpoint_folder> \
    --data <path_to_imagenet_data>
```


To train the student(s) without Moco framework execute train_student.py instead of train_student_moco.py

[comment]: <> (📋Describe how to train the models, with example commands on how to train the models in your paper, including the full training procedure and appropriate hyperparameters.)
## Evaluation

To evaluate NN models on ImageNet, run:

```eval
python eval_knn.py \
    -a alexnet \
    --weights <path_to_pretrained_model> \
    --save <path_to_save_folder> \
    <path_to_imagenet_data>
```


To evaluate Linear Classifier models on ImageNet, run:

```eval
python save_var_mean.py --x_root <NN_evaluation_save_folder>

python eval_multiple_linear.py \
    --arch alexnet \
    --weights <path_to_pretrained_model> \
    --mean_paths <NN_evaluation_save_folder>/var_mean.pth.tar \
    --save <path_to_save_folder> \
    <path_to_imagenet_data>
```

To evaluate cluster alignment models on ImageNet, run:

```eval
python eval_cluster_alignment.py  \
    --batch-size 256 \ 
    --weights <path_to_pretrained_model> \
    --model resnet18  \
    --save <path_to_save_folder> \
    <path_to_imagenet_data> \ 
    --visualization \ 
    --confusion_matrix
```




## Results

<p align="center">
  <img src="https://user-images.githubusercontent.com/62820830/85651404-e48b8880-b675-11ea-9432-754546efad1a.png" width="300">
</p>

Our model achieves the following performance :


| Model name         | Top 1 Linear Classifier Accuracy | Top 1 NN Accuracy | Pre-trained |
| ------------------ |----------------------------------| ----------------- | ----------------- |
| CompReSS(Resnet50) |               71.6%              |        63.4%        | [Pre-trained Resnet50](https://drive.google.com/file/d/15rzzSkcedEuCE7Cm8yLXopA5PqHUQscb/view?usp=sharing) |
| CompReSS(Mobilenet)|               63.0%              |        54.4%        | [Pre-trained Mobilenet](https://drive.google.com/file/d/1gNkO48iREh6M6uuLd8TGqaOm3ChWiAdc/view?usp=sharing) |
| CompReSS(Resnet18) |               61.7%              |        53.4%        | [Pre-trained Resnet18](https://drive.google.com/file/d/1C3uJ6MS2A0WCBeygxyBs4grP4ixptndE/view?usp=sharing) | 
| CompReSS(Alexnet)  |               57.6%              |        52.3%        | [Pre-trained Alexnet](https://drive.google.com/file/d/1wiEdfk6unXKtYRL1faIMoZMXnShaxBMU/view?usp=sharing) |



## License

This project is under the MIT license.


