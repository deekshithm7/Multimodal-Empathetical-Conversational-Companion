import torch

def fuse(V, A, T, use_v=True, use_a=True, use_t=True):
    parts = []
    if use_v: parts.append(V)
    if use_a: parts.append(A)
    if use_t: parts.append(T)
    return torch.cat(parts, dim=1)
