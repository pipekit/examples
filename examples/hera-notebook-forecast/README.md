[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# Hera Notebook Forecast

A notebook-driven data job for analysts. Press play in a Jupyter notebook to run a real workflow on Pipekit, with Kubernetes hidden.

The job is an energy demand forecast: it generates synthetic half-hourly demand readings for a few regions, aggregates them into daily energy totals (MWh), and fits a linear trend to forecast the next day. The job is generic, so you can swap in your own logic.

This example splits the work the way a platform team would:

- `dataplatform/`: the platform team's library. It sets the image, resource requests, service account, namespace, cluster, and the Pipekit connection. Analysts never touch it.
- `forecast_step.py`: the single Hera `@script` step an analyst writes. It uses pandas and numpy on the platform's image.
- `demand_forecast.py`: the same logic as plain Python functions, the tested source of truth.
- `test_demand_forecast.py`: a local test of that logic. Runs in milliseconds, no cluster.
- `run_forecast.ipynb`: the notebook you press play in.
- `workflow.py`: the same job as a plain script, for the terminal.

## Log into Pipekit via the CLI

With the [CLI installed](https://docs.pipekit.io/cli), log in once. This writes a token to `~/.pipekit/token` that the SDK reuses, so you do not paste a token anywhere.

```bash
pipekit login
```

## Set up the environment

```bash
python3 -m venv .venv
.venv/bin/pip install hera pipekit-sdk ipykernel
```

pandas and numpy run on the cluster, not locally, so you do not need them here.

## Run it from the notebook

Open `run_forecast.ipynb`, select the `.venv` kernel (top right in VSCode), and run the cells top to bottom. Set your cluster name in the `Point at your cluster` cell if it is not `free-trial-cluster`. The run cell prints a link to watch the job live in the Pipekit UI, and a later cell pulls the forecast logs inline.

## Run it from the terminal

```bash
.venv/bin/python workflow.py
```

It submits the job, prints a watch link, waits for the run to finish, and prints the logs.

### Change the cluster name

The default cluster name is `free-trial-cluster`. Set `PIPEKIT_CLUSTER` to use a different one:

```bash
export PIPEKIT_CLUSTER=my-cluster
```

## Test the logic locally

```bash
.venv/bin/python test_demand_forecast.py
```

The aggregation and forecast functions are plain Python, so you can test them in milliseconds before the job ever touches the cluster.
