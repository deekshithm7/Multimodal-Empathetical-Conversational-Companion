import torch
from torch.utils.data import Dataset

class DummyMultiModalDataset(Dataset):
    def __init__(self, n=200):
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        V = torch.randn(2048)
        A = torch.randn(768)
        T = torch.randn(768)
        y = torch.randint(0, 4, (1,)).item()
        return V, A, T, y
