# Slurm Workload Manager Project Research

## 1. What is this project?

**Slurm** (Simple Linux Utility for Resource Management) is an open-source cluster resource management and job scheduling system. It is the workload manager of choice for many of the world's top supercomputers and HPC (High Performance Computing) clusters.

Slurm provides three key functions:
1. **Resource allocation** -- allocates exclusive and/or non-exclusive access to compute nodes to users for a duration of time.
2. **Job framework** -- provides a framework for starting, executing, and monitoring work (normally parallel jobs) on the set of allocated nodes.
3. **Queue arbitration** -- arbitrates conflicting requests for resources by managing a queue of pending work.

The project originated at Lawrence Livermore National Laboratory (LLNL) and is now primarily maintained by **SchedMD LLC**. It is tested only under Linux.

- Version: 26.11.0-0rc1 (pre-release of the next major version)
- API version: 46.0.0 (declared in META)
- License: GNU General Public License v2+ (with OpenSSL exception)
- Protocol: SLURM_PROTOCOL_VERSION (maintained in `src/common/slurm_protocol_common.h`)
- Language: C (with some Perl, Lua, Python for extensions/testing)
- Home page: <https://slurm.schedmd.com/>

## 2. High-Level Architecture

### Top-Level Directory Layout

| Directory | Purpose |
|---|---|
| `src/` | **All source code** -- daemons, user commands, plugins, API, common libraries |
| `slurm/` | Installed include files (public API headers: `slurm.h`, `slurm_errno.h`, `slurmdb.h`, `spank.h`) |
| `doc/` | Documentation: HTML (`doc/html/`), man pages (`doc/man/` in man1/man5/man8 sections) |
| `etc/` | Sample configuration files (`slurm.conf.example`, `slurmdbd.conf.example`, init scripts, systemd service files) |
| `testsuite/` | Test suite: Expect tests (`expect/`), Python tests (`python/`), unit tests (`slurm_unit/`), C test source (`src/`) |
| `contribs/` | Optional contributed tools: Perl API, PAM module, PMI/PMI2 libraries, lua bindings, Torque/PBS compatibility wrappers, seff/sreport tools |
| `auxdir/` | Autotools helper scripts (`ax_*.m4`, `x_ac_*.m4` for feature detection) |
| `CHANGELOG/` | Per-release changelogs (e.g., `slurm-26.05.md`) |
| `debian/` | Debian packaging (produces ~20 .deb packages) |
| `tools/` | Code quality config (codespell, flake8, gitlint configurations) |
| `META` | Version metadata consumed by configure.ac and RPM |

### Key Daemon Binary Entry Points (`src/`)

| Daemon | Directory | Purpose |
|---|---|---|
| **slurmctld** | `src/slurmctld/` | **Central controller daemon** -- the brain of Slurm. Manages jobs, nodes, partitions, reservations, scheduling decisions. Single point of coordination per cluster (with backup). |
| **slurmd** | `src/slurmd/` | **Node daemon** -- runs on every compute node. Executes and monitors jobs, manages prolog/epilog, handles local resource enforcement. Sub-components: `slurmd/slurmd` (main daemon), `slurmd/common/` (shared helpers), `slurmd/slurmstepd/` (job step launcher). |
| **slurmdbd** | `src/slurmdbd/` | **Database daemon** -- stores accounting and job history data in a relational database (MySQL). Acts as the centralized accounting tier. |
| **slurmrestd** | `src/slurmrestd/` | **REST API daemon** -- provides a RESTful HTTP API (OpenAPI v0.0.45) for interacting with Slurm. Supports JSON and YAML serialization. |
| **sackd** | `src/sackd/` | **Auth cache daemon** -- caches authentication credentials to reduce authentication overhead. |
| **slurmstepd** | `src/slurmd/slurmstepd/` | **Job step daemon** -- launched per-job-step on compute nodes, manages I/O, cgroups, and signal delivery for job steps. |
| **stepmgr** | `src/stepmgr/` | **Step manager** -- manages job step lifecycle (launch, I/O forwarding, GRES tracking). Used by srun for direct step management. |

