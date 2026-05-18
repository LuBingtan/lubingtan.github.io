# Wiki Index

## Cloud Native

### Kubernetes

- [Kubernetes 概念](./Cloud_Native/Kubernetes/1_kubernetes概念.md) — Kubernetes 是什么、为什么需要它，以及容器部署的发展历史
- [K8s 工作负载](./Cloud_Native/Kubernetes/1-1_k8s工作负载.md) — Pod 的概念、原理及工作负载资源类型
- [Kubernetes API Server](./Cloud_Native/Kubernetes/2_kubernetes-api-server.md) — kube-apiserver 的证书认证、SSL/TLS 与架构分析
- [kube-scheduler 源码分析](./Cloud_Native/Kubernetes/4_kube-scheduler源码分析.md) — scheduler 的工作流程、配置初始化与调度算法源码解读
- [client-go list & watch 原理](./Cloud_Native/Kubernetes/5_client-go%20list%20&%20watch%20原理.md) — client-go 中 List-Watch 机制的实现原理
- [Service 相关](./Cloud_Native/Kubernetes/6_service相关.md) — Kubernetes Service 的概念、类型及其实现原理
- [CNI 详解](./Cloud_Native/Kubernetes/cni详解.md) — 容器网络接口的实现：IP 分配、network namespace、veth pair、bridge
- [FlowSchema](./Cloud_Native/Kubernetes/flowschema.md) — kube-apiserver 的流量控制与 API 优先级机制
- [PLEG](./Cloud_Native/Kubernetes/k8s之pleg.md) — Pod Lifecycle Event Generator 的原理与僵尸进程排查
- [Kubelet 原理](./Cloud_Native/Kubernetes/kubelet原理.md) — kubelet 创建 Pod 的完整流程：syncLoop、PLEG、容器运行时
- [Kubernetes 高可用](./Cloud_Native/Kubernetes/kubernetes_ha.md) — stacked etcd 与 external etcd 两种 HA 拓扑方案
- [RBAC](./Cloud_Native/Kubernetes/rbac.md) — 基于角色的访问控制：用户创建、证书签名请求、权限绑定
- [Kueue](./Cloud_Native/Kubernetes/kueue.md) — Kubernetes 原生作业队列管理器：配额管理、公平共享、抢占与多集群调度

### CICD

- [DevOps 理念与实践](./Cloud_Native/CICD/devops-thinking.md) — CI/CD pipeline 设计原则：Pipeline as Code、可复用性、性能与可靠性指标、开发环境可复现

### Linux Container

- [容器知识备忘录](./Cloud_Native/Linux_Container/容器知识备忘录.md) — Linux Namespace、Cgroups、UnionFS 等容器核心技术总结

## Machine Learning

### High Performance Computing

- [ompi架构介绍](./Machine_Learning/High_Performance_Computing/ompi架构介绍.md) — Open MPI 架构介绍
- [Slurm](./Machine_Learning/High_Performance_Computing/slurm.md) — HPC 集群工作负载管理器：资源分配、作业调度、回填算法与插件架构

### Inference

- [Model Mesh Serving](./Machine_Learning/Inference/Model%20Mesh%20Serving:%20一种可以大规模部署ML模型的解决方案.md) — 大规模 ML 模型部署方案：ModelMesh 的原理与架构
- [vLLM Production Stack 实战](./Machine_Learning/Inference/vLLM%20Production%20Stack实战.md) — vLLM 生产环境搭建实战：硬件准备、LWS 部署、benchmark

## Operation

### Development Environment

- [Docker 环境配置](./Operation/Development_Environment/Docker环境配置.md) — Docker 在 Ubuntu/WSL 中的安装与镜像加速配置
- [Windows 开发环境配置](./Operation/Development_Environment/WIndows开发环境配置.md) — WSL 安装、版本切换与 Windows 开发环境搭建

### Linux

- [Bash 及命令行工具技巧集合](./Operation/Linux/Bash以及命令行工具技巧集合.md) — 网络诊断、磁盘管理、Bash 脚本等实用命令行技巧
