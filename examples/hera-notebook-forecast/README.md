[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# Hera Notebook Forecast

A notebook-driven data job for analysts. Press play in a Jupyter notebook to run a real workflow on Pipekit, with Kubernetes hidden.

The job is an energy demand forecast: it generates synthetic half-hourly demand readings for a few regions, aggregates them into daily energy totals (MWh), and fits a linear trend to forecast the next day. The job is generic, so you can swap in your own logic.

This example splits the work the way a platform team would:

- `dataplatform/`: the platform team's library. It sets the image, resource requests, service account, namespace, cluster, and the Pipekit connection. Analysts never touch it.
- `forecast_step.py`: the single Hera `@script` step an analyst writes. It uses pandas and numpy on the platform's image.
- `demand_forecast.py`: the same logic as plain Python functions, the tested source of truth.
- `test_demand_forecast.py`: a local test of that logic. Runs in milliseconds, no cluster.
- `run_forecast.ipynb`: the notebook you press play in to run the job once.
- `cron_forecast.ipynb`: the notebook that schedules the same job as a recurring cron.
- `workflow.py`: the same job as a plain script, for the terminal.

## Log into Pipekit via the CLI

With the [CLI installed](https://docs.pipekit.io/cli), log in once. This writes a token to `~/.pipekit/token` that the SDK reuses, so you do not paste a token anywhere.

```bash
pipekit login
```

## Set up the environment

This repo ships a Nix dev shell (`shell.nix` at the repo root) that provides Python and the C++ runtime the Jupyter kernel needs on NixOS. From the repo root, inside the dev shell:

```bash
direnv allow                 # or run: nix-shell
python -m venv .venv
.venv/bin/pip install hera pipekit-sdk ipykernel jupyter
```

`ipykernel` and `jupyter` let your editor run the notebook. pandas and numpy run on the cluster, not locally, so you do not need them here.

## Register the kernel

On NixOS the kernel needs `libstdc++` on `LD_LIBRARY_PATH`, or `pyzmq` fails to load and the editor reports that `jupyter and notebook` are missing. Bake that path into the kernel so it works however you launch your editor. Run this inside the dev shell, where `LD_LIBRARY_PATH` is set:

```bash
.venv/bin/python -m ipykernel install --user --name hera-forecast \
  --display-name "Python (hera-forecast)" \
  --env LD_LIBRARY_PATH "$LD_LIBRARY_PATH"
```

Re-run it after a nixpkgs upgrade or `nix-collect-garbage`, since the baked path points into the Nix store.

## Run it from the notebook

Open `examples/hera-notebook-forecast/run_forecast.ipynb` and select the `Python (hera-forecast)` kernel in the picker (top right), not a bare `Python 3.x` interpreter. Run the cells top to bottom. Set your cluster name in the `Point at your cluster` cell if it is not `free-trial-cluster`. The run cell prints a link to watch the job live in the Pipekit UI, and a later cell streams the forecast logs inline as the run produces them.

## Schedule it on a cron

Open `examples/hera-notebook-forecast/cron_forecast.ipynb` and run the cells top to bottom, the same way. Instead of running the job once, it schedules the job as a `CronWorkflow` with one call:

```python
from dataplatform import cron
from forecast_step import forecast_demand

cron('daily-demand-forecast', forecast_demand, schedule='0 6 * * *')
```

The cell prints a link to the cron's run history in the UI. Each tick of the schedule starts a new run there. The same step runs with the same platform defaults as the one-off path. A `cron_to_yaml` cell renders the manifest for the GitOps path. It is the same kind of `CronWorkflow` as the native `examples/cronworkflow-example/workflow.yaml`, with the schedule in the `schedules` list that Argo Workflows 3.6 requires.

Creating a cron is in the SDK. Managing it after creation (suspend, resume, delete, trigger) is a CLI or UI task. See the [cron CLI commands](https://docs.pipekit.io/cli/cron-workflows).

## Run it from the terminal

From the repo root, with the dev shell loaded:

```bash
.venv/bin/python examples/hera-notebook-forecast/workflow.py
```

It submits the job, prints a watch link, waits for the run to finish, and prints the logs.

### Change the cluster name

The default cluster name is `free-trial-cluster`. Set `PIPEKIT_CLUSTER` to use a different one:

```bash
export PIPEKIT_CLUSTER=my-cluster
```

## Test the logic locally

```bash
.venv/bin/python examples/hera-notebook-forecast/test_demand_forecast.py
```

The aggregation and forecast functions are plain Python, so you can test them in milliseconds before the job ever touches the cluster.