### User Command Entry Points (`src/`)

| Command | Directory | Purpose |
|---|---|---|
| `sbatch` | `src/sbatch/` | Submit a batch job script for later execution |
| `srun` | `src/srun/` | Submit and launch a job step (interactive or within a job allocation) |
| `salloc` | `src/salloc/` | Allocate resources for an interactive job session |
| `scancel` | `src/scancel/` | Cancel a pending or running job/job step |
| `squeue` | `src/squeue/` | Report job state and queue information |
| `sinfo` | `src/sinfo/` | Report node and partition state information |
| `scontrol` | `src/scontrol/` | Administrative control interface (job/node/partition/reservation management) |
| `sacct` | `src/sacct/` | Display accounting data for completed jobs |
| `sacctmgr` | `src/sacctmgr/` | Manage accounting database (accounts, users, QOS, associations) |
| `sreport` | `src/sreport/` | Generate resource utilization reports from accounting data |
| `sdiag` | `src/sdiag/` | Display scheduler diagnostic information |
| `sshare` | `src/sshare/` | Report fair-share information |
| `sprio` | `src/sprio/` | Display job priority components |
| `sstat` | `src/sstat/` | Display live job step statistics |
| `sattach` | `src/sattach/` | Attach standard I/O to a running job step |
| `strigger` | `src/strigger/` | Set event triggers (for email notifications, etc.) |
| `sview` | `src/sview/` | Graphical view of cluster state |
| `sbcast` | `src/sbcast/` | Broadcast files to allocated nodes |
| `scrontab` | `src/scrontab/` | Manage crontab entries for Slurm jobs |
| `scrun` | `src/scrun/` | OCI-compliant runtime integration (container support) |

### Plugin Architecture

Slurm uses a **loadable plugin system** for nearly all subsystems. This is the core architectural pattern. Plugins are shared objects (`.so` files) loaded at runtime. There are approximately **40 plugin types**, each with multiple implementations.

Plugin types are defined as interfaces in `src/interfaces/` (e.g., `sched_plugin.h`, `select.h`, `auth.h`). Implementations live in `src/plugins/<type>/<implementation>/`.

**Key plugin categories and their implementations:**

| Plugin Type | Interface Header | Implementations |
|---|---|---|
| **sched** (scheduler) | `sched_plugin.h` | `backfill` (~5k LOC), `builtin` |
| **select** (resource selection) | `select.h` | `cons_tres` (consumable TRES, ~11.5k LOC), `linear` (whole-node) |
| **auth** (authentication) | `auth.h` | `munge`, `jwt`, `slurm`, `none` |
| **cred** (credential) | `cred.h` | (MUNGE-based, JWT-based) |
| **topology** | `topology.h` | `block`, `flat`, `ring`, `tree`, `torus3d` |
| **preempt** | `preempt.h` | `partition_prio`, `qos` |
| **priority** | `priority.h` | `basic`, `multifactor` |
| **gres** (generic resources) | `gres.h` | `gpu`, `mps`, `nic`, `shard` |
| **gpu** (GPU management) | `gpu.h` | `nvml`, `rsmi`, `oneapi`, `nrt`, `generic` |
| **accounting_storage** | `accounting_storage.h` | `mysql`, `slurmdbd` |
| **accounting_gather** | `accounting_gather.h` | `energy` variants (gpu, ipmi, rapl, etc.) |
| **job_submit** | `job_submit.h` | `lua` (user-defined submit filters) |
| **jobcomp** (job completion) | `jobcomp.h` | `filetxt`, `elasticsearch`, `kafka`, `lua`, `mysql`, `script` |
| **mpi** | `mpi.h` | `pmi2`, `pmix`, `cray_shasta` |
| **task** (task launch) | `task.h` | `affinity`, `cgroup` |
| **cgroup** | `cgroup.h` | (cgroup v1/v2 resource constraint management) |
| **switch** (network) | `switch.h` | (HPE Slingshot, InfiniBand) |
| **data_parser** | `data_parser.h` | REST API data serialization (v0.0.42 through v0.0.45) |

