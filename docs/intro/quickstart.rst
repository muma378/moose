.. _intro-quickstart:

=====================
快速上手教程
=====================
在这篇教程中，我们假设你已经安装好了Moose并且了解一个数据标注项目的基本流程，如果还没有的话请参考 **安装指南** 和 **标注任务创建指南**。

我们将以一个名为 **cityscape** 的图片标注项目开始(得益于各大厂商在自动驾驶研发上的投入，对街景图像的采集与标注的需求也变得旺盛)，该项目需要在 `标注平台 <http://bz.datatang.com/Admin/task/markList>`_ 上创建任务，上传图片数据并建立索引关系，待标注人员完成后，再将结果从后端提取出来，整理成相应格式并等待交付客户。

这篇教程将会着重讲述Moose相关的操作，包含以下要点：

1. 创建一个新的Moose项目；
2. 创建一个新的application;
3. 编写动作(action)：upload，完成数据上传和索引建立；
4. 创建订单(order)，定义动作接口；
5. 抽象模型(model)，导出标注数据；
6. 完成单元化测试。

创建一个Moose项目
--------------------------


在开始为一个数据标注（采集）项目编写相关的业务逻辑之前，我们需要创建一个Moose Project。在你想要保存代码的地方打开命令行，输入： ::

    $ moose-admin startproject tutorial


这将会在当前文件夹中创建以下内容： ::


   tutorial/   # project's python module
       __init__.py     # an empty file tells Python that this directory should be considered as a package
       settings.py     # settings/configuration for this Moose project
       template.cfg    # global tasks' config template
       manage.py   # a command-line utility that let you interact with Moose in various ways


创建一个新的application
---------------------------
现在，你的工作环境——Moose Project——已经创建起来，我们可以开始真正的工作了。
每一个你通过Moose编写的 **application** 都遵循一套特定的规则，他们既是Python的一个package，同时也是与一个“项目”——不同于前文提到的 *Moose Project*，这里指的是 **工程意义** 上的项目——相关的所有（代码层面上的）业务逻辑的集合。
Moose提供了一系列的工具来自动创建相应的文件和文件夹，使得开发者可以专注于编写业务逻辑的代码而不是创建文件。为了创建(一个名叫 *cityscape* 的) **app**，你需要在之前创建的Moose Project的目录下（在与 **manage.py** 同一级目录里）输入： ::

    $ python manage.py startapp cityscape

这将会为你创建一个叫 **cityscape** 的文件夹，内部结构如下： ::

    cityscape/
        configs/    # directory to put tasks' config files
        data/       # directory for input/output data
        __init__.py
        actions.py      # actions defined that application runs with
        apps.py         # control center to glue all components
        models.py       # object representation for data queried from the backend
        template.cfg    # local tasks' config template
        tests.py


这其中尤其需要注意的是 *cityscape/apps.py* 。它是整个app的控制中心，负责连接各个单元和模块，使正确的配置文件（**configs**）被加载、动作（**actions**）能通过命令行被触发、数据被存储到正确的位置（**data**）。我们之后会了解到它是如何控制的，现在，你唯一需要做的是提供一些项目相关的信息：


.. code-block:: python
   :caption: cityscape/app.py
   :name: init-app-py

    # -*- coding: utf-8 -*-
    from moose.apps import AppConfig

    class CityscapeConfig(AppConfig):
        name = 'cityscape'
        verbose_name = u"街景道路标注"


编写动作(action)：upload，完成数据上传和索引建立
-----------------------------------------------------

项目很快开始运作起来，我们接到的第一个任务是创建一期标注任务，并且向我们提供了以下信息：

- 数据来源：*/data/cityscape/vol1* 目录下的所有图片
- 模板名称：*街景图片多边形标注 v1.1*
- 索引格式：

::

    {
        "url": "path/to/image01.jpg", "dataTitle": "image01.jpg"
    }

我们在这里不过多地解释这些信息代表的含义，如果你还不了解，请参考我们的文档 **《标注任务创建指南》** 。假设你已经根据这些信息在 `标注平台
<http://bz.datatang.com/Admin/task/markList>`_ 上创建了一期任务，并且返回了以下信息：

- 任务ID：*10000*
- 任务名称：*2017第2000期图片标注任务*
- 任务批次：*cityscape - vol1*

接下来要做的就是上传原始图片并且建立索引关系。这些动作被抽象成一个叫 **AbstractAction** 的类，我们在 *cityscape/actions.py* 定义它的实现：

.. code-block:: python
   :caption: cityscape/actions.py
   :name: upload-actions-py

    # -*- coding: utf-8 -*-
    import os
    import json
    from moose import actions
    from moose.connection.cloud import AzureBlobService
    from tutorial import settings

    class Upload(actions.base.BaseAction):

        def run(self, **kwargs):
            """
            Inherited classes must implement this interface,
            which will be called then to perform the operation.
            """
            task_id = '10000'

            # Phase 1. establishes the connection to azure and do uploading files
            azure = AzureBlobService(settings.AZURE)
            # Assume there was only one file in '/data/cityscape/vol1'.
            images = [('/data/cityscape/vol1/a.jpg', 'vol1/a.jpg'), ]
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
            return '{} files uploaded.' % len(blobs)


