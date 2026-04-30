# vLLM Production Stack 实战



## 本地测试环境

### 准备硬件环境

- 显卡：RTX 5060 (8GB)
- 内存：32GB
- 系统：win11

### 准备软件环境

#### Setup CUDA on WSL2

[CUDA on WSL User Guide — CUDA on WSL 13.1 documentation](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

#### Install nvidia docker in WSL2

[Installing the NVIDIA Container Toolkit — NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

> [!NOTE]
>
> 当前vLLm版本(v0.13.0), 默认cuda 版本是12.9.1, 当然本地的cuda版本不一定要12.9.1, 但是driver版本必须要大于`575.57.08`(reference: <https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html#cuda-driver>)
>
> win11上推荐使用这种方式升级: Use [nvidia-app](https://www.nvidia.cn/software/nvidia-app/) to upgrade nvidia-driver in windows and then restart WSL


在WSL中查看GPU状态:
```sh
% nvidia-smi

Tue Jan 20 13:35:34 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.152                Driver Version: 573.24         CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5060 ...    On  |   00000000:01:00.0 Off |                  N/A |
| N/A   47C    P8              4W /   95W |       0MiB /   8151MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
```

#### 环境测试验证

##### Docker镜像验证

###### Step-1 获取hugging face token

Check out [User access tokens](https://huggingface.co/docs/hub/security-tokens#what-are-user-access-tokens)
```sh
export HF_TOKEN=<your token>
```

###### Step-2 使用官方Docker镜像启动容器

```bash
docker run -it --rm --runtime nvidia --gpus all \
      -v ~/.cache/huggingface:/root/.cache/huggingface \
      --env "HF_TOKEN=$HF_TOKEN" \
      -p 8000:8000 \
      --ipc=host \
      --entrypoint=bash \
      vllm/vllm-openai:v0.13.0
# Why we need this: https://github.com/vllm-project/vllm/issues/30392
mkdir -p /usr/lib64 && \
    ln -s /usr/local/cuda/targets/x86_64-linux/lib/stubs/libcuda.so /usr/lib64/libcuda.so
# We must use a pre-defined template for some kinds of models
cat <<EOF > /tmp/template.jinja
{%- set counter = namespace(index=0) -%}
{%- for message in messages -%}
    {%- if message['role'] == 'user' -%}
        {{- '[Round ' + counter.index|string + ']\n问：' + message['content'] -}}
        {%- set counter.index = counter.index + 1 -%}
    {%- endif -%}
    {%- if message['role'] == 'assistant' -%}
        {{- '\n答：' + message['content'] -}}
        {%- if (loop.last and add_generation_prompt) or not loop.last -%}
            {{- '\n' -}}
        {%- endif -%}
    {%- endif -%}
{%- endfor -%}


{%- if add_generation_prompt and messages[-1]['role'] != 'assistant' -%}
    {{- '\n答：' -}}
{%- endif -%}
EOF
# Run vllm serve
vllm serve --model facebook/opt-125m  --gpu-memory-utilization=0.8 --max-model-len=128 --chat-template=/tmp/template.jinja
```

##### 启动kind cluster

```bash
git clone https://github.com/vllm-project/production-stack.git
bash utils/install-kind-cluster.sh
```

查看GPU Node是否可以enable
```sh
kubectl describe nodes | grep -i gpu

# Expected output:
nvidia.com/gpu: 1
... (plus many lines related to gpu information)
```

> [!NOTE]
> 
> 这里失败了, 下面是 debug

`kubectl -n gpu-operator logs gpu-operator-1769492979-node-feature-discovery-worker-zgtbp` output:

```
E0127 05:55:18.244715       1 system.go:111] "failed to get DMI entry" err="open /host-sys/devices/virtual/dmi/id/sys_vendor: no such file or directory" attributeName="sys_vendor"
```

`kubectl get nodes -oyaml |grep feature.node.kubernetes.io` 和gpu相关的好像只有这个
```
feature.node.kubernetes.io/pci-1414.present: "true"
```

尝试nvkind https://github.com/NVIDIA/nvkind + nvidia k8s device plugin依然不行

next step: 需要查看 NFD https://github.com/kubernetes-sigs/node-feature-discovery

看了NFD实现, 应该还是driver的问题, 升级driver之后, wsl2 内部似乎无法识别gpu

```sh
$ lspci -nn
01e5:00:00.0 3D controller [0302]: Microsoft Corporation Basic Render Driver [1414:008e]
1cd3:00:00.0 3D controller [0302]: Microsoft Corporation Basic Render Driver [1414:008e]
5582:00:00.0 SCSI storage controller [0100]: Red Hat, Inc. Virtio 1.0 console [1af4:1043] (rev 01)
7580:00:00.0 System peripheral [0880]: Red Hat, Inc. Virtio file system [1af4:105a] (rev 01)
```

可以看到没有 nvidia 设备, 而是 `Microsoft Corporation Basic Render Driver` . 尝试了新启动一个wsl2以及wsl --update升级kernel, 依然不行

###### 问题根因

WSL2 并非通过传统的 PCI 直通（PCI Passthrough）来访问 GPU，而是使用微软的 **GPU-PV（GPU 准虚拟化）** 机制。GPU 物理设备归 Windows 宿主机管理，WSL2 内部通过 `dxgkrnl` 内核驱动通道将 CUDA/NVML 调用转发给 Windows 的 NVIDIA 驱动执行。

架构示意：

```
┌─ WSL2 Linux ──────────────────────────────────────┐
│  nvidia-smi / CUDA App                             │
│       ↓                                            │
│  libcuda.so / libnvidia-ml.so                      │
│       ↓                                            │
│  dxgkrnl (Microsoft GPU-PV kernel driver)          │
│       ↓ (VMBus)                                    │
├─ Windows Host ─────────────────────────────────────┤
│  NVIDIA Driver → Physical GPU                      │
└────────────────────────────────────────────────────┘
```

这就是为什么 `nvidia-smi` 能正常显示 GPU 信息，但 `lspci` 看不到 NVIDIA 设备--`lspci` 枚举的是 Hyper-V 虚拟化出的虚拟 PCI 设备（`Microsoft Basic Render Driver [1414:008e]`），而真实的 NVIDIA GPU 从未作为 PCI 设备暴露给 WSL2。

> [!NOTE]
>
> 这不是 driver bug，无需回滚 driver。NFD 的 `pci` source 在 WSL2 中天然无法工作，需要换用其他方式检测 GPU。

###### 解决方案：NFD Custom Source

NFD 除了 `pci` source 之外，还支持 `custom` source 和 `local` source，可以通过自定义脚本检测 GPU，不依赖 `lspci`。

**Step 1: 确认 NVIDIA Device Plugin 正常工作**

虽然 NFD 检测不到 GPU，但 NVIDIA Device Plugin 不依赖 PCI 检测--它通过 `nvidia-smi` 和 `/dev/nvidia*` 设备节点工作：

```sh
kubectl describe nodes | grep nvidia.com/gpu
```

如果输出包含 `nvidia.com/gpu: 1`，说明 Device Plugin 已正确注册 GPU 资源，Kubernetes 调度器可以将 GPU 分配给 Pod。

> [!NOTE]
>
> 如果这里也没有 GPU 资源，检查 GPU Operator 的 device-plugin 容器日志：
> ```sh
> kubectl logs -n gpu-operator -l app=nvidia-device-plugin
> ```

**Step 2: 创建 NFD Custom Hook 脚本**

NFD 的 `local` source 会在 HostPath 目录下查找可执行的 hook 脚本，将其输出作为 node feature：

```sh
# 创建 hook 文件
cat <<'EOF' > /tmp/nvidia-gpu.sh
#!/bin/bash
# NFD custom hook: 通过 nvidia-smi 检测 GPU（不依赖 lspci）
if command -v nvidia-smi &> /dev/null && nvidia-smi -L &> /dev/null 2>&1; then
    echo "nvidia-gpu-present"
    GPU_COUNT=$(nvidia-smi -L 2>/dev/null | wc -l)
    echo "nvidia-gpu-count=${GPU_COUNT}"
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 | sed 's/ /-/g')
    echo "nvidia-gpu-model=${GPU_NAME}"
fi
EOF
chmod +x /tmp/nvidia-gpu.sh
```

> [!NOTE]
>
> 在生产环境中，NFD worker 以 DaemonSet 方式部署，hook 脚本需要通过 ConfigMap 挂载到 `/etc/kubernetes/node-feature-discovery/source.d/`。在 kind 开发环境中，如果 NFD 未正确加载 hook，可以退而使用下面的「快速方案」。

**Step 3: 创建 NodeFeatureRule**

将 hook 检测结果映射为 Kubernetes node label：

```yaml
# nvidia-gpu-feature-rule.yaml
apiVersion: nfd.k8s-sigs.io/v1alpha1
kind: NodeFeatureRule
metadata:
  name: nvidia-gpu-custom
spec:
  rules:
    - name: nvidia.gpu.present
      labels:
        feature.node.kubernetes.io/nvidia-gpu.present: "true"
      matchFeatures:
        - feature: local.nvidia-gpu
          matchExpressions:
            nvidia-gpu-present: { op: Exists }

    - name: nvidia.gpu.count
      labelsTemplate: |
        feature.node.kubernetes.io/nvidia-gpu.count={{ .count }}
      matchFeatures:
        - feature: local.nvidia-gpu
          matchExpressions:
            nvidia-gpu-count: { op: Exists }
      vars:
        - count

    - name: nvidia.gpu.model
      labelsTemplate: |
        feature.node.kubernetes.io/nvidia-gpu.model={{ .model }}
      matchFeatures:
        - feature: local.nvidia-gpu
          matchExpressions:
            nvidia-gpu-model: { op: Exists }
      vars:
        - model
```

```sh
kubectl apply -f nvidia-gpu-feature-rule.yaml
```

**Step 4: 验证**

```sh
kubectl get nodes -o yaml | grep feature.node.kubernetes.io/nvidia-gpu

# 预期输出:
#   feature.node.kubernetes.io/nvidia-gpu.present: "true"
#   feature.node.kubernetes.io/nvidia-gpu.count: "1"
#   feature.node.kubernetes.io/nvidia-gpu.model: "NVIDIA-GeForce-RTX-5060"
```

**快速方案（仅开发环境）**

如果只想快速跳过 NFD 问题继续后续部署，直接手动打 label：

```sh
kubectl label node <node-name> feature.node.kubernetes.io/nvidia-gpu.present=true
```

---

### 部署 vLLM

#### Step 1: 确认集群 GPU 资源

```sh
kubectl describe nodes | grep -A 5 "Capacity"
kubectl describe nodes | grep nvidia.com/gpu
```

#### Step 2: 准备模型缓存 PVC（可选，加速后续启动）

```sh
# 如果模型较大，可以创建 PVC 缓存模型文件
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: huggingface-cache
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
EOF
```

#### Step 3: 使用 Helm 部署 vLLM

```sh
cd production-stack

# 查看可用的 Helm Chart 和默认配置
ls helm/

# 部署 vLLM（具体参数参考仓库中的 values.yaml）
helm upgrade --install vllm ./helm \
  --set resources.limits.nvidia.com/gpu=1 \
  --set server.extraArgs={--gpu-memory-utilization=0.8,--max-model-len=128} \
  --wait
```

> [!NOTE]
>
> 如果 Helm Chart 路径不是 `helm`，请参考 `production-stack` 仓库的 README 确认正确的 Chart 路径。也可以通过 `helm search` 或直接查看部署脚本确认。

#### Step 4: 检查部署状态

```sh
kubectl get pods -l app.kubernetes.io/name=vllm
kubectl logs -f deployment/vllm
```

等待 Pod 进入 Running 状态。首次启动需要下载模型，取决于网络和模型大小，可能需要几分钟：

```sh
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=vllm --timeout=600s
```

查看 Pod 详情确认 GPU 分配：

```sh
kubectl describe pod -l app.kubernetes.io/name=vllm | grep -A 2 "Limits"
# 预期输出包含 nvidia.com/gpu: 1
```

---

### 测试推理服务

#### Step 1: Port Forward

```sh
kubectl port-forward svc/vllm 8000:8000
```

#### Step 2: 发送推理请求

**健康检查：**

```sh
curl -s http://localhost:8000/health
```

**Chat Completion：**

```sh
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "facebook/opt-125m",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "max_tokens": 64
  }' | jq .
```

预期看到正常的流式/非流式 chat completion 响应。

**Completion（传统续写方式）：**

```sh
curl -s http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "facebook/opt-125m",
    "prompt": "The capital of France is",
    "max_tokens": 32
  }' | jq .
```

#### Step 3: 查看 vLLM Metrics

```sh
curl -s http://localhost:8000/metrics | head -30
```

---

### 总结

在 WSL2 + kind 环境中成功部署 vLLM Production Stack 的关键点：

1. **WSL2 GPU 检测差异**：`lspci` 看不到 NVIDIA GPU 是 GPU-PV 架构的预期行为，并非 driver 版本问题。NFD 的 `pci` source 需要改用 `custom` source 通过 `nvidia-smi` 检测
2. **NVIDIA Device Plugin 正常**：Device Plugin 不依赖 PCI 检测，GPU 资源注册不受影响，`nvidia.com/gpu` 正常可用
3. **生产环境注意**：真实裸机 Linux 节点上 `lspci` 可正常看到 NVIDIA PCI 设备，NFD 的 `pci` source 直接可用。WSL2 特有的 workaround（如 `ln -s` 创建 `libcuda.so` 软链接和 NFD custom source）仅限开发环境
