[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# External Log

Sometimes you may want to use Argo Workflows to deploy a kubernetes resource that it outside of the workflow. This example shows how to do that, and demonstrates that you can capture the logs from that external resource.

The workflow deploys a kubernetes job that emits "Hello Pipekit!". You will see "Hello Pipekit!" in your Pipekit logs. Ensure you use the filter button to select the container called `hellopipekit` in order to see the logs.

## Log into Pipekit via the CLI
With the CLI installed, log into Pipekit:
```bash
pipekit login
```

## Running the native Workflow
```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=external-logs-example workflow.yaml
```
