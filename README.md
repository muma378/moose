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

    现在，Moose的代码就可以被导入（importable），并且可以使用**moose-admin**等命令行工具了。至此，我们就完成了安装！

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

我们将以一个名为 **cityscape** 的图片标注项目开始(得益于各大厂商在自动驾驶研发上的投入，对街景图像的采集与标注的需求也变得旺盛)，该项目需要在[标注平台](http://bz.datatang.com/Admin/task/markList)上创建任务，上传图片数据并建立索引关系，待标注人员完成后，再将结果从后端提取出来，整理成相应格式并等待交付客户。

这篇教程将会着重讲述Moose相关的操作，包含以下要点：
1. 创建一个新的Moose项目；
2. 创建一个新的application;
3. 编写action：upload，完成数据上传和建立索引；
4. 编写template，解耦数据和功能；
4. 编写model，导出标注数据；
5. 完成单元化测试。

### 创建一个Moose项目

在开始为一个数据标注（采集）项目编写相关的业务逻辑之前，我们需要创建一个Moose Project。在你想要保存代码的地方打开命令行，输入：

```
$ moose-admin startproject tutorial
```

这将会在当前文件夹中创建以下内容：

```python
tutorial/
    tutorial/   # project's python module
        __init__.py     # an empty file tells Python that this directory should be considered as a package
        settings.py     # settings/configuration for this Moose project
        template.cfg    # global tasks' config template
    manage.py   # a command-line utility that let you interact with Moose in various ways
```

### 创建一个新的application

现在，你的工作环境——Moose Project——已经创建起来，我们可以开始真正的工作了。
每一个你通过Moose编写的 **application** 都遵循一套特定的规则，他们既是Python的一个package，同时也是与一个“项目”——不同于前文提到的 *Moose Project*，这里指的是 **工程意义** 上的项目——相关的所有（代码层面上的）业务逻辑的集合。
Moose提供了一系列的工具来自动创建相应的文件和文件夹，使得开发者可以专注于编写业务逻辑的代码而不是创建文件。为了创建(一个名叫 *cityscape* 的) **app**，你需要在之前创建的Moose Project的目录下（在与 **manage.py** 同一级目录里）输入：

```
$ python manage.py startapp cityscape
```

这将会为你创建一个叫 **cityscape** 的文件夹，内部结构如下：

```python
cityscape/
    configs/    # directory to put tasks' config files
    data/       # directory for input/output data
    __init__.py     
    actions.py      # actions defined that application runs with
    apps.py         # control center to glue all components
    models.py       # object representation for data queried from the backend
    template.cfg    # local tasks' config template
    tests.py        
```

这其中尤其需要注意的是 *cityscape/apps.py* 。它是整个app的控制中心，负责连接各个单元和模块，使正确的配置文件（**configs**）被加载、动作（**actions**）能通过命令行被触发、数据被存储到正确的位置（**data**）。我们之后会了解到它是如何控制的，现在，你唯一需要做的是提供一些项目相关的信息：

```python
# -*- coding: utf-8 -*-
from moose.apps import AppConfig

class CityscapeConfig(AppConfig):
    name = 'cityscape'
    verbose_name = u"街景道路标注"

```

### 编写action：upload，完成数据上传和建立索引；

项目很快开始运作起来，我们接到的第一个任务是创建一期标注任务，并且向我们提供了以下信息：

* 数据来源：*/data/cityscape/vol1* 目录下的所有图片
* 模板名称：*街景图片多边形标注 v1.1*
* 索引格式：
    ```js
    {
        "url": "path/to/image01.jpg", "dataTitle": "image01.jpg"
    }
    ```

我们在这里不过多地解释这些信息代表的含义，如果你还不了解，请参考我们的文档 **《标注任务创建指南》** 。假设你已经根据这些信息在[标注平台](http://bz.datatang.com/Admin/task/markList)上创建了一期任务，并且返回了以下信息：

* 任务ID：*10000*
* 任务名称：*2017第2000期图片标注任务*
* 任务批次：*cityscape - vol1*

接下来要做的就是上传原始图片并且建立索引关系。这些动作被抽象成一个叫 **AbstractAction** 的类，我们在 *cityscape/actions.py* 定义它的实现：

```python
# -*- coding: utf-8 -*-
import os
import json
from moose import actions
from moose.connection.cloud import AzureBlobService
from tutorial import settings

class Upload(actions.AbstractAction):

    def run(self, **kwargs):
        """
        Inherited classes must implement this interface,
        which will be called then to perform the operation.
        """
        task_id = '10000'

        # Phase1. establishes the connection to azure and do uploading files
        azure = AzureBlobService(settings.AZURE)
        # lists all files in the data directory
        images = self.list_all_images('/data/cityscape/vol1')
        blobs = azure.upload(task_id, images)

        # Phase 2. creates the index file to declare the relationships
        # between files uploaded and names to display
        index_file = os.path.join(self.app.data_dirname, task_id+'.json')
        with open(index_file, 'w') as f:
            for blob_file in blobs:
                item = {
                    'url': blob_file,
                    'dataTitle': os.path.basename(blob_file)
                }
                f.write(json.dumps(item))

```

为了避免我们的教程陷入过多细节的讨论，我们跳过了部分具体实现，例如 *list_all_images* 方法和 *AzureBlobService* 类。目前你只需要了解：通过继承 **actions.AbstractAction** 并对接口 **run** 添加实现，我们完成了原始文件的上传和索引文件的生成这两个功能。

为了使得这个 *Action* 可以在命令行里被调用，我们还需要做一件事情——在 *AppConfig* 中注册该动作。在 *cityscape/apps.py* 中添加以下内容：

```python
class CityscapeConfig(AppConfig):

    def ready(self):
        self.register('Upload', 'upload')   # now we can type `-a upload` to refer the action 'cityscape.actions.Upload'

```

注册完成之后，我们就可以在命令行中通过指定 *-a upload* 选项来运行我们之前在 *cityscape.actions.Upload* 中编写的代码了。在与之前相同的位置下输入：

```
$ touch cityscape/configs/null.cfg
$ python manage.py run cityscape -a upload -c null.cfg
```

此时，你应该可以在命令行中看见文件上传的进度条，以及生成的 *cityscape/data/10000.json* 文件了。至于在命令行中创建的 *null.cfg* 又是起什么作用，我们很快就会在下一节中讲到。

### 编写template，解耦数据和功能

如果你是一位有经验的开发者，那么你一定已经意识到我们之前的代码中存在一点问题——包含过多的“魔法常量”（*magic constant*），不仅如此，在实际的工作中我们还会发现，那些业务逻辑相关的代码通常是固定的，反而是这些“魔法常量”会频繁变化。