为了避免我们的教程陷入过多细节的讨论，我们跳过了部分具体实现，例如 *AzureBlobService* 类。目前你只需要了解：通过继承 **actions.base.BaseAction** 并对接口 **run** 添加实现，我们完成了原始文件的上传和索引文件的生成这两个功能。

为了使得这个 *Action* 可以在命令行里被调用，我们还需要做一件事情——在 *AppConfig* 中注册该动作。在 *cityscape/apps.py* 中添加以下内容：

.. code-block:: python
   :caption: cityscape/app.py
   :name: upload-app-py

    class CityscapeConfig(AppConfig):
        name = 'cityscape'
        verbose_name = u"街景道路标注"

        def ready(self):
            self.register('Upload', 'upload')   # now we can type `-a upload` to refer the action 'cityscape.actions.Upload'


注册完成之后，我们就可以在命令行中通过指定 *-a upload* 选项来运行我们之前在 *cityscape.actions.Upload* 中编写的代码了。在'cityscape/configs/'下创建一个文件叫"placeholder.cfg", 我们在其中输入以下内容：

.. code-block:: guess
   :caption: cityscape/configs/placeholder.cfg
   :name: placeholder-cfg-1

    [meta]
    keys = upload

    [upload]

然后在与之前相同的位置下输入： ::

    $ python manage.py run cityscape -a upload -c placeholder.cfg

此时，你应该可以在命令行中看见文件上传的进度条，以及生成的 *cityscape/data/10000.json* 文件了。至于我们手动创建的 *placeholder.cfg* 是起什么作用，我们会在下一节中进行详细说明。

创建订单(order)，定义动作接口
--------------------------------

如果你是一位有经验的开发者，那么你一定已经意识到我们之前的代码中存在一点问题——包含过多的“魔法常量”（*magic constant*），不仅如此，在实际的工作中我们还会发现，那些业务逻辑相关的代码通常是固定的，反而是这些“魔法常量”会经常性地改变。

为了避免频繁地修改我们的代码，我们提出订单（*order*）这一术语（terminology）。通过将每次处理所需的参数按照.CONFIG的格式定义好——我们称之为 *订单模板*，后续的订单会自动按照该模板生成。通过填写相应的内容来“告诉”application诸如任务ID、数据位置等必要的信息。一个常见的订单模板格式如下：

.. code-block:: guess
   :caption: cityscape/template.cfg
   :name: template-cfg

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


需要注意的是，订单模板的格式不是强制性的——只要能定义你的借口，你可以组织成任意格式！我们推荐使用如上的格式是希望即使在不同的app中也能复用同一个action（或者尽量少地去修改它），并且这种格式比较好地概括了我们日常工作中一个订单会用到的属性。

我们将上面的模板复制到 *cityscape/template.cfg* 文件中，然后在命令行中运行： ::

    $ python manage.py genconf cityscape -c trial.cfg

如果你是在Linux或macOS X平台上运行，并且已经安装了 *vim* 的话，那么此时会用vim的打开你刚才创建的 *cityscape/configs/trial.cfg* 已提供一个快速编辑的界面。

    你可以通过在 tutorial/tutorial/settings.py 中设置EDITOR的值来使用你喜欢的文本编辑器——只要保证它能通过在命令行里指定文件名的方式打开。
    此外，你还可以通过 editconf 命令快速打开一个订单文件，以对其进行修改。

我们在里面填上需要的值，并且对刚才编写的action *Upload* 进行修改：

.. code-block:: guess
   :caption: cityscape/configs/trial.cfg
   :name: trial-cfg

    [common]
    root = /data/cityscape/vol1
    relpath = /data/cityscape

    [upload]
    task_id = 10000

    [export]
    title = 2017第2000期图片标注任务


.. code-block:: python
   :caption: cityscape/actions.py
   :name: order-actions-py-1

    class Upload(actions.base.BaseAction):

        def run(self, **kwargs):
            config = kwargs['config']
            task_id = config.upload['task_id']
            # ···

            images = [('/data/cityscape/vol1/a.jpg', 'vol1/a.jpg'), ]
            # ···

完成以上修改后，在命令行里运行（run）时通过指定订单文件名就可以按照该订单的配置来执行——我们通过指定使用 *trial.cfg* 完成与上一节相同的功能： ::

    $ python manage.py run cityscape -a upload -c trial.cfg

将 **action** 的接口独立出来之后我们发现，如之前期望的，很多动作可以被复用。我们也确实在 *moose.actions* 模块中定义了一些常见的动作，比如 *upload.SimpleUpload*, *upload.ReferredUpload*, *upload.MultipleUpload* 等等。通过查阅相应的[API文档]()发现之前编写的 action: upload 已经被 *SimpleUpload* 实现了，只需要继承它并做些细微的调整即可。因此，我们的最终版本是这样的：

