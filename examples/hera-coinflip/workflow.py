from hera.workflows import DAG, Workflow, script
from hera.shared import global_config
from pipekit_sdk.service import PipekitService

pipekit = PipekitService(token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGl0eVVVSUQiOiI4OTAxNTQ1My00ZTM0LTQ4MWYtYWYwNi02Y2QyNjZjZmQ5ZDkiLCJpc0ludGVybmFsIjp0cnVlLCJDbHVzdGVyVVVJRCI6IiIsIk9yZ1VVSUQiOiIiLCJpc0FjdGl2ZSI6dHJ1ZSwiaXNzIjoicGlwZWtpdCIsImV4cCI6MTY5NTg5ODcyOX0.I3Z1-NEbEW-P9lAqhm9HylPR4QcxO_67RKtIJ194lCU')

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

pipekit.submit(w, "vcluster-test")
