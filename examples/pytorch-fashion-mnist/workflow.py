"""The same Fashion-MNIST pipeline authored with the Argo Workflows Python SDK.

This builds the identical prep -> train (fan-out) -> register DAG as ``workflow.yaml``
and submits it to Pipekit. Data and ML teams usually author in Python, so this is the
canonical way to write the pipeline; ``workflow.yaml`` is the same graph as a plain
manifest for the GitOps path.

Run it from the repo dev shell:

    pip install 'hera' 'pipekit-sdk>=7.1.0' && pipekit login
    python examples/pytorch-fashion-mnist/workflow.py

The SDK package installs as ``hera`` today. Set PIPEKIT_CLUSTER to target a cluster
other than the free trial one. Print the manifest instead of submitting with
``RENDER_ONLY=1 python workflow.py``.
"""

import os

from hera.workflows import DAG, Container, Parameter, S3Artifact, Workflow
from hera.workflows.models import ArchiveStrategy, NoneStrategy, ResourceRequirements, ValueFrom

TORCH_INDEX = "https://download.pytorch.org/whl/cpu"

# One pod per config. Each trains a small MLP and scores it on the test set.
CONFIGS = [
    {"idx": "0", "lr": "0.05", "hidden": "64"},
    {"idx": "1", "lr": "0.10", "hidden": "128"},
    {"idx": "2", "lr": "0.20", "hidden": "256"},
]


def _resources(memory, ephemeral, cpu_limit="1"):
    return ResourceRequirements(
        requests={"cpu": "500m", "memory": "512Mi", "ephemeral-storage": "512Mi"},
        limits={"cpu": cpu_limit, "memory": memory, "ephemeral-storage": ephemeral},
    )


def _none_archive():
    return ArchiveStrategy(none=NoneStrategy())


PREP_SCRIPT = r"""
set -e
pip install --quiet --no-cache-dir torch torchvision --index-url {{workflow.parameters.torch_index}}
python - <<'PY'
import os
import torch
from torchvision import datasets, transforms

to_tensor = transforms.ToTensor()
train_ds = datasets.FashionMNIST("/tmp/d", train=True, download=True, transform=to_tensor)
test_ds = datasets.FashionMNIST("/tmp/d", train=False, download=True, transform=to_tensor)

def take(dataset, count):
    images = torch.stack([dataset[i][0] for i in range(count)])
    labels = torch.tensor([dataset[i][1] for i in range(count)])
    return images, labels

train_x, train_y = take(train_ds, 8000)
test_x, test_y = take(test_ds, 2000)
os.makedirs("/tmp/out", exist_ok=True)
torch.save({"train_x": train_x, "train_y": train_y, "test_x": test_x, "test_y": test_y}, "/tmp/out/data.pt")
print("prep: train", tuple(train_x.shape), "test", tuple(test_x.shape))
PY
"""

TRAIN_SCRIPT = r"""
set -e
pip install --quiet --no-cache-dir torch --index-url {{workflow.parameters.torch_index}}
python - <<'PY'
import json
import os
import torch
from torch import nn

idx = "{{inputs.parameters.idx}}"
lr = float("{{inputs.parameters.lr}}")
hidden = int("{{inputs.parameters.hidden}}")
pixels, classes = 28 * 28, 10

data = torch.load("/tmp/in/data.pt")
model = nn.Sequential(nn.Flatten(), nn.Linear(pixels, hidden), nn.ReLU(), nn.Linear(hidden, classes))
torch.manual_seed(0)
optimizer = torch.optim.SGD(model.parameters(), lr=lr)
loss_fn = nn.CrossEntropyLoss()
train_x, train_y = data["train_x"], data["train_y"]
sample_count = train_x.shape[0]
model.train()
order = torch.randperm(sample_count)
for start in range(0, sample_count, 128):
    batch = order[start : start + 128]
    optimizer.zero_grad()
    loss_fn(model(train_x[batch]), train_y[batch]).backward()
    optimizer.step()

model.eval()
with torch.no_grad():
    predictions = model(data["test_x"]).argmax(dim=1)
    accuracy = float((predictions == data["test_y"]).float().mean())

os.makedirs("/tmp/out", exist_ok=True)
torch.save(model.state_dict(), "/tmp/out/model.pt")
with open("/tmp/out/metrics.json", "w") as handle:
    json.dump({"idx": idx, "lr": lr, "hidden": hidden, "accuracy": round(accuracy, 4)}, handle)
print(f"train config {idx}: lr={lr} hidden={hidden} accuracy={accuracy:.4f}")
PY
"""