### Source Code Packages (`src/`)

| Package | Purpose |
|---|---|
| `src/common/` | Shared library code -- data structures (`job_record.h`, `bitstring.h`, `list.h`), protocol definitions (`slurm_protocol_defs.h`), utilities (`xmalloc.c`, `xstring.c`, `xhash.c`, `timers.c`) |
| `src/api/` | Public C API for Slurm (libslurm) -- exposes functions like `slurm_submit_batch_job()`, `slurm_load_jobs()`, `slurm_load_nodes()`, etc. |
| `src/interfaces/` | Plugin interface definitions (one `.h`/`.c` pair per plugin type) |
| `src/plugins/` | All plugin implementations organized by type |
| `src/database/` | MySQL common database code shared between plugins |
| `src/conmgr/` | Connection manager -- event-driven I/O multiplexer (epoll/poll-based). Handles RPC dispatch, connection lifecycle, TLS, and worker threads. This is the low-level networking layer. |
| `src/lua/` | Lua scripting integration for job_submit, jobcomp, CLI filter plugins |
| `src/curl/` | cURL integration for HTTP-based data transfers |

## 3. Main Entry Points and Core Abstractions

### Core Data Structures

All defined in `src/common/` headers:

**`job_record_t`** (`src/common/job_record.h`, line 256, ~325 fields) -- The central data structure for representing a job in the system. A very large C struct containing:
- Job identity and metadata (job_id, user_id, group_id, account, partition, name, array info)
- Resource specification (node_bitmap, cpu_cnt, gres_list_req, tres_req_cnt, licenses, network)
- State tracking (job_state, state_reason, start_time, end_time, suspend_time, time_limit)
- Priority and scheduling (priority, prio_factors, qos_ptr, last_sched_eval)
- Preemption details (preempt_time, preempt_in_progress, licenses_to_preempt)
- Accounting fields (assoc_ptr, db_index, billable_tres, tres_alloc_str)
- Execution context (alloc_node, batch_host, step_list, job_resrcs, switch_jobinfo)

**`job_resources_t`** (`src/common/job_resources.h`) -- Details of allocated resources (cores, memory, GPUs per node).

**`node_record_t`** -- Represents a compute node (state, features, CPU/memory/disk capacity, energy data).

**`part_record_t`** -- Represents a partition (logical grouping of nodes with scheduling policies, limits, priority).

**`step_record_t`** -- Represents a job step (within a job allocation, has its own resource assignment and state).

### Daemon Architecture

#### slurmctld (Central Controller) -- `src/slurmctld/`

The slurmctld is a multi-threaded C daemon with these major components (source files in `src/slurmctld/`):

| Source File | Lines | Purpose |
|---|---|---|
| `controller.c` | 4,421 | Main controller loop, initialization, signal handling, reconfiguration |
| `job_mgr.c` | 19,759 | **Job lifecycle management** -- job submission, state transitions, suspend/resume, requeue, cancel, batch processing |
| `job_scheduler.c` | 5,785 | **Main scheduling loop** -- iterates pending jobs, interacts with the sched plugin to select jobs for initiation, handles backfill coordination |
| `node_mgr.c` | 5,383 | Node state management -- state transitions (UP, DOWN, DRAIN, FAIL, etc.), node registration |
| `node_scheduler.c` | 4,680 | Node selection within the scheduler -- chooses specific nodes for job allocation |
| `proc_req.c` | 7,517 | RPC request processing -- dispatches incoming RPCs from clients and slurmd nodes |
| `reservation.c` | 8,956 | Advanced reservation management |
| `partition_mgr.c` | 2,250 | Partition lifecycle management |
| `fed_mgr.c` | 6,030 | Federation management -- coordinates across multiple Slurm clusters |
| `acct_policy.c` | 5,654 | Accounting policy enforcement -- association and QOS limit checking |
| `power_save.c` | 1,795 | Power saving / idle node management (cloud bursting) |
| `licenses.c` | 2,903 | License management |
| `gang.c` | 1,427 | Gang scheduling support |
| `agent.c` | 2,783 | Asynchronous RPC agent for communication with slurmd nodes |
| `state_save.c` | 331 | State checkpointing to disk (periodic and on shutdown) |
| `backup.c` | 699 | Backup controller (hot standby) |
| `statistics.c` | 968 | Performance statistics tracking |
| `slurmctld.h` | 2,932 | Main header with global state declarations |

