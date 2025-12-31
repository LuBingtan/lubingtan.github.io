<h1>dd</h1>

Kubernetes Contributing 记录


参考: [kubernetes/community: development.md](https://github.com/kubernetes/community/blob/master/contributors/devel/development.md)

---
## Prepare
1. 拉仓库 github.com/kubernetes/kubernetes

2. 按照必要的依赖 (环境 m1 mac)

   ```bash
   # binary
   brew install coreutils ed findutils gawk gnu-sed gnu-tar grep make jq
   # python package
   pip3 install pyyaml
   ```

3. 检查一下 `make verify` (可能要很长时间)
   - 安装 etcd `hack/install-etcd.sh`
   - 安装 protoc `hack/install-protoc.sh`
4. 





## Canditate Issue

### Issue [#104155](https://github.com/kubernetes/kubernetes/issues/104155)

reproduce
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-deployment
  namespace: default
spec:
  minReadySeconds: 5
  replicas: 3
  selector:
    matchLabels:
      app: example
  strategy:
    rollingUpdate:
      maxSurge: 50%
      maxUnavailable: 0%
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: example
    spec:
      containers:
        - image: nginxdemos/hello:latest
          imagePullPolicy: Always
          name: api
          resources:
            limits:
              cpu: "1"
              memory: 105Mi
            requests:
              cpu: "100m"
              memory: 105Mi
      restartPolicy: Always
      terminationGracePeriodSeconds: 120
```

