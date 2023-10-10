[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# Get Versions

This is specifically designed for use inside a Pipekit free trial cluster. It allows you to see the versions of the software installed within the cluster.

It will not work elsewhere because the kubectl commands are looking for specifically tagged deployments. Feel free to fork this repository and adjust the kubectl commands to work with your own cluster.

## Log into Pipekit via the CLI
With the CLI installed, log into Pipekit:
```bash
pipekit login
```

## Running the native Workflow
```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=free-trial-cluster-versions workflow.yaml
```

## Running the Hera Workflow
Install the Pipekit SDK. Set an environment variable with your Hera token, then run workflow.py

```bash
pip install pipekit-sdk
export PIPEKIT_HERA_TOKEN=$(pipekit hera | cut -c10-)
python3 workflow.py
```

## Change the cluster name
If you're using a different cluster name, modify `free-trial-cluster` on the last line.
