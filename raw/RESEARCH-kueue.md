# Kueue Project Research

## 1. What is this project?

**Kueue** (pronounced "cue-ay") is a Kubernetes-native **job queueing manager**, part of the `kubernetes-sigs` organization. It is a job-level manager that decides:

- **When** a job should be **admitted** to start (i.e., when its pods can be created), based on available quota.
- **When** a job should **stop** (i.e., when its active pods should be deleted).

It acts as a resource manager for batch workloads on Kubernetes, providing fair sharing, preemption, and multi-tenant resource management on top of standard Kubernetes scheduling.

- Module path: `sigs.k8s.io/kueue`
- Go version: 1.26.0
- API version: v1beta2 (respects Kubernetes deprecation policy)
- License: Apache 2.0

## 2. High-Level Architecture

### Top-Level Directory Layout

| Directory | Purpose |
|---|---|
| `apis/` | Kubernetes API types (CRDs): `kueue/v1alpha1`, `v1beta1`, `v1beta2` and `config/v1beta1`, `v1beta2` |
| `cmd/` | Entry points for binaries |
| `pkg/` | Core library code |
| `internal/` | Private implementation (mocks) |
| `client-go/` | Generated client libraries (clientset, informers, listers, applyconfigurations) |
| `config/` | Kubernetes manifests (RBAC, CRDs, webhooks), Kustomize overlays |
| `charts/` | Helm chart for deployment |
| `test/` | E2E, integration, and performance tests |
| `hack/` | Build and code-generation scripts |
| `keps/` | KEPs (Kubernetes Enhancement Proposals) -- design documents |
| `docs/`, `site/` | Documentation site |
| `examples/` | Example configurations |

### Key Binary Entry Points (`cmd/`)

| Binary | Purpose |
|---|---|
| `cmd/kueue/` | **Main controller** -- the core Kueue operator (manager binary) |
| `cmd/kueuectl/` | **CLI plugin** (`kubectl kueue`) for interacting with Kueue resources |
| `cmd/kueueviz/` | **Visualization dashboard** backend + frontend for cluster state |
| `cmd/importer/` | Tool for importing resource configurations |
| `cmd/experimental/` | Experimental binaries |

### Core Packages (`pkg/`)

| Package | Purpose |
|---|---|
| `pkg/scheduler/` | **The scheduler** -- core algorithm that matches workloads to ClusterQueues via flavor assignment and preemption |
| `pkg/cache/` | **Caching layer** -- in-memory state tracking for queues (`queue/`), scheduler cache (`scheduler/`), and hierarchy (`hierarchy/`) |
| `pkg/controller/` | **Reconcilers (controllers)** -- all Kubernetes controller logic |
| `pkg/webhooks/` | **Admission webhooks** -- validation/mutation of Kueue resources |
| `pkg/workload/` | Workload utility functions (resources, usage, admission checks) |
| `pkg/podset/` | PodSet abstractions for managing groups of homogeneous pods |
| `pkg/resources/` | Resource flavor and quota calculations |
| `pkg/metrics/` | Prometheus metrics definitions and registration |
| `pkg/features/` | Feature gate management |
| `pkg/visibility/` | On-demand visibility API for pending workloads |
| `pkg/debugger/` | Debugging utilities |
| `pkg/dra/` | Dynamic Resource Allocation support |

## 3. Main Entry Points and Core Abstractions

### Core API Objects (CRDs) -- defined in `apis/kueue/v1beta2/`

| Resource | Purpose |
|---|---|
| **Workload** | The fundamental unit of work. Contains pod sets (homogeneous pod groups), queue name, priority, admission state, and status |
| **ClusterQueue** | A cluster-scoped resource defining resource quotas (flavors, borrowing limits, cohorts). The central resource management primitive |
| **LocalQueue** | A namespaced resource that points to a ClusterQueue. Workloads are submitted to LocalQueues |
| **Cohort** | A group of ClusterQueues that can borrow resources from each other |
| **ResourceFlavor** | Defines a resource "taste" (e.g., spot vs on-demand, GPU type) with node labels/taints |
| **AdmissionCheck** | A mechanism for internal/external components to gate workload admission (e.g., provisioning requests, MultiKueue checks) |
| **WorkloadPriorityClass** | Defines priority values for workloads |

### Controller Architecture (`pkg/controller/`)

The `cmd/kueue/main.go` sets up the controller-manager via `controller-runtime`. Key controller groups:

1. **Core controllers** (`pkg/controller/core/`) -- reconcile the core Kueue API objects:
   - `WorkloadReconciler` -- manages Workload lifecycle
   - `ClusterQueueReconciler` -- manages ClusterQueue lifecycle
   - `LocalQueueReconciler` -- manages LocalQueue lifecycle
   - `CohortReconciler` -- manages Cohort lifecycle
   - `ResourceFlavorReconciler` -- manages ResourceFlavor lifecycle
   - `AdmissionCheckReconciler` -- manages AdmissionCheck lifecycle
   - `WorkloadPriorityClassReconciler` -- manages WorkloadPriorityClass lifecycle

2. **Job framework** (`pkg/controller/jobframework/`) -- a generic framework for integrating any job type:
   - Defines `GenericJob` interface (Suspend, IsSuspended, RunWithPodSetsInfo, Finished, PodSets, IsActive, PodsReady, GVK)
   - Defines `IntegrationCallbacks` for registering new job types
   - Each integration provides its own reconciler and webhook

