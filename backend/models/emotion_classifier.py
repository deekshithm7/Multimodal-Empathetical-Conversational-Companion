import torch
import torch.nn as nn

class FusionMLP(nn.Module):
    """
    Simple MLP fusion model for emotion recognition.
    This is the ACTUAL architecture used for training the at.pth checkpoint.
    """
    def __init__(self, use_v, use_a, use_t, num_classes):
        super().__init__()

        input_dim = (
            (2048 if use_v else 0) +
            (768  if use_a else 0) +
            (768  if use_t else 0)
        )
        print("input_dim=", input_dim)
        
        # Architecture matching at.pth checkpoint
        # For A+T: 1536 → 1024 → 512 → 4
        hidden_dim1 = 1024
        hidden_dim2 = 512
        dropout_rate = 0.3
        
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim1),      # mlp.0: 1536 → 1024
            nn.GELU(),                              # mlp.1
            nn.Dropout(dropout_rate),               # mlp.2
            nn.Linear(hidden_dim1, hidden_dim2),    # mlp.3: 1024 → 512
            nn.GELU(),                              # mlp.4
            nn.Dropout(dropout_rate)                # mlp.5
        )

        self.classifier = nn.Linear(hidden_dim2, num_classes)  # 512 → 4

    def forward(self, fused):
        h = self.mlp(fused)
        logits = self.classifier(h)
        return logits
