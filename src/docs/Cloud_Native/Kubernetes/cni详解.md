## CNI 的作用:

参考: [K8S CNI之：利用ipvlan+host-local+ptp打通容器与宿主机的平行网络 | 国南之境 (hansedong.github.io)](https://hansedong.github.io/2019/03/19/14/)

- 给Pod分配IP
- 创建 network namespace, veth pair 以及 bridge
  - veth 一端放进容器的 net namespace
  - 另一端放在 host
  - host网卡以及 veth 设备加入 bridge , 这样容器才能与 host 通信

- 设置 route 规则
  - 指向本节点的 pod ip, gateway 设置成当前节点( iface 为对应的 veth)


另外如果要跨节点通信,

- 在节点上手动设置 route 规则 (`ip route add`)
  - 指向其他节点上的 Pod CIDR, gateway 设置成对应的节点 IP, 或者设置成交换机的 IP


查看network namespace

```bash
# ip netns list
cni-26105ccb-b905-e5b7-09e2-159a9f58ab64 (id: 1)
```

查看 veth

```bash
# ip link show type veth
4: vethbdd29507@if4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 06:a5:48:56:05:94 brd ff:ff:ff:ff:ff:ff link-netns cni-0d153976-a5a0-b8b8-9bb8-2d6938f2ed3d
31: eth0@if32: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 02:42:ac:12:00:02 brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

查看 路由规则

```bash
# ip route
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         172.18.0.1      0.0.0.0         UG    0      0        0 eth0
10.244.0.0      172.18.0.4      255.255.255.0   UG    0      0        0 eth0
10.244.1.2      0.0.0.0         255.255.255.255 UH    0      0        0 vethbdd29507
10.244.2.0      172.18.0.3      255.255.255.0   UG    0      0        0 eth0
172.18.0.0      0.0.0.0         255.255.0.0     U     0      0        0 eth0
# 或者
# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         172.18.0.1      0.0.0.0         UG    0      0        0 eth0
10.244.0.0      172.18.0.4      255.255.255.0   UG    0      0        0 eth0
10.244.1.2      0.0.0.0         255.255.255.255 UH    0      0        0 vethbdd29507
10.244.2.0      172.18.0.3      255.255.255.0   UG    0      0        0 eth0
172.18.0.0      0.0.0.0         255.255.0.0     U     0      0        0 eth0
```



## Kind 是怎么做的?

每个节点部署了一个 kindnetd

```bash
# kubectl -n kube-system  get ds kindnet
NAME      DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
kindnet   3         3         3       3            3           <none>          4h57m
```

kindnet 的作用:

- 动态配置每个节点的 cni 里的 CIDR

- 自动配置节点上的 route 规则, 这样才能跨节点通信

- 自动配置iptabels 规则, 给所有目标是**集群之外**的流量, 做 MASQUERADE (即把源 IP 自动改成当前的IP)

  > 为什么要改掉源 IP ? 假设这样的场景, 内网机器要访问外网, 外网服务器接受到请求后, 返回响应时要给哪个IP发送呢? 直接发给内网IP是无法访问的, 所以需要做 SNAT, 源IP设置成外网可见的网关(Gateway)

