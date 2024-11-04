import os
import sys
import time

from hera.workflows import Container, Resources, Step, Steps, Workflow, script
from pipekit_sdk.service import PipekitService

# Obtain Pipekit Hera token from environment variable
pipekit = PipekitService(token=os.environ["PIPEKIT_HERA_TOKEN"])

@script(image="python:alpine3.6", command=["python"], add_cwd_to_sys_path=False, resources=Resources(
        cpu_request="50m", memory_request="30Mi", cpu_limit="50m", memory_limit="30Mi"))
def flip_coin() -> None:
    import random

    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


with Workflow(
    generate_name="coinflip-",
    annotations={
        "workflows.argoproj.io/description": (
            "This is an example of coin flip defined as a sequence of conditional steps."
        ),
    },
    entrypoint="coinflip",
    namespace="argo",
    service_account_name="argo-workflow",
) as w:
    heads = Container(
        name="heads",
        image="alpine:3.6",
        command=["sh", "-c"],
        args=['echo "it was heads"'],
    )
    tails = Container(
        name="tails",
        image="alpine:3.6",
        command=["sh", "-c"],
        args=['echo "it was tails"'],
    )

    with Steps(name="coinflip") as s:
        fc: Step = flip_coin()

        with s.parallel():
            heads(when=f"{fc.result} == heads")
            tails(when=f"{fc.result} == tails")


# Submit the workflow to Pipekit
pipe_run = pipekit.submit(w, "free-trial-cluster")

# Print Run URL
run_info = pipekit.get_run(pipe_run.uuid)
if "PIPEKIT_URL" in os.environ:
    pipekit_url = os.environ["PIPEKIT_URL"]
else:
    pipekit_url = "https://pipekit.io"
print(
    f"Observe the run at: {pipekit_url}/pipes/{run_info.pipe_uuid}/runs/{run_info.uuid}"
)

# Wait for the workflow to complete
pipe_status = pipekit.get_run(pipe_run.uuid)
pipe_states = ["completed", "failed", "stopped", "terminated"]

while pipe_status.status not in pipe_states:
    time.sleep(5)
    pipe_status = pipekit.get_run(pipe_run.uuid)

# Throw non-zero exit code if workflow failed
if pipe_status.status != "completed":
    print(f"Exiting - Workflow status: {pipe_status.status}")
    sys.exit(1)
else:
    print(f"Workflow status: {pipe_status.status}")
    sys.exit(0)
