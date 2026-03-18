import os
import warnings

import cv2
import torch
import pandas as pd
import numpy as np
from albumentations import (
    CoarseDropout,
    ColorJitter,
    Compose,
    GaussianBlur,
    GaussNoise,
    LongestMaxSize,
    MotionBlur,
    Normalize,
    PadIfNeeded,
    RandomBrightnessContrast,
    RandomGamma,
    RandomResizedCrop,
    Rotate
)

from albumentations.pytorch import ToTensorV2
warnings.filterwarnings('ignore')


# ============================================================
# ------------------- TRANSFORMS -----------------------------
# ============================================================
def get_strong_train_transforms(target_size):
    """
    Strong augmentations for learning.
    Creates significant variations for one-shot learning

    :param target_size: It is a tuple consisting of two numbers: width and height.
    """
    return Compose([
        # Random crop with zoom change (simulating zooming in/out)
        RandomResizedCrop(
            size=(target_size[0], target_size[1]),
            scale=(0.7, 1.0),
            p=0.5
        ),
        # Rotation up to 15 degrees
        Rotate(
            limit=15,
            border_mode=cv2.BORDER_REFLECT_101,
            p=0.2
        ),
        ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.2,
            hue=0.1,
            p=0.5
        ),
        GaussNoise(std_range=(0.1, 0.3), p=0.3),
        GaussianBlur(blur_limit=(3, 7), p=0.2),
        # Random Area Cutting (CoarseDropout - modern name)
        CoarseDropout(
            num_holes_range=(1, 1),          # one hole
            hole_height_range=(50, 50),      # hole height 50 pixels
            hole_width_range=(50, 50),       # hole width 50 pixels
            fill=0,                          # fill with black
            p=0.2
        ),
        LongestMaxSize(max_size=max(target_size)),
        PadIfNeeded(
            min_height=target_size[0],
            min_width=target_size[1],
            border_mode=cv2.BORDER_CONSTANT
        ),
        # Нормализация (ImageNet stats)
        Normalize(
            mean=(0.485, 0.456, 0.406),
            std=(0.229, 0.224, 0.225)
        ),
        ToTensorV2()
    ])

def get_train_transforms(
    target_size,
    normalization="imagenet"
):
    """
    Валидационные трансформы
    Без сильных искажений для честной оценки
    """
    if normalization == "imagenet":
        mean = (0.485, 0.456, 0.406)
        std = (0.229, 0.224, 0.225)
    else:
        # если z-score — Albumentations сделает per-channel
        mean = (0.0, 0.0, 0.0)
        std = (1.0, 1.0, 1.0)

    transforms = Compose([
        # A.Resize(target_size[0], target_size[1]), # type: ignore
        LongestMaxSize(max_size=max(target_size)),
        # Small rotation +-2 degrees
        Rotate(
            limit=2,
            border_mode=cv2.BORDER_REFLECT_101,  # REFLECT
            p=0.5
        ),
        PadIfNeeded(
            min_height=target_size[0],
            min_width=target_size[1],
            border_mode=cv2.BORDER_CONSTANT
        ),
        MotionBlur(blur_limit=3, p=0.1),
        # Gamma shift
        RandomGamma(
            gamma_limit=(90, 110),  # 0.8–1.2
            p=0.2
        ),
        # Brightness shift
        RandomBrightnessContrast(
            brightness_limit=0.05,
            contrast_limit=0.05,
            p=0.3
        ),
        GaussNoise(
            std_range=(0.03, 0.08),
            p=0.15
        ),
        Normalize(mean=mean, std=std),
        ToTensorV2()
    ])

    return transforms


def get_val_transforms(target_size):   
    """
    Here are the given values ​​of mean and standard deviation for ImageNet.\n
    mean = (0.485, 0.456, 0.406)\n
    std = (0.229, 0.224, 0.225)
    
    :param target_size: It is a tuple consisting of two numbers: width and height.
    """
    return Compose([
        LongestMaxSize(target_size[0]),
        PadIfNeeded(
            min_height=target_size[0],
            min_width=target_size[1],
            border_mode=cv2.BORDER_CONSTANT
        ),
        Normalize(
            mean=(0.485, 0.456, 0.406),
            std=(0.229, 0.224, 0.225)
        ),
        ToTensorV2()
    ])


