## Principles

### CI/CD Pipelines

#### Pipelines as code

- The definition of the pipeline for testing/building/deploying should be put together with project code, so that we can make sure it can work properly within a certain project
- The pipeline should be also well tested before applying any change on it.
- Example: GitHub actions
  - The workflow that triggered by a pull request event is defined in a git repository along with other code.
  - When a pull request that try to add some changes on it, the workflow will setup with the change in that PR.
  - At the same time, other PR will still use the workflow defined in the master branch.
- Counter example: Prow
  - All presubmit/postsubmit jobs are pre-defined in a centrallized repository, you cannot change them only for a certain pull request.

#### Reusable pipeline

> A workflow must contain the following basic components:
>
> 1. One or more *events* that will trigger the workflow.
> 2. One or more *jobs*, each of which will execute on a *runner* machine and run a series of one or more *steps*.
> 3. Each step can either run a script that you define or run an **action**, which is a reusable extension that can simplify your workflow.
>
> Reference: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows#workflow-basics

- Why is it reusable?
  - Step is a building block:
    - Action contains multiple Step
    - Step can call an Action
  - Job is building block:
    - Workflow contains multiple Job
    - Job can call a Workflow
- Counter example: tekton pipeline
  - Pipeline contains multiple Task, Task contains multiple Step
  - Pipeline cannnot call another Pipeline, Task cannot call another Task, Step cannot call another Step.
  - No building block, so you have to copy and paste the same code if you want to reuse it in another pipeline/task/step.

#### Performance

- The basic performance of a CI/CD system
  - Efficiency = User Time / (User Time + System Time)
    - `User Time` is the time from the actual execution to the completion of the **user-defined task**.
      - It depends on what users needed to define when using the CI/CD system.
    - `System Time`  includes all the time spent on things that the user doesn't care about. 
      - For example, in tekton, it includes github event processing, pipelinerun/task creating/updating, pod creating/deleting, init-container excution, parameters/results passing, etc.
- Monitor and improve the performance of the **the user-defined  tasks**
  - For example, enable build cache for golang, maven, docker, etc.

#### Reliability

The basic reliability of a CI/CD system:
- Pipeline Reliability = (Number of successful runs - Number of failed runs caused by **user-defined task**) / Total number of runs
  - Failures caused by **user-defined task** are not counted in the CI/CD system's failure count, as this is not the responsibility of the CI/CD system.

### Development Environment

#### Reproducible-environment

Setting up a development environment is a significant hurdle, especially for highly complex environments. It may require building numerous components locally to achieve even a basic setup. Furthermore, due to incomplete documentation and varying interpretations of the documentation by developers, the final setup may differ significantly from each developer's. This is even more pronounced compared to a standard(CI) test environment.

While remote development environment is an option, but the performance and ease of use is often less than ideal. For example, network latency and lag, the long upload/download times, or various security/compliance restrictions within the company prevent us from using it as effectively as local development environment.

## How to

### Development Environment

#### Docker as a service

Why we need Docker as a service instead of building Docker images locally?

You might not be able to build a Docker image locally.
- Installing and maintaining Docker on a laptop may not be straightforward for many people, including those on macOS and Windows.
- The network environment of a local laptop may differ from that of a data center, and the Dockerfile may require accessing certain websites to install packages.
- The Dockerfile may require a large amount of CPU, memory or disk space resources to build the image, which may not be available on a local laptop.

#### Kubernetes as a service

Each developer may need a separate Kubernetes environment. Yes, each one, because we need them to be independent of each other. Therefore, we need Kubernetes as a service.
Then developers can simply deploy their Docker images to Kubernetes.
