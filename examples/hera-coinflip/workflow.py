from hera.workflows import DAG, Workflow, script
from hera.shared import global_config
from pipekit_sdk.service import PipekitService

pipekit = PipekitService(token='REPLACE_ME')

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

with Workflow(generate_name="coinflip-", entrypoint="d", namespace="argo", service_account_name="argo-workflow") as w:
    with DAG(name="d") as s:
        f = flip()
        heads().on_other_result(f, "heads")
        tails().on_other_result(f, "tails")

pipekit.submit(w, "REPLACE_ME")
