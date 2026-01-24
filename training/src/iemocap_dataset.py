import torch
from torch.utils.data import Dataset
import json
from pathlib import Path

class IEMOCAPDataset(Dataset):
    """
    IEMOCAP Dataset loader for cached features
    
    Loads pre-extracted features from .pt files based on index JSON
    """
    def __init__(self, index_file, use_vision=True):
        """
        Args:
            index_file: Path to train_index.json or test_index.json
            use_vision: Whether to load vision features (set to False if not cached)
        """
        with open(index_file, 'r') as f:
            self.data = json.load(f)
        
        self.use_vision = use_vision
        
        # Don't filter - use zeros for missing vision (dialog-level issue)
        # if use_vision:
        #     self.data = [item for item in self.data if item['vision'] is not None]
        
        print(f"Loaded {len(self.data)} samples from {index_file}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Load text features
        text = torch.load(item['text'])  # (768,)
        
        # Load audio features
        audio = torch.load(item['audio'])  # (768,)
        
        # Load vision features or create zeros
        if self.use_vision and item['vision'] is not None:
            vision = torch.load(item['vision'])  # (2048,)
        else:
            vision = torch.zeros(2048)  # Placeholder if vision not available
        
        # L2 NORMALIZATION - Fix scale mismatch (vision is 4.9x larger than audio)
        vision = torch.nn.functional.normalize(vision, p=2, dim=0)
        audio = torch.nn.functional.normalize(audio, p=2, dim=0)
        text = torch.nn.functional.normalize(text, p=2, dim=0)
        
        # Get label
        label = item['label']
        
        return vision, audio, text, label


if __name__ == '__main__':
    # Test the dataset loader
    import sys
    
    dataset = IEMOCAPDataset(
        index_file=r'd:\Multimodal-Empathetical-Conversational-Companion\training\train_index.json',
        use_vision=False  # Set to True after video caching is complete
    )
    
    print(f"\nDataset size: {len(dataset)}")
    
    # Test loading one sample
    V, A, T, y = dataset[0]
    print(f"\nSample shapes:")
    print(f"  Vision: {V.shape}")
    print(f"  Audio: {A.shape}")
    print(f"  Text: {T.shape}")
    print(f"  Label: {y}")
    
    # Test with DataLoader
    from torch.utils.data import DataLoader
    loader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    batch = next(iter(loader))
    V_batch, A_batch, T_batch, y_batch = batch
    print(f"\nBatch shapes:")
    print(f"  Vision: {V_batch.shape}")
    print(f"  Audio: {A_batch.shape}")
    print(f"  Text: {T_batch.shape}")
    print(f"  Labels: {y_batch.shape}")
    print(f"\n✓ Dataset loader working correctly!")
