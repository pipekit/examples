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
manifest you can commit to git (the GitOps path). ``cron`` schedules the same job to
run on a recurring basis; re-running it with the same name updates the existing cron.
``suspend_cron``, ``resume_cron``, ``delete_cron``, and ``get_cron`` manage that cron
after you create it. They need pipekit-sdk 2.1.2 or newer.

These defaults target the Pipekit free trial cluster: namespace ``argo``, service
account ``argo-workflow`` (set explicitly, since the controller default is ``argo``
whose task-result permissions live in another namespace), and the small resource
footprint the trial cluster allows.
"""

import os
import time

from hera.workflows import CronWorkflow, Resources, Steps, Workflow

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


def _build_cron(name, step, schedule, concurrency_policy="Replace", starting_deadline_seconds=0, timezone=None):
    """Wrap a single Hera @script function as a scheduled CronWorkflow with platform defaults.

    Mirrors _build, but the job runs on a schedule instead of once. The cron uses a stable
    name, not generate_name, so creating it again targets the same cron object. Each tick of
    the schedule starts a new run under that cron. concurrency_policy and
    starting_deadline_seconds match the native examples/cronworkflow-example.

    The schedule goes into the `schedules` list, not the older singular `schedule` field.
    Argo Workflows 3.6 deprecated `schedule` and the cluster CRD now requires `schedules`,
    so the singular field fails validation with "spec.schedules: Required value".
    """
    with CronWorkflow(
        name=name,
        entrypoint="main",
        namespace=_NAMESPACE,
        service_account_name=_SERVICE_ACCOUNT,
        schedules=[schedule],
        concurrency_policy=concurrency_policy,
        starting_deadline_seconds=starting_deadline_seconds,
        timezone=timezone,
    ) as cron_workflow:
        with Steps(name="main"):
            step()
    return cron_workflow


def _run_history_link(pipekit, name):
    """Return the UI run-history URL for a cron's pipe, or None if no pipe matches.

    The create path gets the pipe uuid straight from the API response. The update path
    does not, so we look the pipe up by name. Pipekit names the pipe after the cron, so a
    name match points at the same pipe the run history lives under.
    """
    cluster = pipekit.get_cluster_by_name(CLUSTER)
    if cluster is None:
        return None
    for pipe in pipekit.list_pipes(cluster.uuid):
        if pipe.name == name:
            return f"{_UI_URL}/pipes/{pipe.uuid}"
    return None


def create_cron(cron_workflow):
    """Create a built CronWorkflow on Pipekit, or update it if the name already exists.

    The call is idempotent on the cron name. An analyst re-running the cell with a changed
    schedule updates the existing cron instead of failing, so there is no delete-first step.
    Prints whether it created or updated, plus a link to the cron's run history. Returns the
    PipeRun on create, or None on update, since the update call returns the cron spec rather
    than a run.
    """
    pipekit = _service()
    name = cron_workflow.name
    schedule = ", ".join(cron_workflow.schedules or [])
    try:
        pipe_run = pipekit.create(cron_workflow, CLUSTER)
    except Exception as err:
        if "already exists" not in str(err):
            raise
        pipekit.update_cron(cron_workflow, CLUSTER)
        print(f"updated cron {name} (schedule {schedule})")
        if link := _run_history_link(pipekit, name):
            print(f"run history: {link}")
        return None
    print(f"created cron {name} (schedule {schedule})")
    print(f"run history: {_UI_URL}/pipes/{pipe_run.pipe_uuid}")
    return pipe_run


def cron(name, step, schedule, concurrency_policy="Replace", starting_deadline_seconds=0, timezone=None):
    """Schedule a @script function to run on a recurring basis, via Pipekit.

    schedule is a standard cron expression, for example "0 6 * * *" for 06:00 every day. The
    job runs with the same platform defaults as run(): the data image, resources, namespace,
    and service account. The call is idempotent on the name, so re-running it with a changed
    schedule updates the existing cron. Prints a link to the cron's run history in the UI.
    Use suspend_cron(name), resume_cron(name), delete_cron(name), and get_cron(name) to
    manage the cron after you create it.
    """
    return create_cron(_build_cron(name, step, schedule, concurrency_policy, starting_deadline_seconds, timezone))


def cron_to_yaml(name, step, schedule, concurrency_policy="Replace", starting_deadline_seconds=0, timezone=None):
    """Return the CronWorkflow as a committable manifest, without creating it."""
    return _build_cron(name, step, schedule, concurrency_policy, starting_deadline_seconds, timezone).to_yaml()


def suspend_cron(name):
    """Suspend the cron so it stops scheduling new runs. Returns the updated cron spec.

    Suspend pauses the schedule; runs already started keep going. Call resume_cron(name) to
    schedule again. name is the cron name you passed to cron(), in the platform namespace.
    """
    pipekit = _service()
    cron_model = pipekit.suspend_cron(CLUSTER, _NAMESPACE, name)
    print(f"suspended cron {name}")
    return cron_model


def resume_cron(name):
    """Resume a suspended cron so it schedules runs again. Returns the updated cron spec."""
    pipekit = _service()
    cron_model = pipekit.resume_cron(CLUSTER, _NAMESPACE, name)
    print(f"resumed cron {name}")
    return cron_model


def delete_cron(name):
    """Delete the cron. Runs it already started are not affected."""
    pipekit = _service()
    pipekit.delete_cron(CLUSTER, _NAMESPACE, name)
    print(f"deleted cron {name}")


def get_cron(name):
    """Fetch the live cron and print its schedule and whether it is suspended.

    Returns the full cron spec, so you can read other fields off the returned object.
    """
    pipekit = _service()
    cron_model = pipekit.get_cron(CLUSTER, _NAMESPACE, name)
    schedules = ", ".join(cron_model.spec.schedules or [])
    state = "suspended" if cron_model.spec.suspend else "active"
    print(f"cron {name}: schedule {schedules}, {state}")
    return cron_model


def logs(result, follow=False, timeout_seconds=3900):
    """Print logs for a run. Pass the PipeRun from run()/submit(), or a run-uuid string.

    follow=True streams the run's logs live: it backfills the history so far, then prints
    new lines as they arrive, and returns when the run finishes. This blocks the cell while
    the run is active. Otherwise it prints a one-off snapshot of the logs.

    timeout_seconds caps how long follow=True waits. If the run never sends an end-of-stream
    signal, the stream stops after this and prints a note, so the cell cannot hang forever.
    The default matches wait().
    """
    run_uuid = getattr(result, "uuid", result)
    pipekit = _service()
    if follow:
        _stream_logs(pipekit, run_uuid, timeout_seconds)
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


_TERMINAL_STATES = {"completed", "failed", "stopped", "terminated"}


def _run_status(pipekit, run_uuid):
    """Return the run's status, or "" if the status check itself fails.

    Used only to decide whether to keep reconnecting, so a transient failure here should
    not stop the stream. An unknown status reads as not-terminal and we keep waiting.
    """
    try:
        return pipekit.get_run(run_uuid).status
    except Exception:  # noqa: BLE001 - best-effort check; any failure means "keep waiting"
        return ""


def _stream_logs(pipekit, run_uuid, timeout_seconds):
    """Stream a run's logs over Server-Sent Events until the run ends.

    The SDK's follow path builds the stream URL with empty `pod-name=`/`container-name=`
    params, which the API turns into a Loki matcher that matches no stream, so it prints
    nothing. We hit `container_logs_stream` with no scope params, the same workaround the
    snapshot path uses, and parse the SSE ourselves.

    The server sends three kinds of `data:` events: a `ping` keep-alive every few seconds,
    a JSON log line, and a final `close` once the run has been finished for two ticks. The
    chunked connection can drop before `close` arrives. On a busy cluster the pod can be
    slow to start, and the connection may drop several times before any logs appear. We
    reconnect from the last event id we saw, so the resumed stream does not replay the
    backfill, and we keep reconnecting while the run is still pending or running. We stop
    once the run reaches a terminal state or the wall-clock deadline passes, so the cell
    cannot hang.
    """
    import json

    import requests
    from pipekit_sdk.models.model import Logs

    url = f"{pipekit.users_url}/api/users/v1/runs/{run_uuid}/container_logs_stream"
    deadline = time.monotonic() + timeout_seconds
    data_prefix = "data: "
    id_prefix = "id: "
    last_event_id = ""
    printed_any_log = False
    waiting_notice_shown = False
    backoff_seconds = 1

    # Connection-level drops, not bad responses. raise_for_status() still raises on a
    # 4xx/5xx, so a real auth or routing error surfaces instead of looping.
    transient = (
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    )

    while time.monotonic() < deadline:
        # last-event-id resumes the stream after the last line we printed, so a reconnect
        # does not replay the whole history. The server pings every few seconds, so a 60s
        # read gap means the connection is dead.
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {pipekit.access_token}",
                "Cache-Control": "no-cache",
                "last-event-id": last_event_id,
            },
            stream=True,
            timeout=(10, 60),
        )
        response.raise_for_status()

        try:
            for raw in response.iter_lines(decode_unicode=True):
                if time.monotonic() > deadline:
                    print(f"stopped following after {timeout_seconds}s; the run may still be active")
                    return

                line = raw.strip() if raw else ""
                if not line:
                    continue

                if line.startswith(id_prefix):
                    last_event_id = line[len(id_prefix) :]
                    continue
                if not line.startswith(data_prefix):
                    continue

                payload = line[len(data_prefix) :]
                if payload == "ping":
                    continue
                if payload == "close":
                    return

                # A real log line means the stream is healthy, so reset the backoff.
                backoff_seconds = 1
                printed_any_log = True
                entry = Logs.model_validate(json.loads(payload))
                print(f"[{entry.pod_name}][{entry.container_name}] {entry.output}")
        except transient:
            pass  # the connection dropped; the status check below decides what to do
        finally:
            response.close()

        # The stream ended without a `close`. Reconnect only while the run is still active.
        # A terminal run that dropped its stream is genuinely finished, so stop there.
        if _run_status(pipekit, run_uuid) in _TERMINAL_STATES:
            return
        # Before any logs appear, tell the user we are waiting on the pod. After logs have
        # started, a drop reconnects silently and resumes from last_event_id.
        if not printed_any_log and not waiting_notice_shown:
            print("waiting for the run to produce logs (the pod may still be starting)...")
            waiting_notice_shown = True
        time.sleep(backoff_seconds)
        backoff_seconds = min(backoff_seconds * 2, 10)

    print(f"stopped following after {timeout_seconds}s; the run may still be active")


def wait(result, poll_seconds=5, timeout_seconds=3900):
    """Poll until the run reaches a terminal state and return the final status string.

    Raises TimeoutError if the run does not finish within timeout_seconds. The default
    sits above the free trial cluster's 1 hour activeDeadlineSeconds, so a run that hits
    its own deadline returns a terminal status before this fires.
    """
    pipekit = _service()
    run_uuid = getattr(result, "uuid", result)
    terminal = {"completed", "failed", "stopped", "terminated"}
    start = time.monotonic()
    status = pipekit.get_run(run_uuid).status
    while status not in terminal:
        if time.monotonic() - start > timeout_seconds:
            raise TimeoutError(f"run {run_uuid} did not finish within {timeout_seconds}s")
        time.sleep(poll_seconds)
        status = pipekit.get_run(run_uuid).status
    return status
