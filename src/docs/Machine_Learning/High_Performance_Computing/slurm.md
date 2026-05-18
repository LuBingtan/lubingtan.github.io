# Slurm: HPC 集群工作负载管理器

## What is Slurm

[Slurm](https://slurm.schedmd.com/)（Simple Linux Utility for Resource Management）是一个开源的集群资源管理和作业调度系统，是全球顶级超算和 HPC 集群的首选工作负载管理器。

Slurm 常与 [Open MPI](../High_Performance_Computing/ompi架构介绍.md) 搭配使用于 HPC 场景，负责资源分配和作业调度。

Slurm 提供三个核心功能：
1. **资源分配** — 为用户分配计算节点的独占/非独占访问权限（按时间段）
2. **作业框架** — 提供在已分配节点上启动、执行和监控作业（通常是并行作业）的完整框架
3. **队列仲裁** — 通过管理待处理作业队列来仲裁资源冲突

项目起源于 Lawrence Livermore National Laboratory (LLNL)，现由 SchedMD LLC 维护。仅在 Linux 下测试运行。语言为 C（附带 Perl、Lua、Python 用于扩展/测试），采用 GPLv2+ 许可证。

## 架构

### 核心 Daemon

Slurm 采用多 daemon 分布式架构：

| Daemon | 功能 |
|---|---|
| **slurmctld** | 中央控制器——Slurm 的大脑。管理作业、节点、分区、预留和调度决策。每个集群一个（含热备），代码量约 85k 行 C |
| **slurmd** | 节点 daemon——运行在每个计算节点上。执行和监控作业，管理 prolog/epilog，本地资源管控 |
| **slurmdbd** | 数据库 daemon——将计费和作业历史数据存入 MySQL，作为集中式计费层 |
| **slurmrestd** | REST API daemon——提供 RESTful HTTP API（OpenAPI），支持 JSON/YAML 序列化 |
| **slurmstepd** | 作业步 daemon——每个作业步在计算节点上启动，管理 I/O、cgroup 和信号传递 |
| **sackd** | 认证缓存 daemon——缓存认证凭证以减少认证开销 |

### 常用用户命令

| 命令 | 功能 |
|---|---|
| `sbatch` | 提交批处理作业脚本 |
| `srun` | 提交并启动作业步（交互式或在分配内） |
| `salloc` | 为交互式会话分配资源 |
| `scancel` | 取消作业或作业步 |
| `squeue` | 查看作业队列状态 |
| `sinfo` | 查看节点和分区状态 |
| `scontrol` | 管理控制接口（作业/节点/分区/预留管理） |
| `sacct` | 查看已完成作业的计费数据 |
| `sacctmgr` | 管理计费数据库（账户、用户、QOS） |

### 插件架构

Slurm 的核心架构模式是**可加载插件系统**。约 40 种插件类型，每种有多个实现。插件接口定义在 `src/interfaces/`，实现位于 `src/plugins/<type>/<implementation>/`。

关键插件类别：

| 插件类型 | 功能 | 主要实现 |
|---|---|---|
| **sched** (调度器) | 作业调度算法 | `backfill`（保守回填，约 5k LOC）、`builtin` |
| **select** (资源选择) | 资源到作业的匹配 | `cons_tres`（可消耗 TRES，约 11.5k LOC）、`linear`（整节点） |
| **priority** (优先级) | 作业优先级计算 | `multifactor`（多因子加权）、`basic` |
| **auth** (认证) | 认证机制 | `munge`、`jwt` |
| **gres** (通用资源) | 通用资源管理 | `gpu`、`mps`、`nic`、`shard` |
| **topology** (拓扑) | 网络拓扑感知 | `block`、`flat`、`ring`、`tree`、`torus3d` |
| **mpi** (MPI 启动) | 并行作业启动 | `pmi2`、`pmix`、`cray_shasta` |
| **accounting_storage** (计费) | 计费数据持久化 | `mysql`、`slurmdbd` |
| **jobcomp** (作业完成) | 作业完成日志 | `filetxt`、`elasticsearch`、`kafka`、`lua`、`mysql` |

## 核心调度算法

### 多因子优先级

`priority/multifactor` 插件将作业优先级计算为多个因子的加权和：
- **Age**（排队时间）
- **Fair-share**（基于历史资源使用 vs 配置份额）
- **Job size**（请求的资源量）
- **Partition** 优先级偏移
- **QOS** 优先级
- **Site factor**（管理员自定义）

### 保守回填 (Backfill)

回填调度器 (`sched/backfill`) 实现保守回填算法。核心思想：如果启动低优先级作业不会延迟任何高优先级作业的预计开始时间，则立即启动它。这在不违反优先级顺序的前提下最大化集群利用率。

调度流程：
1. `job_scheduler.c` 主循环调用 sched 插件
2. 回填调度器通过 **oracle** 估算作业结束时间和资源可用性
3. 调用 `node_scheduler.c` 和 `select/cons_tres` 检查资源分配可行性 (`job_test()`)
4. 为不会阻塞高优先级作业的低优先级作业临时提升有效优先级

### CONsumable TRES (cons_tres)

`select/cons_tres` 插件以细粒度管理资源分配——精确到单个 CPU、内存字节、GPU 等。每节点跟踪资源使用情况，通过 `job_test()` 判断作业是否适合可用资源。

## 关键依赖

| 依赖 | 用途 |
|---|---|
| **MUNGE** | 认证凭据服务 |
| **MySQL/MariaDB** | 计费数据库后端 |
| **hwloc** | 硬件拓扑发现（CPU、NUMA、缓存层级） |
| **Lua** | 可脚本化的作业提交过滤器 |
| **PMIx / UCX** | 并行作业启动和高性能通信 |
| **NVML / RSMI / oneAPI** | GPU 管理（NVIDIA / AMD / Intel） |
| **libjwt** | JWT 认证 |
| **cgroup** | 资源容器（cgroup v1/v2） |

## 项目状态

- **当前版本**: 26.11.0-0rc1（预发布）
- **发布模式**: YY.MM 版本方案，每年两次大版本（4-5 月和 10-11 月）
- **构建系统**: GNU Autotools，RPM/DEB 分包（约 20 个子包）
- **测试框架**: Pytest（集成测试）、Expect（遗留集成测试）、Check（C 单元测试）
- **代码量**: slurmctld 约 85k 行，单文件最大约 19.8k 行，总计约 3,300+ 次提交（2026 年）

## 参考

- [Slurm 官方文档](https://slurm.schedmd.com/)
- [Slurm GitHub](https://github.com/SchedMD/slurm)
