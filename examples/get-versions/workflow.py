import os

from hera.workflows import DAG, Container, Parameter, Workflow, Resources
from pipekit_sdk.service import PipekitService

# Obtain Pipekit Hera token from environment variable
pipekit = PipekitService(token=os.environ["PIPEKIT_HERA_TOKEN"])

items = [
    {
        "label": "app.kubernetes.io/component=workflow-controller",
        "hrname": "Argo Workflows",
        "type": "deployment",
    },
    {
        "label": "app.kubernetes.io/name=pipekit-agent",
        "hrname": "Pipekit Agent",
        "type": "deployment",
    },
    {"label": "app=minio", "hrname": "Minio", "type": "statefulset"},
]

with Workflow(
    generate_name="versions-",
    entrypoint="main",
    namespace="argo",
    service_account_name="argo-workflow",
) as w:
    kubernetes_version = Container(
        name="kubernetes-version",
        image="dtzar/helm-kubectl:3.12.3",
        command=["/bin/bash", "-c", "kubectl version"],
        resources=Resources(cpu_request="50m", memory_request="30Mi", cpu_limit="50m", memory_limit="30Mi"),
    )

    kubectl_versions = Container(
        name="kubectl-version",
        image="dtzar/helm-kubectl:3.12.3",
        command=[
            "/bin/bash",
            "-c",
            'version=$(kubectl -n pipekit get {{inputs.parameters.type}} \
                    -l {{inputs.parameters.label}} \
                    -o=jsonpath="{..image}") && \
                    echo "{{inputs.parameters.hrname}}: $version"',
        ],
        resources=Resources(cpu_request="50m", memory_request="30Mi", cpu_limit="50m", memory_limit="30Mi"),
        inputs=[
            Parameter(name="label"),
            Parameter(name="hrname"),
            Parameter(name="type"),
        ],
    )

    with DAG(name="main"):
        kubernetes_version(name="kubernetes-version")
        kubectl_versions(
            name="kubectl-version-0",
            arguments={
                "label": "{{item.label}}",
                "hrname": "{{item.hrname}}",
                "type": "{{item.type}}",
            },
            with_items=items,
        )
# Submit the workflow to Pipekit
pipe_run = pipekit.submit(w, "free-trial-cluster")

# Optionally print the logs
# pipekit.print_logs(pipe_run["uuid"], container_name="main")

# Print Run URL
run_info = pipekit.get_run(pipe_run["uuid"])
print(
    f"Observe the run at: https://pipekit.io/pipes/{run_info['pipeUUID']}/runs/{run_info['uuid']}"
)