The scheduling flow works as:
1. `job_scheduler.c`'s main loop calls the **sched plugin** (either `backfill` or `builtin`)
2. The backfill scheduler (`src/plugins/sched/backfill/backfill.c`, ~5k LOC) implements:
   - **Conservative backfilling**: evaluates whether starting a lower-priority job would delay any higher-priority job. If not, it temporarily boosts the lower-priority job's effective priority.
   - Uses the **oracle** (`backfill/oracle.c`) for estimating job end times and resource availability.
   - Calls into `node_scheduler.c` for node selection and `select/cons_tres` plugin for resource allocation feasibility checking (`job_test()`).
3. The select plugin (`select/cons_tres` for modern deployments, or `select/linear`) handles the actual resource-to-job matching.

#### slurmd (Node Daemon) -- `src/slurmd/`

The node agent that runs on every compute node:
- `slurmd.c` -- main daemon loop, registration with controller, RPC handling
- `req.c` -- request processing (launch jobs, prolog/epilog, signal delivery)
- `job_mem_limit.c` -- per-job memory limit enforcement
- `launch_state.c` -- tracks launched job state on the node
- `common/slurmd_common.c` -- shared utilities
- `common/slurmstepd_init.c` -- initializes the slurmstepd environment
- `slurmstepd/slurmstepd_*.c` -- the per-step daemon that actually launches and monitors processes

#### slurmdbd (Accounting Database) -- `src/slurmdbd/`

- `slurmdbd.c` -- main daemon, connection management, protocol handling
- `proc_req.c` -- RPC processing for accounting queries (jobs, associations, accounts, QOS, reservations)
- `backup.c` -- backup/failover support
- Uses MySQL via the `accounting_storage/mysql` plugin for persistence.

#### slurmrestd (REST API) -- `src/slurmrestd/`

- `slurmrestd.c` -- HTTP daemon (supports both inetd and standalone modes)
- `http.c` -- HTTP request/response handling
- `openapi.c` -- OpenAPI specification handling and request routing
- `operations.c` -- maps REST operations to Slurm API calls
- `plugins/openapi/` -- OpenAPI version-specific plugins (data serialization)
- `plugins/auth/` -- authentication plugins for REST API

### Core Algorithms

**Job Priority Calculation:**
The `priority/multifactor` plugin calculates job priority as a weighted sum of multiple factors:
- Age (time in queue)
- Fair-share (based on historical resource usage vs. configured shares)
- Job size (requested resources)
- Partition priority offset
- QOS priority
- Site factor (admin-defined)

**Backfill Scheduling:**
The backfill scheduler (`src/plugins/sched/backfill/backfill.c`) is a conservative backfilling algorithm. Its core insight: if starting a lower-priority job on currently-idle resources would not delay the expected start time of any higher-priority job, start it now. This maximizes utilization without violating priority ordering.

**Resource Selection (`select/cons_tres`):**
The CONsumable TRES (Trackable RESources) plugin (`src/plugins/select/cons_tres/`) manages resource allocation at fine granularity -- individual CPUs, memory bytes, GPUs, and other resources. It tracks resource usage per-node and tests whether jobs fit on available resources via `job_test()`.

## 4. External Dependencies and Frameworks

### Required Dependencies

