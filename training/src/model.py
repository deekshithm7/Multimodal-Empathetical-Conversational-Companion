import torch
import torch.nn as nn

class FusionMLP(nn.Module):
    def __init__(self, use_v, use_a, use_t, num_classes):
        super().__init__()

        # Use full ResNet50 features (2048-dim) for better quality
        vision_dim = 2048 if use_v else 0
        
        input_dim = (
            (vision_dim if use_v else 0) +
            (768  if use_a else 0) +
            (768  if use_t else 0)
        )
        print("input_dim=", input_dim)
        
        # Larger capacity for trimodal
        hidden_dim1 = 2048 if input_dim > 1500 else 1024
        hidden_dim2 = 1024 if input_dim > 1500 else 512
        
        # HIGHER dropout for trimodal (0.5 instead of 0.1) - critical fix!
        dropout_rate = 0.5 if input_dim > 1500 else 0.3
        
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim1),
            nn.BatchNorm1d(hidden_dim1),  # Add batch norm
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim1, hidden_dim2),
            nn.BatchNorm1d(hidden_dim2),  # Add batch norm
            nn.GELU(),
            nn.Dropout(dropout_rate)
        )

        self.classifier = nn.Linear(hidden_dim2, num_classes)

    def forward(self, fused):
        h = self.mlp(fused)
        logits = self.classifier(h)
        return logits
