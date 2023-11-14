[![Pipekit Logo](assets/images/pipekit-logo.png)](https://pipekit.io)

# Pipekit Argo Workflows Examples

A collection of examples designed to help you get started with Pipekit. All these examples will work out-of-the-box with the [Pipekit Getting Started guide](https://docs.pipekit.io/getting-started).

You are encouraged to fork the repo and experiment with adjusting the workflows to suit your needs.

## Getting Started

1. Create a free trial account at [pipekit.io](https://pipekit.io/signup).
2. The `README.md` accompanying each example will tell you how to run it from your terminal using the [Pipekit CLI](https://docs.pipekit.io/cli).
3. If you want to experiment with git [run conditions](https://docs.pipekit.io/pipekit/pipes/managing-pipes/run-conditions), fork this repository and connect your fork to Pipekit.

## Examples

| Example Name                                             | Description                                                                                                                                |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| [cronworkflow-example]( examples/cronworkflow-example/ ) | Runs a basic CronWorkflow.                                                                                                                 |
| [dag-diamond]( examples/dag-diamond/ )                   | Runs a basic DAG Workflow.                                                                                                                 |
| [external-logs]( examples/external-logs/ )               | Workflows deploys a kubernetes job. You can see the logs from the job within Pipekit.                                                      |
| [fan-out-fan-in]( examples/fan-out-fan-in/ )             | Shows how S3 artifact processing can be parallelized with Argo Workflows using a fan-out approach.                                         |
| [get-versions](examples/get-versions/)                   | A workflow that outputs the versions of software installed in a Pipekit free trial cluster. Available as both a Hera and a native Workflow |
| [hera-coinflip](examples/hera-coinflip/)                 | Runs a basic coinflip example using the Hera Python framework.                                                                             |
|                                                          |                                                                                                                                            |
