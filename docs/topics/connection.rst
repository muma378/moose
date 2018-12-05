.. _topics-connection:

=======================
连接（Connection）
=======================

*Moose* 不是一个孤立的系统，文件和数据通过各种现有的服务提供——关系/非关系型数据库、文件系统、
云存储服务等等，我们要进行处理就必须提供“港口和桥梁”，将数据接入进来。 *connection*
模块就是被用来处理这样的任务。

对于关系型数据库，无论底层的引擎是mysql还是sqlserver， :doc:`sqlhandler` 模块为所有的操作
提供了一个统一的接口； 除此之外， :doc:`operations` 则基于这层抽象提供了便捷的sql操作接口，
使得数据库查询、插入、修改等操作更加方便；相应的，我们用 :doc:`mongodb` 模块封装了 `pymongo`，
为对于Mongodb的操作提供了一层易用性更强的接口；

而对于微软的云存储服务 `Azure blob`_ ，微软提供了python的 `azure SDK`_ ，:doc:`azure`
模块则是基于该SDK的封装，进一步封装了Azure操作的常用接口。

.. toctree::
   :caption: 模块
   :hidden:

   sqlhandler
   operations
   mongodb
   azure

:doc:`sqlhandler`
   sql连接的处理类，用来管理sql连接，抽象底层实现，提供统一接口。

:doc:`operations`
   基于 :doc:`sqlhandler` 的sql操作的快捷方式。

:doc:`mongodb`
   Mongodb连接的处理类，提供了基于 `pymongo` 封装后更加易用的接口。

:doc:`azure`
   提供了Azure Blob服务的操作接口，用于完成文件的上传和下载。

.. _Azure Blob: https://azure.microsoft.com/en-us/services/storage/blobs/
.. _azure SDK: https://azure-storage.readthedocs.io/
