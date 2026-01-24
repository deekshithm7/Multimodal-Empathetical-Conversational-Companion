import torch
import argparse
import json
from torch.utils.data import DataLoader

from iemocap_dataset import IEMOCAPDataset
from fusion import fuse
from model import FusionMLP
from eval import compute_metrics

def train():

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="Path to config JSON")
    parser.add_argument("--train_index", type=str, default="../train_index.json", help="Path to train_index.json")
    parser.add_argument("--test_index", type=str, default="../test_index.json", help="Path to test_index.json")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    # Use IEMOCAP dataset
    use_vision = config.get("use_v", True)
    train_ds = IEMOCAPDataset(args.train_index, use_vision=use_vision)
    val_ds = IEMOCAPDataset(args.test_index, use_vision=use_vision)

    train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
    val_loader   = DataLoader(val_ds, batch_size=config["batch_size"], shuffle=False)

    model = FusionMLP(
        use_v=config["use_v"],
        use_a=config["use_a"],
        use_t=config["use_t"],
        num_classes=config["num_classes"]
    )

    # Add weight decay for regularization
    weight_decay = config.get("weight_decay", 0.01)
    optim = torch.optim.AdamW(model.parameters(), lr=config["lr"], weight_decay=weight_decay)
    loss_fn = torch.nn.CrossEntropyLoss()
    
    # Learning rate scheduler - decay by 0.5 every 5 epochs
    scheduler = torch.optim.lr_scheduler.StepLR(optim, step_size=5, gamma=0.5)
    
    # Early stopping setup
    best_f1 = 0.0
    patience = 3
    patience_counter = 0
    best_model_state = None

    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0

        for V,A,T,y in train_loader:
            # batchify if needed
            if V.ndim == 1: V = V.unsqueeze(0)
            if A.ndim == 1: A = A.unsqueeze(0)
            if T.ndim == 1: T = T.unsqueeze(0)

            fused = fuse(
                V,A,T,
                use_v=config["use_v"],
                use_a=config["use_a"],
                use_t=config["use_t"]
            )

            logits = model(fused)
            loss = loss_fn(logits, y)

            optim.zero_grad()
            loss.backward()
            optim.step()
            total_loss += loss.item()

        print(f"[epoch {epoch}] train_loss={total_loss/len(train_loader):.3f}")

        # -------- eval --------
        model.eval()
        preds = []
        labels = []

        with torch.no_grad():
            for V,A,T,y in val_loader:
                if V.ndim == 1: V = V.unsqueeze(0)
                if A.ndim == 1: A = A.unsqueeze(0)
                if T.ndim == 1: T = T.unsqueeze(0)

                fused = fuse(
                    V,A,T,
                    use_v=config["use_v"],
                    use_a=config["use_a"],
                    use_t=config["use_t"]
                )
                logits = model(fused)
                p = torch.argmax(logits, dim=1)
                preds.extend(p.tolist())
                labels.extend(y.tolist())

        metrics = compute_metrics(preds, labels)
        print(f"[epoch {epoch}] acc={metrics['accuracy']:.3f}, f1={metrics['f1_weighted']:.3f}, lr={scheduler.get_last_lr()[0]:.6f}")
        
        # Early stopping check
        if metrics['f1_weighted'] > best_f1:
            best_f1 = metrics['f1_weighted']
            best_model_state = model.state_dict().copy()
            patience_counter = 0
            print(f"  → New best F1: {best_f1:.3f}")
        else:
            patience_counter += 1
            print(f"  → No improvement ({patience_counter}/{patience})")
            
        if patience_counter >= patience:
            print(f"\nEarly stopping triggered at epoch {epoch}")
            break
            
        # Step the learning rate scheduler
        scheduler.step()

    # -------- checkpoint --------
    # Save best model (from early stopping)
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print(f"\nRestored best model with F1={best_f1:.3f}")
    
    ckpt_path = f"../checkpoints/{args.config.split('/')[-1].replace('.json','.pth')}"
    torch.save({"model": model.state_dict(), "config": config, "best_f1": best_f1}, ckpt_path)
    print("saved:", ckpt_path)


if __name__ == "__main__":
    train()
