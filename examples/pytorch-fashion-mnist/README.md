[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# PyTorch Fashion-MNIST training pipeline

A small machine-learning pipeline that trains an image classifier on Argo Workflows and picks the best model. It runs inside the Pipekit free trial cluster.

The pipeline has four stages as one DAG:

```text
prep  ->  train (x3, in parallel)  ->  register
```

- `prep` downloads the Fashion-MNIST dataset once and saves it as an artifact.
- `train` fans out over three hyperparameter configs. Each pod trains a small PyTorch model on the CPU and writes its model and metrics as a candidate artifact.
- `register` reads every candidate, picks the most accurate, and writes the winning model and a model card to the artifact store.

This is the standard "data prep, train, evaluate, register" shape, scaled down to fit the free trial cluster's resource limits. The training logic is generic, so you can swap in your own model and dataset.

## Files

- `workflow.py`: the pipeline authored with the Argo Workflows Python SDK. Data and ML teams usually author in Python, so this is the primary path.
- `workflow.yaml`: the same DAG as a plain manifest, for the GitOps path or the CLI.
- `model.py`: the model and training logic as plain PyTorch functions, the tested source of truth. The cluster steps mirror this logic.
- `test_model.py`: a local test of that logic. Runs in milliseconds, no cluster.

## PyTorch on the free trial cluster

PyTorch is installed at run time from `download.pytorch.org` (the CPU-only wheel), so the only Docker Hub image is `python:3.11-slim`. The free trial cluster shares one egress IP, and pulling large images from Docker Hub there can hit the anonymous rate limit. Fetching the wheel from pytorch.org avoids that.

The `torch_index` workflow parameter sets the pip index. Point it at an internal mirror to run offline or on a locked-down cluster.

## Log into Pipekit via the CLI

With the [CLI installed](https://docs.pipekit.io/reference/cli), log in once:

```bash
pipekit login
```

## Run it with the Python SDK

From the repo root:

```bash
pip install 'hera' 'pipekit-sdk>=7.1.0'
python examples/pytorch-fashion-mnist/workflow.py
```

The SDK package installs as `hera` today. The script submits the pipeline, prints a link to watch it live in the Pipekit UI, and exits. Set `PIPEKIT_CLUSTER` to target a cluster other than `free-trial-cluster`. Print the manifest without submitting with `RENDER_ONLY=1 python workflow.py`.

## Run the native Workflow

```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=fashion-mnist-example examples/pytorch-fashion-mnist/workflow.yaml
```

## What you get

The run finishes in a few minutes. Each `train` pod logs its test accuracy, for example:

```text
train config 0: lr=0.05 hidden=64 accuracy=0.6280
train config 1: lr=0.1 hidden=128 accuracy=0.6955
train config 2: lr=0.2 hidden=256 accuracy=0.7290
```

The `register` step selects the most accurate model and exposes it as an output parameter, `selected`, so the choice is visible in the run graph even after the pods are cleaned up:

```json
{
  "framework": "pytorch",
  "dataset": "fashion-mnist",
  "selected": { "idx": "2", "lr": 0.2, "hidden": 256, "accuracy": 0.723 }
}
```

## Test the logic locally

```bash
pip install torch
python examples/pytorch-fashion-mnist/test_model.py
```

The model and training functions are plain PyTorch, so you can test them in milliseconds before the job ever touches the cluster.

## Scaling up

The free trial version keeps the model and dataset small so it fits the trial cluster's limits. For the production shape of this pipeline, including a model registry and GPU training, see [ML Pipelines](https://docs.pipekit.io/use-cases/ml-pipelines) in the Pipekit docs.
