import torch
import torch.nn as nn

class FusionMLP(nn.Module):
    def __init__(self, use_v, use_a, use_t, num_classes):
        super().__init__()

        input_dim = (
            (2048 if use_v else 0) +
            (768  if use_a else 0) +
            (768  if use_t else 0)
        )
        print("input_dim=", input_dim)
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, 1024),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(1024, 512),
            nn.GELU(),
            nn.Dropout(0.1)
        )

        self.classifier = nn.Linear(512, num_classes)

    def forward(self, fused):
        h = self.mlp(fused)
        logits = self.classifier(h)
        return logits
