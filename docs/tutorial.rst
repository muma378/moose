.. _tutorial:

快速上手教程
==========
在这篇教程中，我们假设你已经安装好了Moose并且了解一个数据标注项目的基本流程，如果还没有的话请参考**安装指南**和**标注任务创建指南**。

我们将以一个名为 **cityscape** 的图片标注项目开始(得益于各大厂商在自动驾驶研发上的投入，对街景图像的采集与标注的需求也变得旺盛)，该项目需要在[标注平台](http://bz.datatang.com/Admin/task/markList)上创建任务，上传图片数据并建立索引关系，待标注人员完成后，再将结果从后端提取出来，整理成相应格式并等待交付客户。

这篇教程将会着重讲述Moose相关的操作，包含以下要点：
1. 创建一个新的Moose项目；
2. 创建一个新的application;
3. 编写动作(action)：upload，完成数据上传和索引建立；
4. 创建订单(order)，定义动作接口；
5. 抽象模型(model)，导出标注数据；
6. 完成单元化测试。

创建一个Moose项目
---------------

在开始为一个数据标注（采集）项目编写相关的业务逻辑之前，我们需要创建一个Moose Project。在你想要保存代码的地方打开命令行，输入：::

    $ moose-admin startproject tutorial

这将会在当前文件夹中创建以下内容：::

    tutorial/
        tutorial/   # project's python module
            __init__.py     # an empty file tells Python that this directory should be considered as a package
            settings.py     # settings/configuration for this Moose project
            template.cfg    # global tasks' config template
        manage.py   # a command-line utility that let you interact with Moose in various ways


创建一个新的application
---------------------

现在，你的工作环境——Moose Project——已经创建起来，我们可以开始真正的工作了。
每一个你通过Moose编写的 **application** 都遵循一套特定的规则，他们既是Python的一个package，同时也是与一个“项目”——不同于前文提到的 *Moose Project*，这里指的是 **工程意义** 上的项目——相关的所有（代码层面上的）业务逻辑的集合。
Moose提供了一系列的工具来自动创建相应的文件和文件夹，使得开发者可以专注于编写业务逻辑的代码而不是创建文件。为了创建(一个名叫 *cityscape* 的) **app**，你需要在之前创建的Moose Project的目录下（在与 **manage.py** 同一级目录里）输入：::

    $ python manage.py startapp cityscape

这将会为你创建一个叫 **cityscape** 的文件夹，内部结构如下：::

    cityscape/
        configs/    # directory to put tasks' config files
        data/       # directory for input/output data
        __init__.py
        actions.py      # actions defined that application runs with
        apps.py         # control center to glue all components
        models.py       # object representation for data queried from the backend
        template.cfg    # local tasks' config template
        tests.py
