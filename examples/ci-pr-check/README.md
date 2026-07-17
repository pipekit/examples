[![Pipekit Logo](../../assets/images/pipekit-logo.png)](https://pipekit.io)

# CI pull-request check

A pull-request check pipeline that runs on Argo Workflows. It checks out a repository, runs lint and unit tests in parallel, and reports a combined pass or fail status.

```text
checkout  ->  lint + unit-test (in parallel)
onExit:   report
```

- `checkout` clones the repository and passes the working tree to the next steps as an artifact.
- `lint` and `unit-test` run in parallel, each against the checked-out code.
- `report` is an exit handler, so it runs whether the checks pass or fail. It prints the overall result and, if given a GitHub token, posts a commit status.

This is a simplified, self-contained version of the CI that builds this examples repository (see the `ci/` directory). It runs inside the free trial cluster with no secrets: by default it checks the public `pipekit/examples` repository. The full build, test, and deploy pipeline, including multi-cluster promotion, is described in the Pipekit docs under [CI/CD](https://docs.pipekit.io/use-cases/ci-cd).

## Log into Pipekit via the CLI

With the [CLI installed](https://docs.pipekit.io/reference/cli), log in once:

```bash
pipekit login
```

## Run the Workflow

```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=ci-pr-check-example examples/ci-pr-check/workflow.yaml
```

## Check your own repository

Override the parameters to point at your project and its commands:

```bash
pipekit submit -w --cluster-name=free-trial-cluster --pipe-name=ci-pr-check-example \
  -p repo_url=https://github.com/your-org/your-repo.git \
  -p ref=main \
  -p lint_cmd="pip install --quiet ruff && ruff check ." \
  -p test_cmd="pytest" \
  examples/ci-pr-check/workflow.yaml
```

## Post a real commit status

The `report` step posts a GitHub commit status when three values are present in the pod: `GITHUB_TOKEN`, `GITHUB_REPOSITORY` (as `owner/repo`), and `GIT_SHA`. Add the token as a [secret on the pipe](https://docs.pipekit.io/using-pipekit/pipes/edit/secrets) and pass the other two as parameters or environment values. Without them the step prints the status it would post, so the example still runs with no setup.