| Dependency | Purpose |
|---|---|
| Linux kernel | Slurm is tested only under Linux. Uses cgroups, ptrace, epoll, procfs, sched_setaffinity |
| GCC / Clang | C99-compatible compiler |
| **MUNGE** | Authentication -- default credential/payload authentication service (weak dependency as of 26.05) |
| pthreads | Multi-threading across all daemons |
| GNU Make / Autotools | Build system (autoconf, automake, libtool) |
| OpenSSL | TLS support (library linking, optional via `--with-s2n`) |

### Optional Dependencies

| Dependency | Configure Flag | Purpose |
|---|---|---|
| MySQL / MariaDB | `--with-mysql` | Accounting database backend |
| **hwloc** | `--with-hwloc` | Hardware topology discovery (CPU, NUMA, cache hierarchy) |
| **Lua** | `--with-lua` | Scriptable job submission filters, job completion logging, CLI filters |
| **libcurl** | `--with-libcurl` | HTTP transfers (burst buffer, elasticsearch job completion) |
| **libjwt** / libjansson | `--with-jwt` / `--with-json` | JWT authentication and JSON support |
| **libyaml** | `--with-yaml` | YAML serialization (slurmrestd) |
| **PMIx** | `--with-pmix` | Parallel job launch (alternative to PMI2) |
| **UCX** | `--with-ucx` | High-performance communication for job launch |
| **NVML** (NVIDIA) | `--with-nvml` | GPU management (NVIDIA GPUs) |
| **RSMI** (AMD) | `--with-rsmi` | GPU management (AMD GPUs) |
| **oneAPI Level Zero** | `--with-oneapi` | GPU management (Intel GPUs) |
| **FreeIPMI** | `--with-freeipmi` | Out-of-band power monitoring |
| **LZ4** | `--with-lz4` | Compression for checkpoint files |
| **RDMCA** (InfiniBand) | `--with-ofed` | InfiniBand/OFED support |
| **HPE Slingshot** | `--with-hpe-slingshot` | HPE Slingshot interconnect |
| **PAM** | `--with-pam` | Pluggable Authentication Modules (PAM Slurm Adopt) |
| **systemd** | `--with-systemd` | systemd service integration |
| **readline** | `--with-readline` | Interactive command-line editing (sacctmgr) |
| **sview** (GTK) | `--with-sview` | GUI for cluster monitoring |
| **X11** | `--with-x11` | X11 forwarding for interactive jobs |
| **cgroup** | `--with-cgroup` | Linux cgroups v1/v2 resource containment |
| **HDF5** | `--with-hdf5` | HDF5 profiler output (acct_gather_profile) |
| **librdkafka** | `--with-rdkafka` | Kafka job completion logging |
| **s2n** | `--with-s2n` | TLS implementation (alternative to OpenSSL) |
| **man2html** | | HTML documentation generation |
| **Check** (unit test) | | C unit test framework (optional, `check >= 0.9.8`) |

### Test Frameworks

- **Check** (`>= 0.9.8`) -- C unit testing framework for slurm_unit tests
- **Expect** -- Tcl-based test framework for integration tests
- **Pytest** -- Python test framework (modern tests in `testsuite/python/`)

## 5. Current Repository State

### Active Branches

- **`master`** -- Primary development branch (all new features and fixes land here)
- **`slurm-26.05`** -- Current pre-release maintenance track (26.05.x series)
- **`slurm-25.11`** -- Previous stable release maintenance (latest: 25.11.6-1)
- **`slurm-25.05`** -- Older stable maintenance (latest: 25.05.8-1)
- Release branches back to `slurm-1.0` (all historical versions are preserved as branches)

### Versioning

- **Current version**: 26.11.0-0rc1 (from `META` file)
- Release candidate for Slurm 26.11.x series
- The version scheme is `YY.MM.MICRO` (e.g., 26.05 = May 2026 feature release)
- The 26.05.0 release is the current stable release series
- 26.11 will be the next stable major release (November 2026 release)

### Recent Commits (top of master as of 2026-05-18)

