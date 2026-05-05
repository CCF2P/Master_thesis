import cv2
import torch

from albumentations.pytorch import ToTensorV2
from albumentations import (
    ColorJitter,
    Compose,
    GaussNoise,
    LongestMaxSize,
    Normalize,
    PadIfNeeded,
    Rotate
)


# ============================================================
# ------------------- TRANSFORMS -----------------------------
# ============================================================
def get_val_transforms(target_size) -> Compose:
    """
    Here are the given values of mean and standard deviation for ImageNet.\n
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


def get_val_aug_transforms() -> Compose:
    """
    Light augmentations ONLY for positive pairs during validation.\n
    IMPORTANT: Without Resize and Normalize
    (they are used in get_val_transforms).
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

