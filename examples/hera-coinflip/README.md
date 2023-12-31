[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# Hera Coinflip

This example runs the [coinflip workflow](https://github.com/argoproj-labs/hera/blob/main/examples/workflows/upstream/coinflip.py).

## Log into Pipekit via the CLI
With the CLI installed, log into Pipekit:
```bash
pipekit login
```

## Running the Hera Workflow
Install the Pipekit SDK. Set an environment variable with your Hera token, then run workflow.py

```bash
pip install pipekit-sdk
export PIPEKIT_HERA_TOKEN=$(pipekit hera -r)
python workflow.py
```

### Change the cluster name
If you're using a different cluster name, modify `free-trial-cluster` in the line `pipe_run = pipekit.submit(w, "free-trial-cluster")` of `workflow.py`.
