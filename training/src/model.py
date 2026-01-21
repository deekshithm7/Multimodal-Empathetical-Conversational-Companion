import torch
import torch.nn as nn

class FusionMLP(nn.Module):
    def __init__(self, input_dim=3584, hidden_dim=1024, rep_dim=512, num_classes=4):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, rep_dim),
            nn.GELU(),
            nn.Dropout(0.1)
        )
        self.classifier = nn.Linear(rep_dim, num_classes)

    def forward(self, fused):
        h = self.mlp(fused)
        logits = self.classifier(h)
        return logits