The repository shows ~3,326 commits in 2026 so far (Jan 1 - May 18, 2026). Recent work includes:
- Torus3D topology data parser improvements and fixes
- JWT HTTP auth plugin removal
- License-related HRes fixes
- Backfill scheduler improvements
- Documentation updates for topology parsers
- Regular cherry-pick merges from master to `slurm-26.05`

### Build System

Slurm uses the **GNU Autotools** build system (autoconf, automake, libtool):

1. `configure.ac` -- Main autoconf configuration file (checks for compilers, libraries, headers, optional packages)
2. `auxdir/*.m4` -- Custom autoconf macros for feature detection (JSON, JWT, Lua, MUNGE, hwloc, NVML, etc.)
3. `Makefile.am` files -- Automake input files (one per directory)
4. `configure` -- Generated configure script (~1 MB)
5. `config.h.in` -- Template for generated `config.h`

Build process:
```bash
./configure --prefix=/usr [options...]
make
make install
```

RPM packaging: `slurm.spec` produces separately-packaged sub-RPMs:
- `slurm` (core daemons)
- `slurm-slurmctld` (controller daemon)
- `slurm-slurmd` (node daemon)
- `slurm-slurmdbd` (accounting daemon)
- `slurm-slurmrestd` (REST API daemon)
- `slurm-sackd` (auth cache daemon)
- `slurm-client` (user commands)
- `slurm-devel` (development headers/libraries)
- `slurm-libpmi*` (PMI/PMI2 libraries)
- `slurm-libnss-slurm` (NSS module)
- `slurm-libpam-slurm-adopt` (PAM module)
- `slurm-openlava` (OpenLava compatibility)
- `slurm-torque` (Torque/PBS compatibility)
- `slurm-perlapi` (Perl API bindings)
- `slurm-sview` (GUI)
- `slurm-contribs` (contributed tools)

Debian: Full Debian packaging in `debian/` directory produces similar split packages.

### Testing

The test suite lives in `testsuite/`:

| Test Directory | Framework | Purpose |
|---|---|---|
| `testsuite/python/` | Pytest | Modern integration tests (the primary test framework for new tests) |
| `testsuite/expect/` | Expect (Tcl) | Legacy integration tests |
| `testsuite/slurm_unit/` | Check (C) | Unit tests for core library functions |
| `testsuite/src/` | Custom C | Additional test helpers and utilities |

Tests are run via `testsuite/run-tests` with a configuration file.

### Changelogs

Per-release changelogs in `CHANGELOG/slurm-XX.YY.md` covering releases back to `slurm-22.05`. The 26.05.0rc1 changelog shows a diverse set of changes including:
- API additions (new REST endpoints: healthz, readyz, livez)
- Bug fixes (use-after-free in cons_tres, segfaults in connection handling)
- Performance improvements (threadpool for slurmctld, readlock optimizations)
- Feature removals (job state cache deprecated)
- GPU/NVML fixes
- Packaging improvements (MUNGE as weak dependency)

### Codebase Statistics

Key observations about the codebase:
- slurmctld alone is ~85k lines of C across 25+ source files
- The job_mgr.c file is ~19,759 lines (the single largest source file)
- The backfill scheduler plugin is ~5,213 lines
- The cons_tres select plugin is ~11,519 lines across multiple files
- The connection manager (`src/conmgr/`) provides a custom I/O multiplexing framework (epoll/poll)
- Plugin interfaces are thin wrappers (each `<type>_plugin.h` is typically ~200-400 lines)
- The codebase predates modern C standards and uses C99 with some GNU extensions
- Threading model: pthreads with a custom threadpool (recently improved in 26.05)

### Project Governance

- Maintained by **SchedMD LLC** (<https://schedmd.com>)
- Issue tracker: <https://support.schedmd.com/> (not GitHub Issues)
- Contributions welcome via the SchedMD support portal
- Original authors: Morris Jette (LLNL) et al.
- Regular release cadence: two major releases per year (April/May and October/November)
- The project has been under continuous development since the early 2000s
