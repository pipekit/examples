# Provision a repository

Self-service repository provisioning, the kind of task an internal developer platform puts behind a form. A developer supplies a repository name, an owning team and a service type. The workflow creates the repository from a scaffold, applies branch protection, grants team access, seeds a CI pipeline and registers the service in a catalog.

The steps here print what they would do rather than calling a real Git provider, so the example runs anywhere. Replace the container in each template with your own tooling to make it real.

## Files

| File | Purpose |
|---|---|
| `workflow-template.yaml` | The `WorkflowTemplate`. Register it in Pipekit under Templates and submit it with parameters. |
| `workflow.yaml` | A standalone `Workflow` with the same steps inlined, for a one-off run. |

## Parameters

| Name | Example | Meaning |
|---|---|---|
| `repo-name` | `payments-api` | Name of the repository to create |
| `team` | `team-payments` | Team that gets maintainer access |
| `visibility` | `internal` | Repository visibility |
| `service-type` | `service` | Scaffold to use: `service`, `library` or `infra` |
| `enable-ci` | `true` | Seed a CI pipeline in the new repository |

## Running it

Through Pipekit Templates, which applies the template to your cluster and gives you a parameter form:

1. Add this repository under Templates in Pipekit, pointing at `examples/idp-provision-repository/workflow-template.yaml`.
2. Submit it, choosing a cluster, a namespace and your parameter values.

Or submit the standalone workflow with the CLI:

```bash
pipekit submit -c <cluster-name> -n <namespace> workflow.yaml
```
