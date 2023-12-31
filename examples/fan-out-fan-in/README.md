[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# Fan Out Fan In

This example workflow shows how S3 artifact processing can be parallelized with Argo Workflows using a fan-out approach.

It also includes further artifact configurations:
- `artifactGC` strategy for all artifacts, plus an over-ride for the final output step
- including `{{workflow.uid}}` in the artifact key
- `podSpecPatch` for increased resources for the `reduce` step

## Log into Pipekit via the CLI
With the CLI installed, log into Pipekit:
```bash
pipekit login
```

## Running the native Workflow
```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=fan-out-fan-in-example workflow.yaml
```
