# Moose
Moose是一个数据处理的自动化框架，旨在提供一套快速、灵活、便捷、幂等式的数据处理方案。它不仅提供了常用的数据处理类和函数，也提供了一套命令行式的接口以处理和维护版本内单一、重复、繁琐的任务。
- - - -
## 安装指南
 Moose 运行在Python 2.7和Python 3.3及以上版本。

### 安装发布版
这是较为推荐的安装方法：
	1. 安装pip。最简单的方法是使用[pip安装脚本](https://pip.pypa.io/en/latest/installing/#installing-with-get-pip-py)。如果你的Python发布版已经安装了pip，你可能需要更新以避免由于版本过老导致安装失败。
	2. 了解[virtualenv](https://virtualenv.pypa.io/en/stable/)或[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)并安装教程。这些工具提供了一个独立的Python环境，相比在全局范围内安装包要更加有效且实用，并且不需要管理员权限。这份[文档](https://docs.djangoproject.com/en/1.11/intro/contributing/)提供如何在Python3环境中安装virtualenv的指导。
	3. 安装并且激活虚拟环境后，在命令提示符中输入**pip install Moose**。

### 安装开发者版本
如果你希望安装最新版本的Moose，可以通过以下教程来尝试：
	1. 确认你已安装Git并且可以从命令行中访问。
	2. 获取Moose的主分支代码：
```
$ git clone https://github.com/muma378/moose.git	
```
	这会为你在当前目录下创建一个名为**moose**文件夹。
	3. 确认你的Python解释器可以加载Moose代码。最常见的办法是使用[virtualenv](https://virtualenv.pypa.io/en/stable/)，[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)和 [pip](https://pip.pypa.io/)。这份[文档](https://docs.djangoproject.com/en/1.11/intro/contributing/)提供如何在Python3环境中安装virtualenv的指导。
	4. 在安装和激活virtualenv之后，运行以下命令：
```
$ pip install -e moose/	
```
	这会使得Moose的代码可以被导入（importable），并且使得**moose-admin**等命令行工具可用。至此，我们就完成了安装！

当你想要更新你的Moose代码时，只需要在moose文件夹内运行命令**git pull**，Git便会自动下载任何更新。

### 需要知道的事情
Moose完全由Python编写并且依赖于以下几个关键的Python包（Packages）：
* [azure](http://azure-sdk-for-python.readthedocs.io/en/v2.0.0rc6/)，微软 Azure云服务的SDK的Python版本；
* [pymongo](https://dfproj.readthedocs.io/en/latest/)，包含多个通过Python与MongoDB交互的工具；
* [pymssql](http://pymssql.org/en/stable/)，一个基于Python DB-API ([PEP-249](http://www.python.org/dev/peps/pep-0249/))的访问SQLServer数据库的接口；
* [MySQLdb](https://mysqlclient.readthedocs.io/)，一个提供了访问MySQL数据库的线程兼容的Python库；
* [OpenCV](http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_tutorials.html)，经典图像处理库OpenCV的Python版本；
* [Pillow](http://pillow.readthedocs.io/en/stable/)，一个友好的Python图像库，提供了更直白的图像处理函数；

- - - -
## 快速上手教程
在这篇教程中，我们假设你已经安装好了Moose并且了解一个数据标注项目的基本流程，如果还没有的话请参考**安装指南**和**标注任务创建指南**。

我们将以一个名为 **cityscape** 的图片标注项目开始，该项目需要在[标注平台](http://bz.datatang.com/Admin/task/markList)上创建任务，上传图片数据并建立索引关系，待标注人员完成后，再将结果从后端提取出来，整理成相应格式并等待交付客户。

这篇教程将会着重讲述Moose相关的操作，包含以下要点：
	1. 创建一个新的Moose项目；
	2. 创建一个新的app并配置工单模板;
	3. 编写action：upload，完成数据上传和建立索引；
	4. 编写model，完成数据的导出功能；
	5. 完成单元化测试。

### 创建一个Moose项目

在开始为一个数据标注（采集）项目编写相关的业务逻辑之前，我们需要创建一个Moose Project。在你想要保存代码的地方打开命令行，输入：
```
$ moose-admin startproject tutorial
```
这

**app** 是automate中基本的执行单位，相当于一个独立的脚本，所有的操作都是基于它执行。首先，我们在命令行中输入以下命令以创建一个名为 _sayhi_ 的app：

```
> ./bin/startapp sayhi
```

输入该命令后，我们注意到在当前文件夹下出现了一些新的内容:

```
├ conf
|  └ sayhi
|      └ template.cfg
├ data
|  └ sayhi
├ logs
|  └ sayhi.log
└ src
   ├ apps
   |   └ app_sayhi.py
   └ requires
       └ sayhi.req
```

如图所示，automate为我们自动创建了conf和data目录下名为sayhi的文件夹，这两个目录分别用来存放app的配置文件和生成文件。其中 `conf/sayhi/template.cfg` 是配置文件的模板，我们会在之后的代码中使用到它。
`src/apps/app_sayhi.py` 将是我们主要的代码编辑区域，只应包含业务逻辑相关的代码。打开该文件，里面已经提供了如下内容：

```
import settings
from utils.parse import parse_config
def main():
    config = parse_config()
def usage():
    return ""
```

main()函数是app的入口，控制着整个app的流程，我们的代码就从这里开始。向 `app_sayhi.py` 中添加如下的代码：

```
import os
import settings
from utils.parse import parse_config
from utils.dateutil import name_as_datetime
def main():
    config = parse_config()
    name = config.get('data', 'name')
    product_dir = os.path.join(settings.DATA_DIR, 'sayhi')
    if not os.path.exists(product_dir)：
        os.makedirs(product_dir)
      with open(name_as_datetime(product_dir)) as f:
          f.write("Hi, {0}".format(name))
def usage():
    return "say hi to a friend"
```

我们的app相当简单，不过对于我们最常见的情景已经足够了。它实现了从配置文件中获取_name_这个参数，并输出到以当前日期时间命名的文件当中去。我们将在下一节中介绍如何编写以及维护配置文件。

### Generates configs
我们已经完成了app的编码，在运行之前，还要编写配置文件以定义输入输出。打开 `conf/sayhi/template.cfg` ，添加如下内容：

```
[data]
name = ?
```

之后，在命令行中输入：

```
> ./bin/gen_config sayhi
```

我们注意到 `conf/sayhi` 目录下新增加了如下内容：

```
└ sayhi
   ├ .Nov21-0920.cfg        # it could be a differnent name
     ├ config.cfg
     └ template.cfg
```

打开 `conf/sayhi/config.cfg` ， 里面的内容和之前在 `template.cfg` 中定义的一模一样，我们将它稍作修改：

```
[data]
name = Mary
```

至此，我们的配置文件就已经编写完成。

### Run
在上一节中我们完成了对输入输出的定义，只要在 `settings` 中注册我们的app就可以开始运行我们的程序了。打开 `settings_local.py` ，在 `apps` 中添加你的app的名称就可以了，以 `sayhi` 为例，输入以下内容：

```python
apps = [
    "sayhi",
    ]

```

现在，在命令行中输入以下内容：

```
> ./bin/run sayhi
excuting apps.app_sayhi
done
```

现在再检查 `data/sayhi` 目录下的内容，我们发现新添加了一个命名规则与 `Nov21-0920.txt` 类似的文件（代表着数据被生成的时间），输出其中的内容：

```
> cat data/sayhi/Nov21-0920.txt
Hi, Mary
```

一旦一个app稳定下来后，针对每一次任务，我们便可以重复运行上一节(gen_config)与这一节(run)的操作，使得后续的任务变得简单可维护，这也正是Automate的意义所在。

### Coding Specification
#### Logging
我们建议所有的提示性输出都应该通过日志文件系统被记录到日志中以方便定位和回溯。Python提供了一套完整的[日志机制]( [15.7. logging — Logging facility for Python — Python 2.7.12 documentation](https://docs.python.org/2/library/logging.html) )。我们在Automate中隐去了所有细节，每个app的编写者只需要导入 `settings` 模块中的 `logger` 对象，按照如下方式调用即可：

```
from settings import logger
logger.DEBUG("debug")
logger.INFO("info")
logger.WARNING("warning")
logger.ERROR("error")
logger.CRITICAL("critical")
```

_目前，我们只是将所有的日志输出到access.log，而将error级别及以上的错误输出到error.log以方便用户快速发现较为严重的错误。将来我们可能调整日志机制，为每个app提供相应的log文件以隔离不同app产生的日志文件_

#### Virtual Environment
不同的app可能会有对于同一个package不同版本的需求，同时，对于只使用其中某个app的人来说，也没有必要安装所有app的相关依赖包。因此我们提供了命令 `install` 去帮助用户快速地搭建起开发环境。

```
> echo "six==1.10.0" > src/requires/sayhi.req
> ./bin/install sayhi
building virtual environment...
activating environment...
installing packages...
six==1.10.1
done
```

#### Clean
针对编码和调试时经常出现的重复运行 `gen_config` 和 `run` 导致产生冗余的或无意义的配置和输出文件，我们提供了命令 `clean` 去帮助用户清理conf和data文件夹。输入命令

```
> ./bin/clean sayhi
```
会自动找出相应app中多余的配置和输出文件，打印在屏幕上，待用户确认后将其删除掉，使得每份副本只有最新生成的那一份被保留。

## Basic Concept
### Hierarchy
Automate将传统的任务按照如下结构组织起来：

* **bin** 框架提供的命令文件；
* **conf** 每期任务对应的特定参数的配置文件，相当于传统脚本运行时的参数列表；
* **data** 默认数据存储区域，脚本运行时读取及生成的数据默认存放在与之对应的文件夹下；
* **logs** 脚本运行产生的对应的日志文件；
* **tools** 运行时需要的相关工具，通常为二进制或其他语言编写的可执行文件；
* **src** 代码目录：
	* **apps** 每一类任务即一个app，也可理解成实现了特定接口的一个（组）脚本；
	* **settings.py** 通用配置文件，包含框架运行的核心参数配置，不应修改；
	* **settings_local.py** 本地配置文件，包含本地自定义的参数配置，可覆盖通用配置中的配置项；
	* **core/*** 数据处理库和模块。

### Commands
Automate提供了一系列的命令以方便用户对任务进行快速配置和管理：

* **list** 列出所有命令及使用方法；
* **startapp** 生成app脚本文件以及相应的目录；
* **genconf** 生成配置文件模板，默认调用app对应的_gen_template.py_，如果不存在则拷贝对应的_template.cnf_，如果不存在则拷贝_src_conf_common.cnf_;
* 
* **run** 运行相应app；
* **clean** 清除对应app内或为空或为冗余的配置文件和输出文件；
* **install** 脚本依赖安装;
* **history** 执行及生成数据的历史记录及对应关系（TODO）；
* **crontab** 设定定时任务（TODO）；
* **toolkit** 常用工具的命令行式调用（TODO）；

### Libraries
除了方便的命令接口，Automate也提供了对通用功能的抽象和封装：

* **core**
	* **handlers**
		* _convert_ 音频，图片格式转换；
		* _decrypt_ 加密解密功能；
		* _download_ http或ftp方式获取数据；
	* **storage**
		* _database_ 提供对sqlserver和MongoDB数据库访问；
		* _smb_proxy_ 提供对ftp的访问；
	* **common**
		* _mail_ 邮件系统，提供任务完成通知
* **utils**
	* _parse_ 配置文件解析；
	* _stocking_ 出库相关的数据库查询操作；
	* _traverse_ 文件遍历；
	* _crop_ 图片剪切；
	* _match_ 关键字匹配。