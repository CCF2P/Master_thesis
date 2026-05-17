import numpy as np
import torch
import cv2

from NNModels.NeuralNetworkModel import SiameseMetricModel
from NNModels.ProcessingImage import get_val_transforms


class FeatureExtractor:
    """
    Singleton wrapper for extracting L2-normalized embeddings from images.
    Uses the loaded SiameseMetricModel and validation transforms.
    """
    _instance = None
    _model: SiameseMetricModel | None = None
    _device: torch.device | None = None
    _transform = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(
        self,
        model: SiameseMetricModel,
        device: torch.device,
        target_size: tuple[int, int] = (224, 224)
    ):
        self._model = model
        self._device = device
        self._transform = get_val_transforms(target_size)

    def extract_from_bytes(self, img_bytes: bytes) -> np.ndarray:
        """
        Extract 512-dim L2-normalized embedding from image bytes.
        Returns numpy array ready for FAISS.
        """
        if len(img_bytes) == 0:
            raise ValueError("Empty image bytes")

        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data")

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return self._extract_from_image(img)

    def extract_from_path(self, path: str) -> np.ndarray:
        """
        Extract 512-dim L2-normalized embedding from image file path.
        Returns numpy array ready for FAISS.
        """
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Cannot read image: {path}")

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return self._extract_from_image(img)

    def _extract_from_image(self, img: np.ndarray) -> np.ndarray:
        augmented = self._transform(image=img)["image"]
        tensor = augmented.unsqueeze(0).to(self._device)

        with torch.no_grad():
            embedding = self._model.forward_one(tensor)

        return embedding.cpu().numpy().flatten()
