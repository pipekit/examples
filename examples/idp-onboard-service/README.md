# Onboard a service

The flagship internal developer platform task: one submission takes a new service from nothing to ready. It creates a repository, provisions a namespace with a quota and a network policy, seeds a CI pipeline, opens a change ticket and notifies the team.

The `create-repository` step fails on its first attempt with a `429` from the Git API and succeeds on the retry. That is deliberate. Upstream APIs rate limit, and the point is that the developer who submitted the form never sees it, while the retry stays visible in the run tree.

## Files

| File | Purpose |
|---|---|
| `workflow-template.yaml` | The `WorkflowTemplate`. Register it in Pipekit under Templates, or apply it to a cluster. |
| `workflow.yaml` | A standalone `Workflow` with the same steps inlined. |

## Parameters

| Name | Example | Meaning |
|---|---|---|
| `service-name` | `customer-portal` | Name of the new service |
| `team` | `team-channels` | Owning team |
| `environment` | `staging` | Environment to provision for |
| `cost-centre` | `CC-4471` | Chargeback label on the namespace |

## Reusing this from another workflow

The steps read `{{workflow.parameters.*}}`, which resolve against the **calling** workflow, not the template. So a workflow that references this template has to declare all four parameters itself:

```yaml
spec:
  arguments:
    parameters:
      - name: service-name
        value: payments-ledger
      - name: team
        value: team-ml
      - name: environment
        value: staging
      - name: cost-centre
        value: CC-8820
  templates:
    - name: main
      steps:
        - - name: onboard
            templateRef:
              name: onboard-service
              template: main
```

Omit any one of them and submission fails with `failed to resolve {{workflow.parameters.<name>}}`. Convert the templates to `inputs.parameters` if you would rather the template own its own contract.
