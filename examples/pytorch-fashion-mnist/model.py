"""Pure PyTorch logic for the Fashion-MNIST classifier. No Argo, no cluster.

These functions are the tested source of truth (see ``test_model.py``). The workflow
steps in ``workflow.yaml`` and ``workflow.py`` mirror this logic so the same maths runs
on the cluster. This is the same split the ``hera-notebook-forecast`` example uses:
plain, tested Python here, and the cluster step inlines an equivalent.
"""

import torch
from torch import nn

CLASSES = 10
PIXELS = 28 * 28


def build_model(hidden):
    """A small multi-layer perceptron: 784 inputs, one hidden layer, 10 outputs.

    Big enough to learn Fashion-MNIST on a CPU, small enough to train in seconds.
    """
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(PIXELS, hidden),
        nn.ReLU(),
        nn.Linear(hidden, CLASSES),
    )


def train(model, images, labels, lr, epochs=1, batch_size=128, seed=0):
    """Train the model in place with plain SGD and return it.

    ``images`` is a float tensor shaped [N, 1, 28, 28] scaled to 0-1. ``labels`` is a
    long tensor shaped [N]. The seed fixes the batch order so a given config is
    reproducible.
    """
    torch.manual_seed(seed)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    sample_count = images.shape[0]
    model.train()
    for _ in range(epochs):
        order = torch.randperm(sample_count)
        for start in range(0, sample_count, batch_size):
            batch = order[start : start + batch_size]
            optimizer.zero_grad()
            loss = loss_fn(model(images[batch]), labels[batch])
            loss.backward()
            optimizer.step()
    return model


def accuracy(model, images, labels):
    """Return the fraction of correct predictions on the given set."""
    model.eval()
    with torch.no_grad():
        predictions = model(images).argmax(dim=1)
        return float((predictions == labels).float().mean())
