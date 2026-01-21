from sklearn.metrics import f1_score
import numpy as np

def compute_metrics(preds, labels):
    preds = np.array(preds)
    labels = np.array(labels)

    f1 = f1_score(labels, preds, average="weighted")
    acc = (preds == labels).mean()
    return {
        "f1_weighted": f1,
        "accuracy": acc
    }