def get_val_aug_transforms():
    """
    Light augmentations ONLY for positive pairs during validation.\n
    IMPORTANT: Without Resize and Normalize (they are used in get_val_transforms).
    To avoid double normalization!
    """
    return Compose([
        ColorJitter(
            brightness=0.2,
            contrast=0.2,
            p=0.5
        ),
        Rotate(limit=5, p=0.3),
        GaussNoise(
            std_range=(0.8, 0.99),
            p=0.2
        )
    ])


# ============================================================
# -------------------- DATASETS ------------------------------
# ============================================================
class SmiCLRDataset(torch.utils.data.Dataset):
    def __init__(self, csv_path, root_dir, transform):
        self.df = pd.read_csv(csv_path)
        self.root_dir = root_dir
        self.transform = transform

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.root_dir, row["path_to_img"])
        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"[ERROR] Image not found: {img_path}")
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        aug1 = self.transform(image=image)["image"]
        aug2 = self.transform(image=image)["image"]

        return aug1, aug2

    def __len__(self):
        return len(self.df)


class SmiMIMDataset(torch.utils.data.Dataset):
    def __init__(self, csv_path, root_dir, transform):
        self.df = pd.read_csv(csv_path)
        self.root_dir = root_dir
        self.transform = transform

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.root_dir, row["path_to_img"])
        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"[ERROR] Image not found: {img_path}")
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if self.transform:
            img = self.transform(image=image)["image"]
        return img # type: ignore

    def __len__(self):
        return len(self.df)


# ------------------------------------------------------------
#  Датасет (возвращает изображение, id, возраст, пол)
# ------------------------------------------------------------
class MultiTaskDataset(torch.utils.data.Dataset):
    def __init__(self, csv_path, root_dir, transform=None):
        self.df = pd.read_csv(csv_path)
        self.root_dir = root_dir
        self.transform = transform
        self.id2label = {id_: idx for idx, id_ in enumerate(sorted(self.df["id"].unique()))}
        self.num_classes = len(self.id2label)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.root_dir, row["path_to_img"])
        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"Image not found: {img_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if self.transform:
            image = self.transform(image=image)["image"]

        id_label = self.id2label[row["id"]]
        age = float(row["age"])
        sex = float(row["sex"])

        return (
            image,
            torch.tensor(id_label, dtype=torch.long),
            torch.tensor(age, dtype=torch.float32),
            torch.tensor(sex, dtype=torch.float32)
        )


