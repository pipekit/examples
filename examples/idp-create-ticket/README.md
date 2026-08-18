# Create a ticket

The smallest useful internal developer platform task, and a good first one to put behind a form: a developer asks for something, the platform raises a ticket in the tracker with the right context attached and links it back to the run that created it.

Four sequential steps, so it finishes quickly and reads clearly in the UI.

## Files

| File | Purpose |
|---|---|
| `workflow-template.yaml` | The `WorkflowTemplate`. Register it in Pipekit under Templates, or apply it to a cluster. |
| `workflow.yaml` | A standalone `Workflow` with the same steps inlined. |

## Parameters

| Name | Example | Meaning |
|---|---|---|
| `summary` | `Provision test environment` | Ticket summary |
| `requester` | `n.hansen` | Who asked |
| `priority` | `3` | Ticket priority |
| `system` | `servicenow` | Target tracker |

## Running it

```bash
pipekit submit -c <cluster-name> -n <namespace> \
  -p summary="Provision test environment" -p requester=n.hansen workflow.yaml
```
