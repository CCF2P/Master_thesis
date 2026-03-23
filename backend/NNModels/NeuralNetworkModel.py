import logging
import cv2
import timm
import torch
import torch.nn.functional as F
import numpy as np

from torch import nn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# Model definition 
# ============================================================
class StackedChannelsModel(nn.Module):
    def __init__(self, backbone_name, num_classes=2):
        super().__init__()

        self.backbone = timm.create_model(
            backbone_name,
            pretrained=False,
            num_classes=0,
            global_pool=""
        )

        self._adapt_first_layer(in_channels=6)

        with torch.no_grad():
            dummy = torch.randn(1, 6, 224, 224)
            feat = self.backbone(dummy)
            in_features = feat.shape[1]

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(in_features, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(256, num_classes)
        )

    def _adapt_first_layer(self, in_channels):
        def replace_conv(module):
            for name, child in module.named_children():
                if isinstance(child, nn.Conv2d):
                    new_conv = nn.Conv2d(
                        in_channels,
                        child.out_channels,
                        kernel_size=child.kernel_size, #type: ignore
                        stride=child.stride,           #type: ignore
                        padding=child.padding,         #type: ignore
                        bias=child.bias is not None
                    )
                    with torch.no_grad():
                        new_conv.weight[:, :3] = child.weight
                        mean_w = child.weight.mean(dim=1, keepdim=True)
                        new_conv.weight[:, 3:] = mean_w.repeat(1, 3, 1, 1)
                        if child.bias is not None:
                            new_conv.bias.copy_(child.bias) #type: ignore
                    setattr(module, name, new_conv)
                    return True
                if replace_conv(child):
                    return True
            return False

        if not replace_conv(self.backbone):
            raise RuntimeError("Conv2d layer not found for adaptation")

    def forward(self, x):
        x = self.backbone(x)
        return self.classifier(x)


# ============================================================
# Load model
# ============================================================
class ModelLoader:
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
        backbone_name: str,
        device: str="cuda"
    ):
        """
        Loads model and moves it to the specified device
        """
        if self._model is not None:
            logger.info("Model already loaded, skipping")
            return self._model

        self._device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        logger.info(f"Loading model from {checkpoint_path} on {self._device}...")

        model = StackedChannelsModel(backbone_name=backbone_name)
        state_dict = torch.load(checkpoint_path, map_location=self._device)
        model.load_state_dict(state_dict)
        model.to(self._device)
        model.eval()
        self._model = model
        logger.info("Model loaded successfully")
        return self._model

    def get_model(self):
        if self._model is None:
            raise RuntimeError("Model is not loaded. Call load() first")
        return self._model

    def get_device(self):
        return self._device


# ============================================================
# Inference for a single pair
# ============================================================
def predict_pair(
    model,
    path1,
    path2,
    base_tf,
    device
):
    img1 = cv2.cvtColor(cv2.imread(path1), cv2.COLOR_BGR2RGB) #type: ignore
    img2 = cv2.cvtColor(cv2.imread(path2), cv2.COLOR_BGR2RGB) #type: ignore

    img1 = base_tf(image=img1)["image"]
    img2 = base_tf(image=img2)["image"]

    stacked = torch.cat([img1, img2], dim=0).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(stacked)
        prob_same = F.softmax(logits, dim=1)[0, 1].item()

    return prob_same


async def get_image_bytes_by_path(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


async def predict_pair_async(
    model,
    img_bytes1: bytes,
    img_bytes2: bytes,
    base_tf,
    device
):
    """
    Asynchronous version for working with image bytes
    """
    if len(img_bytes1) == 0:
        raise ValueError("Empty bytes for first image")
    if len(img_bytes2) == 0:
        raise ValueError("Empty bytes for second image")

    img1 = cv2.imdecode(np.frombuffer(img_bytes1, np.uint8), cv2.IMREAD_COLOR)
    img2 = cv2.imdecode(np.frombuffer(img_bytes2, np.uint8), cv2.IMREAD_COLOR)
    if img1 is None or img2 is None:
        raise ValueError("Invalid image data/bytes")

    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    img1_t = base_tf(image=img1)["image"]
    img2_t = base_tf(image=img2)["image"]

    stacked = torch.cat([img1_t, img2_t], dim=0).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(stacked)
        prob_same = F.softmax(logits, dim=1)[0, 1].item()

    return prob_same

