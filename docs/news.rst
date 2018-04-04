.. _news:

Release notes
=============

Moose 0.9.6Beta (2018-04-04)
-----------------------------
* 添加了文档中 `example.rst` 的部分;
* 修改了 `Model` 的初始化参数，默认传入关键字参数 `**context` 作为上下文环境；
* 解决了在windows环境下使用python3安装Moose会失败的bug；


Moose 0.9.5Beta (2018-03-13)
-----------------------------
* 移除了对 `azure>=2.0.0rc` 的依赖，改为对 `azure-storage-blob>=1.1.0` 依赖；
* 添加了 `action.upload.VideosUpload` 以支持对视频拆帧的图片的通用上传；
* 添加了 `process.video` 模块，增加对视频的处理；


Moose 0.9.3Beta (2017-12-29)
-----------------------------
* 由于 MySQLdb_ 在Windows和Mac OSX上安装经常失败导致Moose安装中断，因此我们移除了对 MySQLdb_ 和 pysmb_ 的依赖声明。依赖这两个包的模块依然存在，但由于使用较少基本不会造成较大影响，但如果需要时请尝试手动安装。


Moose 0.9.0Beta (2017-12-06)
-----------------------------

作为发布的第一个版本，Moose提供了基本核心的功能，包括：

* 创建项目（project）和应用（app）；
* 生成和编辑订单（order）；
* 运行App；
* 抽象了常用的连接；
* 内置常见的行为类；


.. _MySQLdb: https://mysqlclient.readthedocs.io/
.. _pysmb: https://pysmb.readthedocs.io/
