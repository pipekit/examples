[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# CronWorkflow Example

Pipekit can run and manage CronWorkflows

## Log into Pipekit via the CLI
With the CLI installed, log into Pipekit:
```bash
pipekit login
```

## Running the native Workflow
```bash
pipekit create cron --cluster-name=free-trial-cluster workflow.yaml
```

The cron is set to run every five minutes.

## Further CLI commands
Further cron commands are available in the [Pipekit Documentation](https://docs.pipekit.io/cli/cron-workflows)
