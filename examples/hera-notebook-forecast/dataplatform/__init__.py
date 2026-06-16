"""The data platform team's internal Hera library.

The platform team owns this module so data analysts never touch Kubernetes.
The image, resource requests, namespace, service account, cluster name, and the
Pipekit connection all live here behind sane defaults. An analyst writes a single
Hera ``@script`` function and submits it:

    from hera.workflows import script
    from dataplatform import DATA_IMAGE, DATA_RESOURCES, run

    @script(image=DATA_IMAGE, resources=DATA_RESOURCES)
    def my_job():
        print("hello from the cluster")

    run("my-job", my_job)

``run``/``submit`` send the workflow to Pipekit and print a link to watch it live.
``logs(result)`` prints a log snapshot. ``to_yaml`` returns the same workflow as a
manifest you can commit to git (the GitOps path).

These defaults target the Pipekit free trial cluster: namespace ``argo``, service
account ``argo-workflow`` (set explicitly, since the controller default is ``argo``
whose task-result permissions live in another namespace), and the small resource
footprint the trial cluster allows.
"""

import os
import time

from hera.workflows import Resources, Steps, Workflow

# Connection. The SDK defaults its URL to https://api.pipekit.io, which is correct
# for the free trial cluster, so PIPEKIT_URL only needs setting for a different env.
CLUSTER = os.environ.get("PIPEKIT_CLUSTER", "free-trial-cluster")
_UI_URL = os.environ.get("PIPEKIT_URL", "https://pipekit.io")

# Defaults the platform team controls. Analysts do not set these.
# A pandas + numpy image so the job code reads like real analyst work. We use a Docker
# Hub Verified Publisher namespace (demisto): the free trial cluster shares one egress
# IP, and Docker Hub does not count pulls from Verified Publisher namespaces against the
# anonymous rate limit, so this avoids the toomanyrequests pull failures that hit
# community images. Swap the tag (or set DATA_IMAGE) to pin a different version.
DATA_IMAGE = os.environ.get("DATA_IMAGE", "demisto/pandas:1.0.0.10120494")
# The free trial cluster applies a 200Mi memory limit when a workflow omits one. We
# set an explicit 512Mi request and limit to override that for the pandas step.
DATA_RESOURCES = Resources(
    cpu_request="250m",
    cpu_limit="500m",
    memory_request="512Mi",
    memory_limit="512Mi",
)

_NAMESPACE = "argo"
_SERVICE_ACCOUNT = "argo-workflow"


def _service():
    # token="" makes the SDK fall back to the credentials `pipekit login` wrote to
    # ~/.pipekit/token. PIPEKIT_TOKEN or PIPEKIT_HERA_TOKEN override it for headless
    # or CI use. The SDK reads PIPEKIT_URL on its own.
    from pipekit_sdk.service import PipekitService

    token = os.environ.get("PIPEKIT_TOKEN") or os.environ.get("PIPEKIT_HERA_TOKEN") or ""
    return PipekitService(token=token)


def _build(name, step):
    """Wrap a single Hera @script function as a one-step workflow with platform defaults."""
    with Workflow(
        generate_name=f"{name}-",
        entrypoint="main",
        namespace=_NAMESPACE,
        service_account_name=_SERVICE_ACCOUNT,
    ) as workflow:
        with Steps(name="main"):
            # Calling the @script function inside the Steps context registers the step
            # and its template.
            step()
    return workflow


def submit(workflow):
    """Submit a built Hera Workflow to Pipekit. Returns the PipeRun and prints a watch link."""
    pipekit = _service()
    pipe_run = pipekit.submit(workflow, CLUSTER)
    run_info = pipekit.get_run(pipe_run.uuid)
    print(f"submitted run {run_info.uuid}")
    print(f"watch live: {_UI_URL}/pipes/{run_info.pipe_uuid}/runs/{run_info.uuid}")
    return pipe_run


def run(name, step):
    """Build a one-step workflow from a @script function and submit it to Pipekit."""
    return submit(_build(name, step))


def to_yaml(name, step):
    """Return the one-step workflow as a committable manifest, without submitting."""
    return _build(name, step).to_yaml()


def logs(result, follow=False):
    """Print logs for a run. Pass the PipeRun from run()/submit(), or a run-uuid string.

    follow=True streams until the run ends (blocks the cell). Otherwise prints a
    snapshot of the run's logs.
    """
    run_uuid = getattr(result, "uuid", result)
    pipekit = _service()
    if follow:
        pipekit.print_logs(run_uuid, follow=True)
        return

    # The SDK snapshot appends empty `pod-name=`/`container-name=` query params. The API
    # parses each as a one-element [""] slice and adds a Loki matcher (podName="") that
    # matches no stream, so the snapshot returns nothing for a finished run. Query the
    # endpoint with no scope params, like the Pipekit UI and MCP, so it returns the logs.
    import requests
    from pipekit_sdk.models.model import Logs

    response = requests.get(
        f"{pipekit.users_url}/api/users/v1/runs/{run_uuid}/container_logs",
        headers={"Authorization": f"Bearer {pipekit.access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    for entry in response.json() or []:
        line = Logs.model_validate(entry)
        print(f"[{line.pod_name}][{line.container_name}] {line.output}")


def wait(result, poll_seconds=5):
    """Poll until the run reaches a terminal state and return the final status string."""
    pipekit = _service()
    run_uuid = getattr(result, "uuid", result)
    terminal = {"completed", "failed", "stopped", "terminated"}
    status = pipekit.get_run(run_uuid).status
    while status not in terminal:
        time.sleep(poll_seconds)
        status = pipekit.get_run(run_uuid).status
    return status
