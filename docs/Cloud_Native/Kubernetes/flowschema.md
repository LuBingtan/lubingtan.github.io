## What is FlowSchema

FlowSchema一种 resoruce, 它可以配置 kube-apiserver 的流量控制. 比如对于哪种流量需要优先处理, 哪种流量可以拒绝, 哪种流量如果来不及处理就先加到队列中.

A flowschema spec is like this:

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta1
kind: FlowSchema
metadata:
 name: fcp-service
spec:
 distinguisherMethod:
   type: ByNamespace
 matchingPrecedence: 50
 priorityLevelConfiguration:
   name: system
 rules:
 - nonResourceRules:
   - nonResourceURLs:
     - '*'
     verbs:
     - '*'
   resourceRules:
   - apiGroups:
     - '*'
     clusterScope: true
     namespaces:
     - '*'
     resources:
     - '*'
     verbs:
     - '*'
   subjects:
   - kind: ServiceAccount
     serviceAccount:
       name: '*'
       namespace: fcp-pp
```



## How does FlowSchema work?

FlowSchema 定义了一组 rules, 如果一个 request hit 其中一个 rule, 就可以认为它属于这个 FlowSchema.

然后这个flowschema对应的流量控制规则定义在 `priorityLevelConfiguration`



PriorityLevelConfiguration 是另一种 resource, 它长这个样子:

```yaml
kind: PriorityLevelConfiguration
metadata:
  name: system
spec:
  limited:
    assuredConcurrencyShares: 8000
    limitResponse:
      queuing:
        handSize: 15
        queueLengthLimit: 100
        queues: 15
      type: Queue
  type: Limited
status: {}
```

这个规则对应的并发限制和这个值 `assuredConcurrencyShares` 有关:

并发限制 = 总并发量 * assuredConcurrencyShares / 所有的assuredConcurrencyShares之和

> 其中 总并发量 = max-requests-inflight + max-mutating-requests-inflight
>
> max-requests-inflight 和 max-mutating-requests-inflight 是 kube-apiserver 参数

举个例子:

apiserver 的 max-requests-inflight=4000 max-mutating-requests-inflight=2000

```
bingtlu@R0016P43QH ~ % k get priorityLevelConfiguration
NAME              TYPE      ASSUREDCONCURRENCYSHARES   QUEUES   HANDSIZE   QUEUELENGTHLIMIT   AGE
catch-all         Limited   1                          <none>   <none>     <none>             679d
exempt            Exempt    <none>                     <none>   <none>     <none>             679d
federation        Limited   4000                       128      6          50                 679d
global-default    Limited   2000                       128      6          50                 679d
leader-election   Limited   1000                       16       4          50                 679d
system            Limited   8000                       15       15         100                679d
workload-high     Limited   3000                       128      6          50                 679d
workload-low      Limited   2500                       128      6          50                 679d
```



system的并发限制 = 6000 * 8000 / (1+4000+2000+1000+8000+3000+2500) = 2341.35



如果超出了这个并发量怎么办? 加到队列里面等待. 一个 priorityLevelConfiguration 包含多个queue, 根据 `distinguisherMethod`分流(flows), 不同的 flow 不会冲突 (比如distinguisherMethod 是 ByUser, 那么当某个user发了大量请求, 不会阻塞另一个user的请求)



还有一种特殊的 priorityLevelConfiguration, 就是 `exempt`, exempt 就是没有限制, 一般会把最重要的request设置成 exempt, 比如group=system:masters



