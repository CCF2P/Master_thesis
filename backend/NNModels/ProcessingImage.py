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
# -------------------- TRANSFORMS -----------------------------
# ============================================================
def get_val_transforms(target_size: tuple[int, int]) -> Compose:
    """
    Validation transforms matching training configuration.
    mean = (0.4576, 0.4576, 0.4576)
    std = (0.1942, 0.1942, 0.1942)
    """
    return Compose([
        LongestMaxSize(target_size[0]),
        PadIfNeeded(
            min_height=target_size[0],
            min_width=target_size[1],
            border_mode=cv2.BORDER_CONSTANT
        ),
        Normalize(
            mean=(0.4576, 0.4576, 0.4576),
            std=(0.1942, 0.1942, 0.1942)
        ),
        ToTensorV2()
    ])


def get_val_aug_transforms() -> Compose:
    """
    Light augmentations for positive pairs during validation.
    Without Resize and Normalize to avoid double normalization.
    """
    return Compose([
        ColorJitter(
            brightness=0.1,
            contrast=0.1,
            p=0.5
        ),
        Rotate(limit=5, p=0.3),
        GaussNoise(
            std_range=(0.1, 0.3),
            p=0.2
        )
    ])
