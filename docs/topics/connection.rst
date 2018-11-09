.. _topics-connection:

=======================
连接（Connection）
=======================

*Moose* 不是一个孤立的系统，文件和数据通过各种现有的服务提供——关系/非关系型数据库、文件系统、云
存储服务等等，我们要进行处理就必须提供“港口和桥梁”，将数据接入进来。*connection* 模块就是被用
来处理这样的任务。

:doc:`sqlhandler` 为所有的关系型数据库提供了一个统一的接口，无论底层的引擎是mysql还是
sqlserver； :doc:`operations` 则基于这层抽象提供了便捷的sql操作接口，使得数据库操作更
加方便； 相应的， :doc:`mongodb` 封装了`pymongo`，为对于Mongodb的操作提供了一层易用性
更强的接口； :doc:`azure` 则提供了对微软Azure blob存储服务的操作接口。

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
