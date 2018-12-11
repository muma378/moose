.. _topics-conn-azure:

=============================
Azure Blob连接
=============================

.. _topics-conn-azure_blob_service

moose.connection.cloud
=========================================

.. class:: moose.connection.cloud.AzureBlobService(settings_dict)

	该类实现对 ``Azure`` 云数据库的封装，对输入参数进行异常处理等操作保证程序的稳定性，对外提供统一的接口，不同用户只需提供不同的配置参数即可连接服务进行创建容器及其内部blob对象的操作。

    :param dict settings_dict: 包含数据库配置的字典。包含数据配置的字典，包含如 ``ACCOUNT`` （用户名），``KEY`` （连接密钥），``ENDPOINT`` （连接站点） ， ``TIMEOUT`` （超时时间）。

    .. attribute:: blob_pattern = 'http://([\\w\\.]+)/(\\w+)/(.*)'

		定义 ``blob`` 的格式

    .. method:: create_container(container_name，set_public=False)

		:param str container_name: 容器名称
		:param bool set_public: 用来设置权限是否支持公共访问

		该方法根据输入的参数 ``set_public`` 设置访问权限，返回名为 ``container_name`` 的容器对象，如果已经该容器已存在则不再返回。

    .. method:: list_containers(prefix=None)

		:param str prefix: 容器名称的前缀，用来过滤只返回容器名称以指定前缀开头的容器，默认为None即返回所有容器。

		该方法返回一个列表，列出指定帐户下的容器。

    .. method:: list_blobs(container_name，prefix=None, suffix=None)

		:param str container_name: 容器名称
		:param str prefix: ``blobname`` 的前缀，用来过滤只返回容器名称以指定前缀开头的 ``blobname`` ，默认为None即返回所有 ``blobname`` 。
		:param str suffix: ``blobname`` 的后缀，用来过滤只返回容器名称以指定后缀结尾的 ``blobname`` ，默认为None即返回所有 ``blobname`` 。

		该方法根据blobname的前缀或后缀进行筛选后列出容器上的所有blobname的列表，返回的blob_names是posix样式的路径，无论创建时名称是什么。

    .. method:: create_blob_from_path(container_name, blob_name, filepath)

		:param str container_name: 容器名称
		:param str blob_name: blob名称
		:param str filepath: 要上传文件的路径

		该方法根据参数 ``filepath`` 上传文件到容器中，生成带有属性和元数据的 ``Blob`` 实例

    .. method:: upload(container_name, blob_pairs, overwrite=False)

		:param str container_name: 容器名称
		:param str blob_pairs: 一个包含 ``blob_name`` 和blob对象文件的本地路径的元祖
		:param bool overwrite: 定义是否覆盖原 ``blob对象``

		该方法首先判断容器是否存在，如果不存在则创建容器，然后根据参数 ``overwrite`` 判断上传是否覆盖容器中的原文件，返回包含bolbname的列表

    .. method:: get_blob_to_path(container_name, blob_name, filepath)

		:param str container_name: 容器名称
		:param str blob_name: blob名称
		:param str filepath: 要上传文件的路径

		该方法是从容器 ``container_name`` 中下指定blob对象 ``blob_name`` 到指定的地址 ``filepath`` 。

    .. method:: download(container_name, dest, blob_names=None)

		:param str container_name: 容器名称
		:param str dest: 下载目标地址
		:param list blob_names: 包含blobname的列表

		该方法返回从容器中获取的blob对象到指定的目标地址，如果参数 ``blobnames`` 为None,则下载container中的所有blob对象

    .. method:: get_blob_to_text(container_name, blob_name)

		预留接口

    .. method:: get_blobs(container_name, blob_names=None)

		预留接口

    .. method:: set_container_acl(container_name, set_public=True)

		:param str container_name: 容器名称
		:param bool set_public: 用来设置权限是否支持公共访问

		该方法实现设置与共享访问签名一起使用的指定容器或存储访问策略的权限。权限指示容器中的blob是否可以公开访问

    .. method:: delete_blobs(container_name, blob_names)

		:param str container_name: 容器名称
		:param list blob_names: blob对象名称列表

		该方法执行从指定容器删除指定的 ``blob`` 对象,返回包含被删除的blob对象名称的列表

    .. method:: copy_blobs(blob_names, container_name, src_container=None, pattern=None)

		:param list blob_names: blob对象名称列表
		:param str container_name: 要复制的目标容器名称
		:param str src_container: 	数据源容器名称
		:param str pattern: 匹配 ``blob`` 对象名称的模式

		该方法实现将blob_names中列出的blob对象复制到dest容器，如果给定 ``src_container`` 则 ``blob_names`` 可以作为容器的相对路径，如果没有给定 ``blob_names`` 则按照匹配模式复制到目标容器中，如果blob_names为None则复制全部


    .. method:: copy_container(src_container, dst_container, pattern=None)

		:param str src_container: 源容器名称
		:param str dst_container: 目标容器名称
		:param str pattern: 匹配 ``blob`` 对象名称的模式

		该方法按照指定匹配模式复制blob对象到目标容器，如果目标容器不存在则在复制前创建该容器