.. code-block:: python
   :caption: cityscape/actions.py
   :name: order-actions-py-2

    class Upload(actions.upload.SimpleUpload):
        default_pattern = "*.jpg"


抽象模型(model)，导出标注数据
---------------------------------

现在标注人员已经完成了所有的标注，是时候将数据按照一定格式导出并交付客户了。类似于upload, 我们使用已经定义的 *actions.export.SimpleExport* 实现导出功能，但是查阅[API文档]()发现需要同时定义成员变量 *data_model*。

简单来说，**data_model** 就是一条原本是JSON字符串的标注数据的对象形式。

由于标注结果的格式通常不统一，并且项目内可能会因为需求或效率的变化而使用不同的模板，这导致产生的数据差异较大，功能难以被复用。因此，我们需要抽象出一层“适配器”的角色，通过定义并向其他对象暴露一系列统一的接口，其他对象只需要调用该接口，不用了解具体实现。同时，这些接口在子类中被继承和实现（或映射），不需要去关心这个接口将被用于做什么。

我们在 **moose.models.BaseModel** 中定义了一些常见的接口，诸如：*filepath*、 *data*、*filelink(task_id)*、*is_effective()* 等等，有些提供了默认实现，另外一些则要求子类必须实现。他们具体的作用可以参考[API文档 model]()。现在，我们输入以下内容：

.. code-block:: python
   :caption: cityscape/actions.py
   :name: model-actions-py

    class Export(actions.export.SimpleExport):
        data_model = 'cityscape.models.CityscapeModel'

.. code-block:: python
   :caption: cityscape/models.py
   :name: model-model-py

    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals
    from moose import models
    from moose.models import fields

    # Create your models here.
    class CityscapeModel(models.BaseModel):
        mark_result = fields.ResultMappingField(prop_name='markResult')

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


我们解释一下其中的设计要点：

- 与 *SimpleUpload* 相似, *actions.export.SimpleExport* 控制整个（导出）动作的流程，包括 **从数据库中提取标注数据 => 加载数据以实例化Model  => 调用实例化后的接口，对标准化后的数据进行处理**；
- *BaseExport.query_class* 定义了查询类，通过继承 *connection.query.BaseQuery* 实现自定义查询——也就是说 **当查询条件发生了变化** 才需要进行修改；
- *BaseExport.query_context* 定义了数据库使用的驱动类（*\*_handler*）和表实际名称到查询类中使用的别名的映射（*\*_context*）——也就是说只有 **当使用的数据库发生了变化** 才需要修改；
- 每条标注数据以 *{'source': {'url': ''}, 'result': {'markResult': ''}}* 的格式返回，其中，顶层的字段 *source* 和 *result* 分别对应数据库中的表示该数据 **原始信息和标注信息** 的两张表，它们的子字段则可能随模板不同而变化；
- 为了方便接下来对标注结果中 *annotation['result']['markResult']* 的调用，*CityscapeModel* 通过声明 *mark_result = fields.ResultMappingField(prop='markResult')* 完成了 **字典的键值到类的属性的映射**；
- *cityscape.models.CityscapeModel* 继承 *models.BaseModel* 并实现了接口 *data* 以提供一个 **可读性更好的数据格式**，这个接口随后会被 *SimpleExport* 的 *dump()* 调用以将其写至文本文件中，完成我们所谓的导出功能。

基于原始数据和处理数据分离的原则设计，即使中途更换了模板，我们也只需新建一个 *NewCityscapeModel* 提供同样的标准化接口（如 *data* ），并修改 *data_model = 'cityscape.models.NewCityscapeModel'* 即可。

之后，同 **Upload** 一样，当我们在 `app` 中对该Action进行注册：

.. code-block:: python
   :caption: cityscape/app.py
   :name: model-app-py
   :emphasize-lines: 7

    class CityscapeConfig(AppConfig):
        name = 'cityscape'
        verbose_name = u"街景道路标注"

        def ready(self):
            self.register('Upload', 'upload')
            self.register('Export', 'export')   # Same as upload, now we can type `-a export`


此时，我们在命令行中输入： ::

    $ python manage.py run cityscape -a export -c trial.cfg

即可完成导出标注结果。

接下来......
---------------

到这里，你就已经掌握了Moose最核心的思想和内容，其他的特性和内容万变不离其宗，基本上都是在这层设计思想上不断细化和完善的结果。这听起来似乎剩下的内容都不重要，然而，正像我们设计Moose的初衷是为了最大化的复用代码、节省时间，其他的模块和语法糖也是基于同样的目的。所以，去探索下这些功能吧，你了解的模块和特性越多，你将来所花费的时间也会越少。因为很有可能你碰到的问题，其他人已经碰到过了。
