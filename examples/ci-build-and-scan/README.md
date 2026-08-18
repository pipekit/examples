# CI build and scan

A CI pipeline shaped like the ones platform teams run for their own services: check out, build an image, run unit tests and lint in parallel, scan the image, publish.

Set `fail-on-critical` to `true` and the scan step reports a critical CVE and exits non-zero. The rest of the DAG stops and `publish` never runs, which is a useful thing to show: a failing gate, the log that explains why, and nothing shipped.

## Files

| File | Purpose |
|---|---|
| `workflow-template.yaml` | The `WorkflowTemplate`. Register it in Pipekit under Templates, or apply it to a cluster. |
| `workflow.yaml` | A standalone `Workflow` with the same steps inlined. |

## Parameters

| Name | Example | Meaning |
|---|---|---|
| `service` | `payments-api` | Service being built |
| `git-ref` | `main` | Ref to build |
| `fail-on-critical` | `false` | Fail the scan step on a critical finding |

## Running it

```bash
# green
pipekit submit -c <cluster-name> -n <namespace> -p fail-on-critical=false workflow.yaml

# blocked by the scan gate
pipekit submit -c <cluster-name> -n <namespace> -p fail-on-critical=true workflow.yaml
```
