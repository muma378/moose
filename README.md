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
3. 编写动作(action)：upload，完成数据上传和索引建立；
4. 创建订单(order)，定义动作接口；
4. 抽象模型(model)，导出标注数据；
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

### 编写动作(action)：upload，完成数据上传和索引建立

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

此时，你应该可以在命令行中看见文件上传的进度条，以及生成的 *cityscape/data/10000.json* 文件了。至于在命令行中创建的 *null.cfg* 是起什么作用，我们会在下一节中进行详细说明。

### 创建订单(order)，定义动作接口

如果你是一位有经验的开发者，那么你一定已经意识到我们之前的代码中存在一点问题——包含过多的“魔法常量”（*magic constant*），不仅如此，在实际的工作中我们还会发现，那些业务逻辑相关的代码通常是固定的，反而是这些“魔法常量”会经常性地改变。

为了避免频繁地修改我们的代码，我们使用订单（*order*）这一概念。通过将每次处理所需的参数按照.CONFIG的格式定义好——我们称之为 *订单模板*，后续的订单会自动按照该模板生成。通过填写相应的值来“告诉”application诸如任务ID、数据位置等必要的信息。一个常见的订单模板格式如下：

```
?cityscape/template.cfg
[meta]
keys = common,upload,export

[common]
name =
root = /path/to/data
relpath = extra/path/to/remove

[upload]
task_id = ?

[export]
title = 2017第?期图片标注任务
```

需要注意的是，订单模板的格式不是强制性的——只要能定义你的借口，你可以组织成任意格式！我们推荐使用如上的格式是希望即使在不同的app中也能复用同一个action（或者尽量少地去修改它），并且这种格式比较好地概括了我们日常工作中一个订单会用到的属性。

我们将上面的模板复制到 *cityscape/template.cfg* 文件中，然后在命令行中运行：

```python
$ python manage.py genconf -c trial.cfg
```

如果你是在Linux或macOS X平台上运行，并且已经安装了 *vim* 的话，那么此时会用vim的打开你刚才创建的 *cityscape/configs/trial.cfg* 已提供一个快速编辑的界面。

```
你可以通过在 tutorial/tutorial/settings.py 中设置EDITOR的值来使用你喜欢的文本编辑器——只要保证它能通过在命令行里指定文件名的方式打开即可。
此外，你还可以通过 editconf 命令快速打开一个订单文件，以对其进行修改。
```

我们在里面填上需要的值，并且对刚才编写的action *Upload* 进行修改：

```
?cityscape/configs/trial.cfg
[common]
root = /data/cityscape/vol1
relpath = /data/cityscape

[upload]
task_id = 10000
```

```python
# cityscape/actions.py
class Upload(actions.AbstractAction):

    def run(self, **kwargs):
        config = kwargs['config']
        task_id = config.upload['task_id']
        ···

        images = self.list_all_images(config.common['root'])
        ···
```

完成以上修改后，在命令行里运行（run）时通过指定订单文件名称就可以按照该订单的配置来执行——我们通过指定使用 *trail.cfg* 完成与上一节相同的功能：

```
$ python manage.py run cityscape -a upload -c trail.cfg
```

将 **action** 的接口独立出来之后我们发现，如之前期望的，很多动作是可以被复用的。我们也确实在 *moose.actions* 模块中定义了一些常见的动作，比如 *upload.SimpleUpload*, *upload.ReferredUpload*, *upload.MultipleUpload* 等等。我们查阅相应[API文档]()发现之前编写的 action: upload 已经被 *SimpleUpload* 实现了，只需要继承它并做些细微的调整即可。因此，我们的最终版本是这样的：

```python
# cityscape/actions.py
class Upload(actions.upload.SimpleUpload):
    default_pattern = "*.jpg"

```

### 抽象模型(model)，导出标注数据

现在标注人员已经完成了所有的标注，是时候将数据按照一定格式导出并交付客户了。类似于upload, 我们使用已经定义的 *actions.export.SimpleExport* 实现导出功能，但是查阅[API文档]()发现需要同时定义成员变量 *data_model*。

简单来说，*data_model* 就是一条标注数据（JSON字符串）的对象形式。

由于标注结果的格式通常不统一，并且项目内可能会因为需求或效率的变化而使用不同的模板，这导致产生的数据差异较大，功能难以被复用。因此，我们需要抽象出一层“适配器”的角色，通过定义并向其他对象暴露一系列统一的接口，其他对象只需要调用该接口，不用了解具体实现。同时，这些接口在子类中被继承和实现（或映射），不需要去关心这个接口将被用于做什么。

我们在 *moose.models.BaseModel* 中定义了最常见的接口，诸如：*filepath*、 *data*、*filelink(task_id)*、*is_effective()* 等等，有些提供了默认实现，另外一些则要求子类必须实现。他们具体的作用可以参考[API文档 model]()。现在，我们按如下：

```python
# cityscape/actions.py
class Export(actions.upload.SimpleExport):
    data_model = 'cityscape.models.CityscapeModel'

```

```python
# cityscape/models.py
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from moose import models
from moose.models import fields

# Create your models here.
class CityscapeModel(models.BaseModel):
    mark_result = fields.ResultMappingField(prop='markResult')

    @property
    def filepath(self):
        return self.source['url']

    @property
    def data(self):
        segmentations = []
        for geometry, properties in self.mark_result:
            segmentations.append({
                'category': properties['type']['currentDataKey'],
                'coordinates': geometry['coordinates'],
            })
        return segmentations

```
