import torch
import argparse
import json
from torch.utils.data import DataLoader

from dataset import DummyMultiModalDataset
from fusion import fuse
from model import FusionMLP
from eval import compute_metrics

def train():

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    train_ds = DummyMultiModalDataset(n=200)
    val_ds   = DummyMultiModalDataset(n=50)

    train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
    val_loader   = DataLoader(val_ds, batch_size=config["batch_size"], shuffle=False)

    model = FusionMLP(
        use_v=config["use_v"],
        use_a=config["use_a"],
        use_t=config["use_t"],
        num_classes=config["num_classes"]
    )

    optim = torch.optim.AdamW(model.parameters(), lr=config["lr"])
    loss_fn = torch.nn.CrossEntropyLoss()

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
        print(f"[epoch {epoch}] acc={metrics['accuracy']:.3f}, f1={metrics['f1_weighted']:.3f}")

    # -------- checkpoint --------
    ckpt_path = f"../checkpoints/{args.config.split('/')[-1].replace('.json','.pth')}"
    torch.save({"model": model.state_dict(), "config": config}, ckpt_path)
    print("saved:", ckpt_path)


if __name__ == "__main__":
    train()
