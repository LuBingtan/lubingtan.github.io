# DevOps 理念与实践

## CI/CD Pipeline

### Pipeline as Code

Pipeline 的定义应该与项目代码放在一起，这样能确保 pipeline 在特定项目中正常工作，且 pipeline 本身的变更也能被充分测试。

**正面案例：GitHub Actions**
- 由 PR 事件触发的 workflow 定义在 git 仓库中，与其他代码一起管理
- 当 PR 包含对 workflow 的修改时，该 PR 会使用修改后的 workflow 运行
- 同时，其他 PR 仍然使用 master 分支中定义的 workflow

**反例：Prow**
- 所有 presubmit/postsubmit 任务预定义在集中式仓库中，无法仅针对某个 PR 进行修改
- Pipeline 的变更与项目代码分离，测试和迭代困难

### 可复用 Pipeline

一个 workflow 应包含以下基本组件：
1. 触发 workflow 的事件（event）
2. 在 runner 上执行的 job，包含一系列 step
3. 每个 step 可以运行脚本，或调用一个可复用的 **action**

可复用的关键在于**构建块（building block）**设计：
- Step 是基本构建块：Action 包含多个 Step，Step 可以调用 Action
- Job 也是构建块：Workflow 包含多个 Job，Job 可以调用 Workflow

**反例：Tekton Pipeline**
- Pipeline 包含多个 Task，Task 包含多个 Step
- Pipeline 不能调用另一个 Pipeline，Task 不能调用另一个 Task，Step 不能调用另一个 Step
- 没有构建块机制，导致复用代码时必须复制粘贴

### 性能指标

CI/CD 系统的基本性能可以用效率来衡量：

**Efficiency = User Time / (User Time + System Time)**

- **User Time**：从实际执行到用户定义任务完成的时间
- **System Time**：用户不关心的系统开销（如 event 处理、资源创建/更新、Pod 调度、参数传递等）

此外，应监控和优化用户定义任务本身的性能，例如启用 Go、Maven、Docker 等构建缓存。

### 可靠性指标

**Pipeline Reliability = (成功运行次数 - 由用户任务导致的失败次数) / 总运行次数**

由用户任务导致的失败不计入 CI/CD 系统的故障统计，因为这并非 CI/CD 系统的责任。

## 开发环境

### 可复现环境

搭建开发环境是一个重要障碍。由于文档不完整或开发者理解差异，最终环境可能差异很大。远程开发环境虽有优势，但网络延迟、上传/下载时间、公司安全合规限制等因素使其无法完全替代本地环境。

### Docker as a Service

为什么需要 Docker as a Service 而非本地构建镜像？

- 在笔记本上安装和维护 Docker 并不简单（尤其是 macOS/Windows）
- 本地网络环境可能与数据中心不同，Dockerfile 可能需要访问内网资源
- 构建可能需要大量 CPU、内存或磁盘，本地笔记本可能无法满足

### Kubernetes as a Service

每个开发者可能需要独立的 Kubernetes 环境，因为他们之间需要互相独立。通过 Kubernetes as a Service，开发者可以直接将镜像部署到 Kubernetes 上。

## 参考

- [GitHub Actions Workflow 基础](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows#workflow-basics)
