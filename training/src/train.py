import torch
from torch.utils.data import DataLoader
from dataset import DummyMultiModalDataset
from fusion import fuse
from model import FusionMLP

def train_phase1():

    # Config (you'll later make this argparse or json)
    config = {
        "batch_size": 16,
        "epochs": 2,
        "lr": 1e-3,
        "use_v": False,
        "use_a": False,
        "use_t": True,
        "num_classes": 4
    }

    # Dummy dataset + loader
    train_ds = DummyMultiModalDataset(n=200)
    val_ds   = DummyMultiModalDataset(n=50)

    train_loader = DataLoader(train_ds, batch_size=config["batch_size"], shuffle=True)
    val_loader   = DataLoader(val_ds, batch_size=config["batch_size"], shuffle=False)

    # Model + loss + optim
    model = FusionMLP(
        input_dim=(
            (2048 if config["use_v"] else 0) +
            (768  if config["use_a"] else 0) +
            (768  if config["use_t"] else 0)
        ),
        num_classes=config["num_classes"]
    )

    optim = torch.optim.AdamW(model.parameters(), lr=config["lr"])
    loss_fn = torch.nn.CrossEntropyLoss()

    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0

        for V, A, T, y in train_loader:
            fused = fuse(
                V.unsqueeze(0) if V.ndim==1 else V,
                A.unsqueeze(0) if A.ndim==1 else A,
                T.unsqueeze(0) if T.ndim==1 else T,
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

        print(f"epoch {epoch} train_loss={total_loss/len(train_loader):.4f}")

        # --- eval ---
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for V, A, T, y in val_loader:
                fused = fuse(
                    V if V.ndim>1 else V.unsqueeze(0),
                    A if A.ndim>1 else A.unsqueeze(0),
                    T if T.ndim>1 else T.unsqueeze(0),
                    use_v=config["use_v"],
                    use_a=config["use_a"],
                    use_t=config["use_t"]
                )
                logits = model(fused)
                preds = torch.argmax(logits, dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        acc = correct / total if total > 0 else 0.0
        print(f"epoch {epoch} val_acc={acc:.3f}")

    # --- checkpoint ---
    torch.save(model.state_dict(), "dummy_checkpoint.pth")
    print("checkpoint saved")

if __name__ == "__main__":
    train_phase1()