3. **Job integrations** (`pkg/controller/jobs/`) -- built-in integrations:
   - `job/` -- standard Kubernetes Batch/Job
   - `pod/` -- plain pods and pod groups
   - `jobset/` -- JobSet (sigs.k8s.io/jobset)
   - `ray/`, `rayjob/`, `raycluster/`, `rayservice/` -- Ray workloads
   - `kubeflow/` -- Kubeflow training jobs
   - `trainjob/` -- Kubeflow Trainer v2 jobs
   - `mpijob/` -- MPI jobs
   - `deployment/` -- Deployments (serving workloads)
   - `statefulset/` -- StatefulSets (serving workloads)
   - `appwrapper/` -- AppWrapper integration
   - `leaderworkerset/` -- LeaderWorkerSet
   - `sparkapplication/` -- Spark applications

4. **Admission check controllers** (`pkg/controller/admissionchecks/`):
   - `provisioning/` -- Integration with cluster-autoscaler ProvisioningRequest
   - `multikueue/` -- Multi-cluster job dispatching

### Scheduler (`pkg/scheduler/`)

The scheduler is the heart of Kueue. Its main components:
- **Scheduler struct** -- orchestrates admission: finds workloads, assigns flavors, handles preemption
- **FlavorAssigner** (`pkg/scheduler/flavorassigner/`) -- selects which resource flavors to use for each pod set
- **Preemptor** (`pkg/scheduler/preemption/`) -- handles preemption with various strategies (fair sharing, hierarchical, within-cohort)
- **Fair sharing** iterator -- iterates workloads in fair-share order

### Cache (`pkg/cache/`)

- `scheduler/` -- ClusterQueue cache: tracks resource usage, flavors, TAS (topology-aware scheduling) state
- `queue/` -- Queue manager: maintains queue hierarchies, inadmissible workload tracking, cluster queue assignments

### CLI (`cmd/kueuectl/`)

A kubectl plugin for managing Kueue resources from the command line.

### Visualization (`cmd/kueueviz/`)

A web-based dashboard for visualizing Kueue cluster state, with a Go backend and frontend.

## 4. External Dependencies and Frameworks

### Core Kubernetes Dependencies
- **controller-runtime** (`sigs.k8s.io/controller-runtime v0.23.3`) -- the core framework for building Kubernetes controllers
- Kubernetes API machinery -- `k8s.io/api`, `k8s.io/apimachinery`, `k8s.io/client-go`, `k8s.io/apiserver`, `k8s.io/component-base`
- **cert-manager** (`github.com/cert-manager/cert-manager`) -- for webhook certificate management
- **open-policy-agent/cert-controller** -- alternative certificate management

### Job Type Integrations
- **JobSet** (`sigs.k8s.io/jobset`) -- batch job sets
- **LeaderWorkerSet** (`sigs.k8s.io/lws`) -- leader-worker pattern workloads
- **Ray** (`github.com/ray-project/kuberay/ray-operator`) -- Ray distributed computing
- **Kubeflow** -- training-operator, trainer, MPI operator, spark-operator
- **AppWrapper** (`github.com/project-codeflare/appwrapper`)

### Other
- **Prometheus** client libraries -- metrics and monitoring
- **Ginkgo/Gomega** -- testing framework
- **Cobra** -- CLI framework for kueuectl
- **cluster-autoscaler** ProvisioningRequest API -- for advanced autoscaling
- **DRA (Dynamic Resource Allocation)** -- `sigs.k8s.io/dra-example-driver`
- **Cluster Inventory API** (`sigs.k8s.io/cluster-inventory-api`) -- for multi-cluster resource management

## 5. Current Repository State

### Active Branch
- `main` is the primary development branch.

### Recent Commits (from HEAD)
1. `b4deeaf4e` -- hack/releasing: add patch upgrade note to patch releases
2. `aa6e3b956` -- test: bump TAS RayJob e2e head CPU and CQ quota for Ray 2.53.0
3. `28bd5ac22` -- Commonize gauge metric reporting for localqueue and clusterqueue reconciler
4. `fd5bd86c3` -- docs: add Mukund's KubeCon EU 2026 talk
5. `4f390e857` -- fix: Avoid nil pointer panic for fairshare ordering

### Release Branches
Active maintenance tracks: `release-0.17` (latest), `release-0.16`, `release-0.15`, with older versions back to `release-0.1`.

### 2026 Roadmap Priorities (from README)
1. **MultiKueue** improvements -- elastic RayJob support, workload-level admission constraints, cross-cluster preemption prevention, long-running service support
2. General focus on multi-cluster job dispatching

### KEPs (Design Proposals)
The `keps/` directory contains many design proposals covering major features including:
- MultiKueue (multi-cluster dispatching)
- Topology-aware scheduling
- Fair sharing and preemption
- Dynamic Resource Allocation (DRA)
- Admission checks
- Partial admission and dynamic reclaim
- Concurrent admission
- Failure recovery
- Kueue visualization

### Build System
- Makefile-based build system
- Container images published to `us-central1-docker.pkg.dev/k8s-staging-images/kueue`
- Multi-arch builds (amd64, arm64, s390x, ppc64le)
- Helm chart in `charts/kueue/`
- Requires Kubernetes 1.29+

### Testing
- Unit tests, integration tests, and E2E tests
- E2E tests run against Kind clusters at K8s versions 1.33, 1.34, 1.35
- Performance/scheduling benchmarks in `test/performance/`
- Testgrid dashboards for all test suites
