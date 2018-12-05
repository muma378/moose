.. _intro-install:

==============
安装指南
==============

Moose 运行在Python 2.7和Python 3.3及以上版本。

安装发布版
---------------------

这是较为推荐的安装方法：

1. 安装pip。最简单的方法是使用 pip_ 安装脚本。如果你的Python发布版已经安装了pip，你可能需要更新以避免由于版本过老导致安装失败。
2. 了解 virtualenv_ 或 virtualenvwrapper_ 并安装教程。这些工具提供了一个独立的Python环境，相比在全局范围内安装包要更加有效且实用，并且不需要管理员权限。
3. 安装并且激活虚拟环境后，在命令提示符中输入 **pip install Moose**。

安装开发者版本
---------------------

如果你希望安装最新版本的Moose，可以通过以下教程来尝试：

1. 确认你已安装Git并且可以从命令行中访问。
2. 获取Moose的主分支代码：::

    $ git clone https://github.com/muma378/moose.git

   这会为你在当前目录下创建一个名为 **moose** 文件夹。
3. 确认你的Python解释器可以加载Moose代码。最常见的办法是使用 virtualenv_， virtualenvwrapper_ 和 pip_ 。
4. 在安装和激活virtualenv之后，运行以下命令：::

    $ pip install -e moose/

   现在，Moose的代码就可以被导入（importable），并且可以使用 **moose-admin** 等命令行工具了。至此，我们就完成了安装！

当你想要更新你的Moose代码时，只需要在moose文件夹内运行命令 **git pull**，Git便会自动下载任何更新。

需要知道的事情
---------------------

Moose完全由Python编写并且依赖于以下几个关键的Python包（Packages）：

* azure_，微软 Azure云服务的SDK的Python版本；
* pymongo_，包含多个通过Python与MongoDB交互的工具；
* pymssql_，一个基于Python DB-API (`PEP-249 <http://www.python.org/dev/peps/pep-0249/>`_)的访问SQLServer数据库的接口；
* MySQLdb_，一个提供了访问MySQL数据库的线程兼容的Python库；
* OpenCV_，经典图像处理库OpenCV的Python版本；
* Pillow_，一个友好的Python图像库，提供了更直白的图像处理函数；

.. _virtualenv: https://virtualenv.pypa.io
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/install.html
.. _user guide: https://virtualenv.pypa.io/en/stable/userguide/
.. _pip: https://pip.pypa.io/en/latest/installing/
.. _azure: https://azure-storage.readthedocs.io/
.. _pymongo: https://dfproj.readthedocs.io/en/latest/
.. _pymssql: http://pymssql.org/en/stable/
.. _MySQLdb: https://mysqlclient.readthedocs.io/
.. _OpenCV: http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_tutorials.html
.. _Pillow: http://pillow.readthedocs.io/en/stable/
