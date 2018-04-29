.. _topics-business:

================
业务逻辑
================

Moose 提供了一系列的动作（action）支撑我们的日常工作，其中最常使用的就是上传 ``upload`` 和导出 ``export`` 了。这一节中我们着重解释这两类任务背后的工作原理，以期帮助大家理解在诸多的upload和export类中共通的流程。


上传（upload）
=================

.. image:: /.static/upload-overview.png

如上图所示，上传过程包含以下步骤：

1. 将想要标注的文件由本地上传到 `Azure Blob Storage`_ ，我们提供了 :doc:`/topics/connections` 模块帮助用户通过几行代码完成上传。(微软官方同样提供了教程解释如何使用 ``blob``，其中除了 `Python SDK`_ 外，还包括了一系列其他的方法)；
2. 将已上传的文件列表按照标注模板需要的格式进行组织，形成索引文件。索引文件提供了被标注对象的相关信息——如存储路径、文件标题、音频内容、音频时长等；
3. 利用平台的接口导入索引文件。后台通过解析索引文件，在数据库中插入相关信息；
4. 标注人员开始标注。这一过程将会首先从后台提取相应信息，前端页面解析后加载并从 ``blob`` 中提取原始文件。

需要注意的是，为了方便处理，我们定义了一套惯例：针对每一期任务都有一个唯一的 ``task ID`` ，这个 ``task ID`` 既对应着标注平台上手动创建的一期任务，也对应着后台MongoDB中存储该期索引和标注信息的一个 ``collection`` 的名称 ，同时也是 ``blob`` 中存储该期标注文件的容器名。
因此索引文件中，如果我们只记录文件在容器中的名称（意即 `myblob` 而非 `http://myaccount.blob.core.chinacloudapi.cn/mycontainer/myblob` 这样的全称），系统会自动使用对应 `task ID` 的账号和容器来扩展url。

导出（export）
=================

.. image:: /.static/export-overview.png




.. _Azure Blob Storage: https://docs.azure.cn/zh-cn/storage/blobs/storage-blobs-introduction
.. _Python SDK: https://docs.azure.cn/zh-cn/storage/blobs/storage-quickstart-blobs-python