REGISTER_SCRIPT = r"""
set -e
python - <<'PY'
import glob
import json
import os
import shutil

best = None
for metrics_path in sorted(glob.glob("/tmp/candidates/*/metrics.json")):
    with open(metrics_path) as handle:
        metrics = json.load(handle)
    print("candidate:", metrics)
    if best is None or metrics["accuracy"] > best["accuracy"]:
        best = dict(metrics, _dir=os.path.dirname(metrics_path))

os.makedirs("/tmp/out", exist_ok=True)
shutil.copy(os.path.join(best["_dir"], "model.pt"), "/tmp/out/model.pt")
card = {
    "framework": "pytorch",
    "dataset": "fashion-mnist",
    "selected": {key: best[key] for key in ("idx", "lr", "hidden", "accuracy")},
}
with open("/tmp/out/model-card.json", "w") as handle:
    json.dump(card, handle, indent=2)
print("registered best model:", card["selected"])
PY
"""


def build() -> Workflow:
    with Workflow(
        generate_name="fashion-mnist-",
        entrypoint="main",
        namespace="argo",
        service_account_name="argo-workflow",
        arguments={"torch_index": TORCH_INDEX},
    ) as workflow:
        prep = Container(
            name="prep",
            image="python:3.11-slim",
            command=["bash", "-c"],
            args=[PREP_SCRIPT],
            resources=_resources(memory="1500Mi", ephemeral="3Gi"),
            outputs=[
                S3Artifact(
                    name="dataset",
                    path="/tmp/out",
                    key="{{workflow.uid}}/dataset",
                    archive=_none_archive(),
                )
            ],
        )
        train = Container(
            name="train",
            image="python:3.11-slim",
            command=["bash", "-c"],
            args=[TRAIN_SCRIPT],
            resources=_resources(memory="2Gi", ephemeral="3Gi"),
            inputs=[
                Parameter(name="idx"),
                Parameter(name="lr"),
                Parameter(name="hidden"),
                S3Artifact(name="dataset", path="/tmp/in", key="{{workflow.uid}}/dataset"),
            ],
            outputs=[
                S3Artifact(
                    name="candidate",
                    path="/tmp/out",
                    key="{{workflow.uid}}/candidates/{{inputs.parameters.idx}}",
                    archive=_none_archive(),
                )
            ],
        )
        register = Container(
            name="register",
            image="python:3.11-slim",
            command=["bash", "-c"],
            args=[REGISTER_SCRIPT],
            resources=ResourceRequirements(
                requests={"cpu": "250m", "memory": "256Mi", "ephemeral-storage": "256Mi"},
                limits={"cpu": "500m", "memory": "512Mi", "ephemeral-storage": "512Mi"},
            ),
            inputs=[
                S3Artifact(
                    name="candidates", path="/tmp/candidates", key="{{workflow.uid}}/candidates"
                )
            ],
            outputs=[
                Parameter(name="selected", value_from=ValueFrom(path="/tmp/out/model-card.json")),
                S3Artifact(
                    name="registered",
                    path="/tmp/out",
                    key="{{workflow.uid}}/registered",
                    archive=_none_archive(),
                ),
            ],
        )

        with DAG(name="main"):
            prep_task = prep()
            train_task = train(
                arguments={
                    "idx": "{{item.idx}}",
                    "lr": "{{item.lr}}",
                    "hidden": "{{item.hidden}}",
                },
                with_items=CONFIGS,
            )
            register_task = register()
            prep_task >> train_task >> register_task

    return workflow


if __name__ == "__main__":
    workflow = build()
    if os.environ.get("RENDER_ONLY"):
        print(workflow.to_yaml())
    else:
        from pipekit_sdk.service import PipekitService

        cluster = os.environ.get("PIPEKIT_CLUSTER", "free-trial-cluster")
        pipekit = PipekitService()
        pipe_run = pipekit.submit(workflow, cluster)
        print(f"submitted run {pipe_run.uuid}")
        print(f"watch live: https://pipekit.io/pipes/{pipe_run.pipe_uuid}/runs/{pipe_run.uuid}")
