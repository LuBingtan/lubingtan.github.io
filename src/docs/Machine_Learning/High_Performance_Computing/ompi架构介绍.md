# Open MPI 架构介绍

## Abstract

Open MPI 架构介绍阅读笔记

参考：

[The Architecture of Open Source Applications (Volume 2): Open MPI (aosabook.org)](http://www.aosabook.org/en/openmpi.html) 

https://www.open-mpi.org/video/internals/Cisco_JeffSquyres-1up.pdf

> 注意：这两篇介绍都是基于Open MPI 的 1.x 版本。在更高的版本中，已经有部分代码架构发生了变化，在结合源码阅读时一定要切换到 1.x 版本，否则容易产生困惑。

[open-mpi/ompi: Open MPI main development repository (github.com)](https://github.com/open-mpi/ompi)

## Background

### The Message Passing Interface (MPI)

MPI是一套通信标准，由[MPI Forum](http://www.mpi-forum.org/)创建并维护（MPI Forum是一个开放组织，由工业、学术界的高性能计算领域的专家组成）.

MPI是这样一种API：

* 可移植
* 高性能的IPC通信

MPI一般作为一个消息传递的中间件，上层应用程序可以通过调用MPI接口来执行消息传递。

MPI定义了一系列与平台无关的、高度抽象的API接口，用于进程之间的消息传递。举一个最简单的例子，进程X是发送进程，只需提供消息内容（例如一个双精度数组）以及另一个接收进程的标识（例如进程Y），同时接收进程Y只需提供发送进程的标识（例如进程X），消息就可以从X传递给Y。

注意这个例子中，没有建立连接、没有字节流的转换、没有网络地址的交换，MPI将这些细节都抽象封装了起来，不仅仅是隐藏了复杂性，而且使应用程序能够兼容不同的平台、硬件以及网络类型。

MPI提供的通信模式：

* point to pint
* collective
* broadcast

### Uses of MPI

Open-MPI 使 MPI 接口的一个开源实现。支持的网络类型包括但不限于: various protocols over Ethernet (e.g., TCP, iWARP, UDP, raw Ethernet frames, etc.), shared memory, and InfiniBand.

MPI 实现一般关注以下几个指标：

* 短消息传递的超低latency：将1-byte数据从linux用户线程传递给另一台服务器的用户线程，通过InfiniBand，只需要消耗1微妙（0.000001 second）
* 短消息传递的超高网络注入率(Extremely high message network injection rate)：一些MPI实现（搭配特定硬件）能够实现高达28 million / second 向网络注入消息。
* Quick ramp-up (as a function of message size) to the maximum bandwidth supported by the underlying transport.
* Low resource utilization：不能影响应用程序的性能

### Open MPI的诞生

Open MPI 联合了四种MPI的不同实现： 

* LAM/MPI,
* LA/MPI (Los Alamos MPI)
* FT-MPI (Fault-Tolerant MPI)
* PACX-MPI

## Architecture

Open MPI使用C语言编写

Open MPI 是一个非常庞大、复杂的代码库

* 2003的MPI 标准——MPI-2.0，定义了超过300个API接口
* 之前的4个项目，每个项目都非常庞大。例如，LAM/MPI由超过1900个源码文件，代码量超过30W行。
* 希望Open MPI尽可能的支持更多的特性、环境以及网络类型。

因此Open MPI花了大量时间设计架构，主要专注于三件事情：

* 将相近的功能划分在不同的抽象层
* 使用运行时可加载的插件以及运行时参数，来选择相同接口的不同实现
* 不允许抽象影响性能

### Abstraction Layer Architecture

Open MPi 可以分为三个主要的抽象层，自顶向下依次为：

* *OMPI (Open MPI)* (pronounced: oom-pee):
  * 由 MPI standard 所定义
  * 暴露给上层应用的 API，由外部应用调用
* *ORTE (Open MPI Run-Time Environment)* (pronounced "or-tay"):
  
  * MPI 的 run-time system
    *  launch, monitor, kill individual processes 
    *  Group individual processes into “jobs”
  * 重定向stdin、stdout、stderr
  * ORTE 进程管理方式：在简单的环境中，通过`rsh`或`ssh` 来launch 进程。而复杂环境(HPC专用)会有shceduler、resource manager等管理组件，面向多个用户进行公平的调度以及资源分配，ORTE支持多种管理环境，例如，orque/PBS Pro, SLURM, Oracle Grid Engine, and LSF.
  
  > 注意 ORTE 在 5.x 版本中被移除，进程管理模块被替换成了[prrte]([openpmix/prrte: PMIx Reference RunTime Environment (PRRTE) (github.com)](https://github.com/openpmix/prrte))

* *OPAL (Open, Portable Access Layer)* (pronounced: o-pull): OPAL 是xOmpi的最底层
  * 只作用于单个进程
  * 负责不同环境的可移植性
  * 包含了一些通用功能（例如链表、字符串操作、debug控制等等）

<img src="https://i.loli.net/2021/05/15/h9SxQC4mpiWVIeA.png" alt="img" style="zoom: 50%;" />

以上各个抽象层都是以 library 的形式存在，他们之间的依赖关系只能从上到下，也就是下层的不能依赖上层的。

<img src="https://i.loli.net/2021/05/15/IcHgv2zi1VsUynj.png" alt="image-20210515092155899" style="zoom:50%;" />

在代码目录中是以project的形式存在，也就是

```tex
ompi/
├── ompi
├── opal
└── orte
```



需要注意的时，考虑到性能因素，Open MPI 有中“旁路”机制（bypass），ORTE以及OMPI层，可以绕过OPAL，直接与操作系统（甚至是硬件）进行交互。例如OMPI会直接与网卡进行交互，从而达到最大的网络性能。

### Plugin Architecture

为了在 Open MPI 中使用类似但是不同效果的功能，Open MPI 设计一套被称为**Modular Component Architecture (MCA)**的架构.

在MCA架构中，为每一个抽象层（也就是OMPI、ORTE、OPAL）定义了多个framework，这里的framework类似于其他语言语境中的接口（interface），framework对于一个功能进行了抽象，而plugin就是对于一个framework的不同实现。每个 Plugin 都是以动态链接库（DSO，dynamic shared object）的形式存在。因此run time 能够动态的加载不同的plugin。

例如下图中 btl 是一个功能传输bytes的framework，它属于OMPI层，btl framework之下又包含针对不同网络类型的实现，例如 tcp、openib (InfiniBand)、sm (shared memory)、sm-cuda (shared memory for CUDA)

> 在Open MPI 2.x 以上版本，btl 模块已经被移到了 OPAL 之下

<img src="https://i.loli.net/2021/05/15/ETWmp7lOUcnBMe6.png" alt="image-20210515121838974" style="zoom: 80%;" />

为什么使用Plugin架构：

* 更好的软件工程
  * 实行严格的抽象划分
* 使代码块变得比较小且彼此之间独立
  * 对于学习以及新加入的开发者比较友好
  * 更容易维护和扩展
* 将用户应用于后端库分离
  * 在编译时MPI 应用，不需要考虑使用的哪个特定的库，例如 libibverbs.so / libportals.so / libpbs.a

#### MCA 设计

MCA：

* Top-level architecture for component services 
* Find, load, unload components 

Frameworks ：

* 包含一系列功能
* 定义接口 
* 本质: plugin 类型分组
* 例如：MPI point-to-point, high-resolution timers

Components（Plugins）：

* Code that exports a specific interface 
* Loaded / unloaded at run-time (usually) 

Modules：

* 与资源绑定
* 例如：“btl_tcp” 组件被加载时, 发现两个网卡(eth0, eth1), btl_tcp组件会创建两个 TCP module

#### MCA 代码结构

Frameworks：

* 拥有唯一的名字（string name）

Components：

* Belong to exactly one framework 
* Have unique string names 
* Namespace is per framework 

> 所有的名字都是可用的C变量名

目录结构：

* 层级结构：\<project\>/mca/\<framework\>/\<component\>
  * Project = opal, orte, ompi
  * Framework = framework name, or “base”
  * Component = component name, or "base"

* Directory names must match
  * Framework name 
  * Component name 
* 例子：
  * ompi/mca/btl/tcp, ompi/mca/btl/sm

```
./ompi/mca
├── allocator
│   ├── Makefile.am
│   ├── allocator.h
│   ├── base
│   ├── basic
│   └── bucket
├── bcol
│   ├── Makefile.am
│   ├── base
│   ├── basesmuma
│   ├── bcol.h
│   └── ptpcoll
├── bml
│   ├── Makefile.am
│   ├── base
│   ├── bml.h
│   └── r2
```

#### MCA 代码实现

* 使用函数指针实现抽象
* 一般被编译为动态库（DSO，so文件）
* 也可以以静态库打包进libmpi
* 使用GNU工具libltdl，能够进行跨平台的加载DSO

##### Components struct

该结构的定义为于 `ompi/mca/btl/btl.h`

```c
struct mca_base_component_2_0_0_t {
    /* Component struct version number */
    int mca_major_version, mca_minor_version, mca_release_version;

    /* The string name of the framework that this component belongs to,
       and the framework's API version that this component adheres to */
    char mca_type_name[MCA_BASE_MAX_TYPE_NAME_LEN + 1];
    int mca_type_major_version, mca_type_minor_version,  
        mca_type_release_version;

    /* This component's name and version number */
    char mca_component_name[MCA_BASE_MAX_COMPONENT_NAME_LEN + 1];
    int mca_component_major_version, mca_component_minor_version,
        mca_component_release_version;

    /* Function pointers */  
    mca_base_open_component_1_0_0_fn_t mca_open_component;
    mca_base_close_component_1_0_0_fn_t mca_close_component;
    mca_base_query_component_2_0_0_fn_t mca_query_component;
    mca_base_register_component_params_2_0_0_fn_t 
        mca_register_component_params;
};

typedef struct mca_base_component_2_0_0_t mca_base_component_t;

typedef struct mca_base_component_2_0_0_t mca_base_component_2_0_0_t;
```

几个关键的函数指针：

* open
* close
* query
* register

##### Framework Interface

以btl为例，位于 `ompi/mca/btl/btl.h`

```c
struct mca_btl_base_component_2_0_0_t {
  mca_base_component_t btl_version;
  mca_base_component_data_t btl_data;
  mca_btl_base_component_init_fn_t btl_init;
  mca_btl_base_component_progress_fn_t btl_progress;
};
typedef struct mca_btl_base_component_2_0_0_t mca_btl_base_component_2_0_0_t;
typedef struct mca_btl_base_component_2_0_0_t mca_btl_base_component_t;
```

##### Plugin

以btl_tcp为例：

```c
struct mca_btl_tcp_component_t {
    /* btl framework-specific component struct */ 
    mca_btl_base_component_2_0_0_t super;

    /* Some of the TCP BTL component's specific data members */
    /* Number of TCP interfaces on this server */
    uint32_t tcp_addr_count;
    
    /* IPv4 listening socket descriptor */
    int tcp_listen_sd;

    /* ...and many more not shown here */
};
```

##### Module

与Plugin类似，有基类也有实现类。

btl base module：

```c
struct mca_btl_base_module_t {
// ......
}
```

tcp module：

```c
struct mca_btl_tcp_module_t {
    mca_btl_base_module_t  super;
    // ......
}
```

每个Plugin可能创建多个Module，与该Plugin关联的资源相关。

<img src="https://i.loli.net/2021/05/15/PSR6JKveHcZbd2r.png" alt="img" style="zoom:50%;" />

#### Component / Module Lifecycle 

<img src="https://i.loli.net/2021/05/15/t4WIcMepAUi8XfP.png" alt="image-20210515163520778" style="zoom: 50%;" />

### Run-Time Parameters

也被称为MCA Parameters，提供 MCA 组件参数，以及base参数。

#### 设计背景

* 尽量避免使用constants，用run-time参数代替
  * 避免重新编译
* 在run-time期间改变程序的行为
  * 在特定环境中，找到实现最佳性能的参数

#### 如何使用

##### 内建参数

* 每个framework的名字都是mca 参数
* 能够指定使用哪一个plugin
* 可以指定include或exclude 行为，例如 btl=tcp,self,sm, 或 btl = ^openib

##### 如何更改参数

* 应用程序中，使用MPI API接口，覆盖默认参数
* 使用命令行工具
  * 例如：`mpirun -mca <name> <value>`
* 使用环境变量
  * `setenv OMPI_MCA_<name> <value>`
* 在文件中更改
  * `$HOME/.openmpi/mca-params.conf`
  * `$prefix/etc/openmpi-mca-params.conf`

mca 参数特性：

* 一般由字符串以及数字组成
* 有的参数是只读的，有的是读写的
* 有的参数是private 的，有的是public的

mca参数名称规则：

`<framework>_<component>_<param_name>`

几个mca 参数例子：

* **btl_udverbs_version**：Read-only, string version of the Verbs library that udverbs BTL was compiled against
* **btl_tcp_if_include**: Read-write, string list of IP interfaces to use
* **btl**: Read-write, list of BTL components to use
* **orte_base_singleton**: Private, whether this process is a singleton

另外，可以通过 ompi_info 命令行工具查看哪些参数可以使用。

##### 如何实现

mca_base负责解析MCA 参数。

