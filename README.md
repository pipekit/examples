[![Pipekit Logo](assets/images/pipekit-logo.png)](https://pipekit.io)

# Pipekit Argo Workflows Examples

A collection of examples designed to help you get started with Pipekit. All these examples will work out-of-the-box with the [Pipekit Getting Started guide](https://docs.pipekit.io/getting-started).

## Getting Started

1. Create a free trial account at [pipekit.io](https://pipekit.io).
2. Fork this repository and connect your fork to Pipekit.
3. Tweak the examples as instructed by each README and run them in your cluster using Pipekit.

## Examples

| Example Name                                             | Description                                                                                                                                |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| [cronworkflow-example]( examples/cronworkflow-example/ ) | Runs a basic CronWorkflow.                                                                                                                 |
| [dag-diamond]( examples/dag-diamond/ )                   | Runs a basic DAG Workflow.                                                                                                                 |
| [fan-out-fan-in]( examples/fan-out-fan-in/ )             | Shows how S3 artifact processing can be parallelized with Argo Workflows using a fan-out approach.                                         |
| [get-versions](examples/get-versions/)                   | A workflow that outputs the versions of software installed in a Pipekit free trial cluster. Available as both a Hera and a native Workflow |
| [hera-coinflip](examples/hera-coinflip/)                 | Runs a basic coinflip example using the Hera Python framework.                                                                             |
|                                                          |                                                                                                                                            |
