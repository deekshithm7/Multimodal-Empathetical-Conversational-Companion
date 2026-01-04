import torch
import numpy as np
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights

# Load model ONCE
_resnet = models.resnet50(weights=ResNet50_Weights.DEFAULT)
_resnet.fc = torch.nn.Identity()
_resnet.eval()

_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def encode_visual(frames):
    """
    Input: list of frames (H, W, C)
    Output: visual feature vector
    """
    embeddings = []

    with torch.no_grad():
        for frame in frames:
            x = _transform(frame).unsqueeze(0)
            emb = _resnet(x)
            embeddings.append(emb)

    if not embeddings:
        return np.zeros(2048).tolist()

    features = torch.mean(torch.stack(embeddings), dim=0)
    return features.squeeze().numpy().tolist()
