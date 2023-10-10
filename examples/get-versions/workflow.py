from hera.workflows import (
    DAG,
    Container,
    Parameter,
    Workflow,
)
from pipekit_sdk.service import PipekitService
import os
pipekit = PipekitService(token=os.environ['PIPEKIT_HERA_TOKEN'])

items = [
    {"label": "app.kubernetes.io/component=workflow-controller", "hrname": "Argo Workflows", "type": "deployment"},
    {"label": "app.kubernetes.io/name=pipekit-agent", "hrname": "Pipekit Agent", "type": "deployment"},
    {"label": "app=minio", "hrname": "Minio", "type": "statefulset"}
]

with Workflow(
    generate_name="versions-",
    entrypoint="main",
    namespace="argo",
    service_account_name="argo-workflow"
) as w:
    kubernetes_version = Container(
        name="kubernetes-version",
        image="dtzar/helm-kubectl",
        command=["/bin/bash", "-c", "kubectl version"]
    )

    kubectl_versions = Container(
        name="kubectl-version",
        image="dtzar/helm-kubectl",
        command=["/bin/bash", "-c", "version=$(kubectl -n pipekit get {{inputs.parameters.type}} -l {{inputs.parameters.label}} -o=jsonpath=\"{..image}\") && echo \"{{inputs.parameters.hrname}}: $version\""],
        inputs=[
            Parameter(name="label"),
            Parameter(name="hrname"),
            Parameter(name="type")
        ],
    )

    with DAG(name="main"):
        k8s_version = kubernetes_version(name="kubernetes-version")
        ctl_version_0 = kubectl_versions(name="kubect-version-0", arguments=items[0])
        ctl_version_1 = kubectl_versions(name="kubect-version-1", arguments=items[1])
        ctl_version_2 = kubectl_versions(name="kubect-version-2", arguments=items[2])

        [k8s_version, ctl_version_0, ctl_version_1, ctl_version_2]

pipekit.submit(w, "free-trial-cluster")
