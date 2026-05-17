import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch

from ForNNTrain.preprocessing_image import get_train_transforms

# ===== ПАРАМЕТРЫ =====
IMG_PATH = "E:\\Diploma_ISU\\Datasets\\OPTG1\\test\\1(27).jpg"   # путь к картинке
TARGET_SIZE = (224, 224)

# ===== ЗАГРУЗКА ИЗОБРАЖЕНИЯ =====
image = cv2.imread(IMG_PATH)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# ===== ТРАНСФОРМЫ =====
transform = get_train_transforms(TARGET_SIZE)

# ===== ПРИМЕНЕНИЕ =====
augmented = transform(image=image)["image"]  # tensor (C, H, W)

# ===== ОБРАТНАЯ НОРМАЛИЗАЦИЯ =====
def denormalize(tensor):
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])

    img = tensor.permute(1, 2, 0).cpu().numpy()
    img = (img * std) + mean
    img = np.clip(img, 0, 1)
    return img

# ===== ВИЗУАЛИЗАЦИЯ =====
plt.figure(figsize=(10, 5))

# оригинал
plt.subplot(1, 2, 1)
plt.title("Original")
plt.imshow(image)
plt.axis("off")

# после трансформов
plt.subplot(1, 2, 2)
plt.title("After get_train_transforms")
plt.imshow(denormalize(augmented))
plt.axis("off")

plt.show()

