[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# Dag Diamond

This example workflow executes a basic diamond workflow:

```bash
   A
  / \
 B   C
  \ /
   D
```

## Log into Pipekit via the CLI
With the CLI installed, log into Pipekit:
```bash
pipekit login
```

## Running the native Workflow
```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=dag-diamond-example workflow.yaml
```
