import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

from typing import Tuple


# ============================================================
# -------------------- POOLING LAYERS -------------------------
# ============================================================
class GeM(nn.Module):
    """Generalized Mean Pooling - лучше захватывает локальные текстуры"""
    def __init__(self, p=3.0, eps=1e-6, trainable=True):
        super().__init__()
        if trainable:
            self.p = nn.Parameter(torch.ones(1) * p)
        else:
            self.p = p
        self.eps = eps

    def forward(self, x):
        return x.clamp(min=self.eps).pow(self.p).mean(dim=(2, 3)).pow(1./self.p)


class AttentionPooling(nn.Module):
    """Attention-weighted pooling для фокуса на важных областях"""
    def __init__(self, in_features, reduction=16):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Conv2d(in_features, in_features // reduction, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_features // reduction, 1, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        weights = self.attention(x)
        return (x * weights).sum(dim=(2, 3)) / weights.sum(dim=(2, 3))


# ============================================================
# -------------------- SIAMESE MODEL --------------------------
# ============================================================
class SiameseMetricModel(nn.Module):
    """
    Siamese model with GeM + Attention pooling and embedding head.
    Produces L2-normalized 512-dim embeddings for single images.
    """
    def __init__(
        self,
        backbone_name: str = "convnext_tiny",
        embedding_dim: int = 512,
        gem_p: float = 3.0,
        use_multitask: bool = False,
        backbone_path: str | None = None
    ):
        super().__init__()
        self.use_multitask = use_multitask

        self.backbone = timm.create_model(
            backbone_name,
            pretrained=False,
            num_classes=0,
            global_pool=""
        )

        if backbone_path and os.path.exists(backbone_path):
            print(f"[INFO ] Loading backbone from {backbone_path}")
            state_dict = torch.load(backbone_path, map_location="cpu")

            if isinstance(state_dict, dict):
                if "state_dict" in state_dict:
                    state_dict = state_dict["state_dict"]
                elif "model" in state_dict:
                    state_dict = state_dict["model"]

            state_dict = {k.replace("backbone.", ""): v for k, v in state_dict.items()}
            state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

            self.backbone.load_state_dict(state_dict, strict=False)
        else:
            if backbone_path:
                print(f"[WARN] Backbone not found: {backbone_path}. Using ImageNet weights.")
            self.backbone = timm.create_model(
                backbone_name,
                pretrained=True,
                num_classes=0,
                global_pool=""
            )

        with torch.no_grad():
            dummy = torch.randn(1, 3, 224, 224)
            feat = self.backbone(dummy)
            in_features = feat.shape[1]

        self.gem = GeM(p=gem_p, trainable=True)
        self.attention_pool = AttentionPooling(in_features, reduction=16)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        total_features = in_features * 4

        self.embedding_head = nn.Sequential(
            nn.Linear(total_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, embedding_dim)
        )

        if use_multitask:
            self.age_head = nn.Sequential(
                nn.Linear(embedding_dim, 64),
                nn.ReLU(inplace=True),
                nn.Linear(64, 1),
                nn.Sigmoid()
            )

        self.classifier_head = nn.Sequential(
            nn.Linear(embedding_dim * 3, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 1)
        )

    def forward_one(self, x: torch.Tensor) -> torch.Tensor:
        """Extract L2-normalized embedding for a single image."""
        features = self.backbone(x)

        gem_out = self.gem(features)
        attn_out = self.attention_pool(features)
        avg_out = self.avg_pool(features).flatten(1)
        max_out = self.max_pool(features).flatten(1)

        multi_scale_features = torch.cat([gem_out, attn_out, avg_out, max_out], dim=1)

        vec = self.embedding_head(multi_scale_features)
        vec = F.normalize(vec, dim=1)

        return vec

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        emb1 = self.forward_one(x1)
        emb2 = self.forward_one(x2)
        return emb1, emb2

    def predict_age(self, embedding: torch.Tensor) -> torch.Tensor | None:
        if self.use_multitask:
            return self.age_head(embedding)
        return None

    def classify_pair(self, emb1: torch.Tensor, emb2: torch.Tensor) -> torch.Tensor:
        diff = torch.abs(emb1 - emb2)
        features = torch.cat([emb1, emb2, diff], dim=1)
        logits = self.classifier_head(features)
        return logits.squeeze(-1)


# ============================================================
# -------------------- MODEL LOADER ---------------------------
# ============================================================
class ModelLoader:
    """Singleton loader for SiameseMetricModel."""
    _instance = None
    _model = None
    _device = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(
        self,
        checkpoint_path: str,
        backbone_name: str = "convnext_tiny",
        embedding_dim: int = 512,
        backbone_path: str | None = None,
        device: str = "cuda"
    ):
        if self._model is not None:
            print("[INFO ] Model already loaded, skipping...")
            return self._model

        self._device = torch.device(
            device if torch.cuda.is_available() and device == "cuda" else "cpu"
        )
        print(f"[INFO ] Loading model from {checkpoint_path} on {self._device}...")

        model = SiameseMetricModel(
            backbone_name=backbone_name,
            embedding_dim=embedding_dim,
            backbone_path=backbone_path
        )

        state_dict = torch.load(checkpoint_path, map_location=self._device)

        if "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]

        model.load_state_dict(state_dict, strict=False)
        model.to(self._device)
        model.eval()
        self._model = model
        print("[INFO ] Model loaded successfully")
        return self._model

    def get_model(self):
        if self._model is None:
            raise RuntimeError("Model is not loaded. Call load() first")
        return self._model

    def get_device(self):
        if self._device is None:
            raise RuntimeError("Model is not loaded. Call load() first")
        return self._device


# ============================================================
# -------------------- INFERENCE HELPERS ----------------------
# ============================================================
async def get_image_bytes_by_path(path: str) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        print("[ERROR] File not found")
        return None
    except PermissionError:
        print("[ERROR] File access denied")
        return None
    except IOError as e:
        print(f"[ERROR] Error opening file: {e}")
        return None


async def extract_embedding_async(
    model: SiameseMetricModel,
    img_bytes: bytes,
    transform,
    device: torch.device
) -> np.ndarray | None:
    """
    Extract L2-normalized embedding (512-dim) from image bytes.
    Returns numpy array ready for FAISS indexing/search.
    """
    if len(img_bytes) == 0:
        raise ValueError("Empty image bytes")

    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data/bytes")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    augmented = transform(image=img)["image"]
    tensor = augmented.unsqueeze(0).to(device)

    with torch.no_grad():
        embedding = model.forward_one(tensor)

    return embedding.cpu().numpy().flatten()
