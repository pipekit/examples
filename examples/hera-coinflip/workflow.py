import os

from hera.workflows import DAG, Workflow, script
from pipekit_sdk.service import PipekitService

# Obtain Pipekit Hera token from environment variable
pipekit = PipekitService(token=os.environ["PIPEKIT_HERA_TOKEN"])

@script()
def flip():
    import random

    result = "heads" if random.randint(0, 1) == 0 else "tails"
    print(result)


@script()
def heads():
    print("it was heads")


@script()
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
print(
    f"Observe the run at: https://pipekit.io/pipes/{run_info['pipeUUID']}/runs/{run_info['uuid']}"
)
