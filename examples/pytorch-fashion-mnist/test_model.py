"""Local test of the model logic. Random tensors, no download, runs in milliseconds.

Run it before the job ever touches the cluster:

    python test_model.py
"""

import torch

from model import CLASSES, accuracy, build_model, train


def test_build_model_shapes():
    model = build_model(hidden=32)
    output = model(torch.zeros(4, 1, 28, 28))
    assert output.shape == (4, CLASSES)


def test_model_learns_a_separable_pattern():
    # Two classes that are trivially separable: all-black images are class 0,
    # all-white images are class 1. A working training loop must reach high accuracy.
    half = 128
    images = torch.cat([torch.zeros(half, 1, 28, 28), torch.ones(half, 1, 28, 28)])
    labels = torch.cat([torch.zeros(half), torch.ones(half)]).long()

    model = build_model(hidden=16)
    before = accuracy(model, images, labels)
    train(model, images, labels, lr=0.1, epochs=5, seed=0)
    after = accuracy(model, images, labels)

    assert after > before
    assert after > 0.9


if __name__ == "__main__":
    test_build_model_shapes()
    test_model_learns_a_separable_pattern()
    print("ok")
