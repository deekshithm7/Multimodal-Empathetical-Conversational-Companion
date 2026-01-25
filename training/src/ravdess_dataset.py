"""
RAVDESS Dataset Loader

Compatible with existing train.py script.
"""

import torch
from torch.utils.data import Dataset
import json
from pathlib import Path

class RAVDESSDataset(Dataset):
    def __init__(self, index_file, use_vision=True):
        """
        Args:
            index_file: Path to ravdess_train_index.json or ravdess_test_index.json
            use_vision: Whether to load vision features
        """
        with open(index_file, 'r') as f:
            self.data = json.load(f)
        
        self.use_vision = use_vision
        
        print(f"Loaded {len(self.data)} samples from {index_file}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Load text features
        text = torch.load(item['text'])  # (768,)
        
        # Load audio features
        audio = torch.load(item['audio'])  # (768,)
        
        # Load vision features
        if self.use_vision:
            vision = torch.load(item['vision'])  # (2048,)
        else:
            vision = torch.zeros(2048)
        
        # L2 normalization
        vision = torch.nn.functional.normalize(vision, p=2, dim=0)
        audio = torch.nn.functional.normalize(audio, p=2, dim=0)
        text = torch.nn.functional.normalize(text, p=2, dim=0)
        
        # Get label
        label = item['label']
        
        return vision, audio, text, label
