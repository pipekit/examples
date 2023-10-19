import os
import time
import sys

from hera.workflows import DAG, Resources, Workflow, script
from pipekit_sdk.service import PipekitService

# Obtain Pipekit Hera token from environment variable
pipekit = PipekitService(token=os.environ["PIPEKIT_HERA_TOKEN"])


@script(
    resources=Resources(
        cpu_request="50m", memory_request="30Mi", cpu_limit="50m", memory_limit="30Mi"
    )
)
def flip():
    import random

    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


@script(
    resources=Resources(
        cpu_request="50m", memory_request="30Mi", cpu_limit="50m", memory_limit="30Mi"
    )
)
def heads():
    print("it was heads")


@script(
    resources=Resources(
        cpu_request="50m", memory_request="30Mi", cpu_limit="50m", memory_limit="30Mi"
    )
)
def tails():
    print("it was tails")


with Workflow(
    generate_name="coinflip-",
    entrypoint="d",
    namespace="argo",
    service_account_name="argo-workflow",
) as w:
    with DAG(name="d") as s:
        f = flip()
        heads().on_other_result(f, "heads")
        tails().on_other_result(f, "tails")

# Submit the workflow to Pipekit
pipe_run = pipekit.submit(w, "free-trial-cluster")

# Optionally print the logs
# pipekit.print_logs(pipe_run["uuid"], container_name="main")

# Print Run URL
run_info = pipekit.get_run(pipe_run["uuid"])
if "PIPEKIT_URL" in os.environ:
    pipekit_url = os.environ["PIPEKIT_URL"]
else:
    pipekit_url = "https://pipekit.io"
print(
    f"Observe the run at: {pipekit_url}/pipes/{run_info['pipeUUID']}/runs/{run_info['uuid']}"
)

# Wait for the workflow to complete
pipe_status = pipekit.get_run(pipe_run["uuid"])
pipe_states = ["completed", "failed", "stopped", "terminated"]

while pipe_status['status'] not in pipe_states:
    time.sleep(5)
    pipe_status = pipekit.get_run(pipe_run["uuid"])

# Throw non-zero exit code if workflow failed
if pipe_status['status'] != "completed":
    print(f"Exiting - Workflow status: {pipe_status['status']}")
    sys.exit(1)
else:
    print(f"Workflow status: {pipe_status['status']}")
