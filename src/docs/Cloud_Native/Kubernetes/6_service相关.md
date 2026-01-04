# What is Kubernetes Service

将运行在一组 [Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/) 上的应用程序公开为网络服务的抽象方法。

使用 Kubernetes，你无需修改应用程序即可使用不熟悉的服务发现机制。 Kubernetes 为 Pods 提供自己的 IP 地址，并为一组 Pod 提供相同的 DNS 名， 并且可以在它们之间进行负载均衡。

在

# Why Use Service

# How Service Works

## 创建了一个Service之后会发生什么

1. 客户端访问kube-apiserver，创建一个service资源，apiserver将service保存在etcd
2. service controller watch到这个被创建的service，

### Service Controller 



### Endpoints Controller原理（TODO）

#### pod 挂了一个sidecar时，kube dns还会生效吗

pod 的 status.conditions字段，里面如果是conditon是not ready的，service对应的endpoints只会把pod ip更新到 NotReadyAddress 字段
然而1.14版的kube-dns只会根据endpoints的 Address 字段注册域名ip

endpoints_controller.go中的endpoint更新逻辑：

```go
func addEndpointSubset(subsets []v1.EndpointSubset, pod *v1.Pod, epa v1.EndpointAddress,
	epp *v1.EndpointPort, tolerateUnreadyEndpoints bool) ([]v1.EndpointSubset, int, int) {
	var readyEps int = 0
	var notReadyEps int = 0
	ports := []v1.EndpointPort{}
	if epp != nil {
		ports = append(ports, *epp)
	}
	if tolerateUnreadyEndpoints || podutil.IsPodReady(pod) {
		subsets = append(subsets, v1.EndpointSubset{
			Addresses: []v1.EndpointAddress{epa},
			Ports:     ports,
		})
		readyEps++
	} else if shouldPodBeInEndpoints(pod) {
		glog.V(5).Infof("Pod is out of service: %s/%s", pod.Namespace, pod.Name)
		subsets = append(subsets, v1.EndpointSubset{
			NotReadyAddresses: []v1.EndpointAddress{epa},
			Ports:             ports,
		})
		notReadyEps++
	}
	return subsets, readyEps, notReadyEps
}
```

kube-dns 中的注册ip的逻辑：

```go
func (kd *KubeDNS) generateRecordsForHeadlessService(e *v1.Endpoints, svc *v1.Service) error {
	subCache := treecache.NewTreeCache()
	glog.V(4).Infof("Endpoints Annotations: %v", e.Annotations)
	for idx := range e.Subsets {
		for subIdx := range e.Subsets[idx].Addresses {
			address := &e.Subsets[idx].Addresses[subIdx]
			endpointIP := address.IP
			recordValue, endpointName := util.GetSkyMsg(endpointIP, 0)
			if hostLabel, exists := getHostname(address); exists {
				endpointName = hostLabel
			}
			subCache.SetEntry(endpointName, recordValue, kd.fqdn(svc, endpointName))
			for portIdx := range e.Subsets[idx].Ports {
				endpointPort := &e.Subsets[idx].Ports[portIdx]
				if endpointPort.Name != "" && endpointPort.Protocol != "" {
					srvValue := kd.generateSRVRecordValue(svc, int(endpointPort.Port), endpointName)
					glog.V(2).Infof("Added SRV record %+v", srvValue)

					l := []string{"_" + strings.ToLower(string(endpointPort.Protocol)), "_" + endpointPort.Name}
					subCache.SetEntry(endpointName, srvValue, kd.fqdn(svc, append(l, endpointName)...), l...)
				}
			}

			// Generate PTR records only for Named Headless service.
			if _, has := getHostname(address); has {
				reverseRecord, _ := util.GetSkyMsg(kd.fqdn(svc, endpointName), 0)
				kd.reverseRecordMap[endpointIP] = reverseRecord
			}
		}
	}
	subCachePath := append(kd.domainPath, serviceSubdomain, svc.Namespace)
	kd.cacheLock.Lock()
	defer kd.cacheLock.Unlock()
	kd.cache.SetSubCache(svc.Name, subCache, subCachePath...)
	return nil
}
```