class PairDataset(torch.utils.data.Dataset):
    """
    Dataset for image pairs.
    Supports on-the-fly generation of pairs for training
    """
    def __init__(
        self,
        csv_path: str,
        root_dir: str,
        transform=None, 
        val_aug_transform=None,
        is_train: bool=True,
        num_neg_per_pos: int=5
    ):
        self.df = pd.read_csv(csv_path)
        self.root_dir = root_dir
        self.transform = transform
        self.val_aug_transform = val_aug_transform
        self.is_train = is_train
        self.num_neg_per_pos = num_neg_per_pos
        
        self.paths = self.df['path_to_img'].values
        self.ids = self.df['id'].values
        self.unique_ids = np.unique(self.ids) # type: ignore
        self.id_to_indices = {id_: np.where(self.ids == id_)[0] for id_ in self.unique_ids}
        
        # Checking the quality of the dataset
        avg_images_per_id = len(self.df) / len(self.unique_ids)
        print(f":: Dataset: {csv_path.split('/')[-1]} | Avg images per ID: {avg_images_per_id:.2f}")
        
        if not is_train and avg_images_per_id < 1.5:
            warnings.warn(
                f"[WARN] Only {avg_images_per_id:.2f} images per ID in validation/test. "
                f"Positive pairs will use augmentations."
            )
        
        # For validation, we generate fixed pairs
        if not is_train:
            self.pairs = self._generate_fixed_pairs(
                num_neg_per_pos=num_neg_per_pos,
                random_state=42
            )

    def _generate_fixed_pairs(self, num_neg_per_pos: int=5, random_state=None):
        """Generating balanced pairs for validation/testing"""
        if random_state:
            np.random.seed(random_state)
        
        pairs = []
        for id_ in self.unique_ids:
            indices = self.id_to_indices[id_]
            
            # Positive pairs: all combinations of photos of one person
            if len(indices) > 1:
                # If several photos - we use different ones
                for i, idx1 in enumerate(indices):
                    for idx2 in indices[i+1:]:
                        pairs.append((idx1, idx2, 1))
            else:
                # One photo is a special marker for augmentations
                idx = indices[0]
                pairs.append((idx, idx, 1))
            
            # Negative pairs
            other_ids = self.unique_ids[self.unique_ids != id_]
            if len(other_ids) > 0:
                num_neg = min(num_neg_per_pos, len(other_ids))
                selected_other = np.random.choice(
                    other_ids,
                    size=num_neg,
                    replace=False
                )
                for oid in selected_other:
                    oidx = np.random.choice(self.id_to_indices[oid])
                    pairs.append((indices[0], oidx, 0))

        return pairs

    def __len__(self):
        if self.is_train:
            return 10000  # On-the-fly generation
        else:
            return len(self.pairs)

    def __getitem__(self, idx):
        if self.is_train:
            return self._get_train_pair()
        else:
            idx1, idx2, same = self.pairs[idx]
            return self._get_pair(idx1, idx2, same, is_val=True)

    def _get_train_pair(self):
        pos_id = np.random.choice(self.unique_ids)
        indices = self.id_to_indices[pos_id]
        idx1 = np.random.choice(indices)
        
        if np.random.rand() > 0.5:
            same = 1
            if len(indices) > 1:
                idx2 = np.random.choice([i for i in indices if i != idx1])
            else:
                idx2 = idx1
        else:
            same = 0
            neg_id = np.random.choice(self.unique_ids[self.unique_ids != pos_id])
            idx2 = np.random.choice(self.id_to_indices[neg_id])
        
        img1 = self._load_image(idx1)
        img2 = self._load_image(idx2)
        
        if self.transform:
            img1 = self.transform(image=img1)['image']
            img2 = self.transform(image=img2)['image']
        
        # Отладка (можно закомментировать после исправления)
        # print(f"img1 shape: {img1.shape}, img2 shape: {img2.shape}")
        assert img1.shape == img2.shape, f"Shape mismatch: {img1.shape} vs {img2.shape}"
        
        stacked = torch.cat([img1, img2], dim=0)  # (6, H, W) # type: ignore
        return stacked, torch.tensor(same, dtype=torch.long)

    def _get_pair(self, idx1, idx2, same, is_val=False):
        """
        Obtaining a pair with augmentations for validation
        CRITICAL FIX: Different augmentations for the same image
        """
        img1 = self._load_image(idx1)
        img2 = self._load_image(idx2)
        
        if is_val and idx1 == idx2 and same == 1:
            # Special case: one photo - we use DIFFERENT augmentations
            img1 = self.transform(image=img1)['image']  # Resize + Normalize # type: ignore
            img2_aug = self.val_aug_transform(image=img2)['image']  # Только jitter # type: ignore
            img2 = self.transform(image=img2_aug)['image']  # Затем Resize + Normalize # type: ignore
        else:
            img1 = self.transform(image=img1)['image'] # type: ignore
            img2 = self.transform(image=img2)['image'] # type: ignore
        
        stacked = torch.cat([img1, img2], dim=0)
        return stacked, torch.tensor(same, dtype=torch.long)

    def _load_image(self, idx):
        path = os.path.join(self.root_dir, self.paths[idx]) # type: ignore
        image = cv2.imread(path)
        if image is None:
            raise ValueError(f"Image not found: {path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image
