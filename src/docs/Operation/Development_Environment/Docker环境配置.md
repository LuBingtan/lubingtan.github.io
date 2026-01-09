## Docker 安装
### 在Ubuntu/WSL中安装

#### 更换apt源(Optional)

/etc/apt/sources.list替换

```bash
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal universe
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates universe
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal multiverse
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates multiverse
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-backports main restricted universe multiverse
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security universe
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security multiverse
```

arm64

```
# 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-updates main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-backports main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-security main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-security main restricted universe multiverse

# 预发布软件源，不建议启用
# deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-proposed main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-proposed main restricted universe multiverse
```


#### 查看docker可用版本

```
apt-cache madison docker
```

#### 安装docker

##### 安装最新版本

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo bash get-docker.sh
sudo service docker start
```

##### 安装特定版本

```Bash
# 卸载
sudo apt-get remove docker docker-engine docker.io
sudo apt-get purge docker docker-engine docker.io
sudo apt-get update
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
# 查看docker-ce所有版本
sudo apt-cache madison docker-ce
# 选择一个版本进行安装
sudo apt-get install docker-ce=18.03.0~ce-0~ubuntu
```

##### 配置非root使用docker

```Bash
sudo groupadd docker
sudo gpasswd -a ${USER} docker
sudo service docker restart
newgrp - docker
```

### 在Mac中安装
#### Docker Desktop

[Mac | Docker Docs](https://docs.docker.com/desktop/setup/install/mac-install/)

#### Rancher Desktop

[Installation | Rancher Desktop Docs](https://docs.rancherdesktop.io/getting-started/installation)

#### 使用虚拟机
这里只列举一种虚拟机, 使用 multipass [canonical/multipass: Multipass orchestrates virtual Ubuntu instances (github.com)](https://github.com/canonical/multipass)

官方文档: [Multipass orchestrates virtual Ubuntu instances](https://multipass.run/install)

如何 ssh 进去:

[How to enable passwordless SSH login on Ubuntu 20.04 that's inside Multipass (techsparx.com)](https://techsparx.com/linux/multipass/enable-ssh.html)



## 配置Docker使用Proxy

### docker daemon 配置 proxy
查看system service 文件地址
```sh
~$ sudo systemctl cat docker
# /lib/systemd/system/docker.service
```
增加额外的配置
```sh
# mkdir /lib/systemd/system/docker.service.d
# cat  /lib/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="https_proxy=http://192.168.32.1:7897"
Environment="http_proxy=http://192.168.32.1:7897"
```
重启docker
```sh
systemctl daemon-reload
systemctl restart docker
```