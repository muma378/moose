.. _topics-conn-mongodb:

===================
MongoDB连接
===================

.. class:: MongoDBHandler(settings_dict,displayed_mongo_url,_client,_db_name,_db,_coll_name,_coll)

	该类实现对MongoDB数据库提供一个对外接口类，其内部封装了数据库的常用操作，用户只要按需传入指定参数即可实现功能。

    :param dict settings_dict: 包含数据配置的字典。包含数据配置的字典，包含如 ``HOST`` （要连接的数据库的主机地址），``PORT`` （端口），``USER`` （用户名） ， ``PASSWORD`` （用户密码）

    .. attribute:: coll_source = 'Source'

		定义原始数据表名称

    .. attribute:: coll_result = 'Result'

		定义结果（标注后）数据表名称

    .. method:: __del__()

		该方法实现断开数据库连接

    .. method:: __connect()

		该方法通过调用 ``__get_mongo_url`` 得到数据库地址来实现数据连接，返回MongoDB客户端对象

    .. method:: __get_mongo_url(settings_dict)

		:param dict settings_dict: 数据库配置信息

		该方法通过输入的数据配置参数返回数据库连接url

    .. method:: __get_displayed_url(settings_dict)

		:param dict settings_dict: 数据库配置信息

		该方法返回一个将用户密码注释的数据库连接地址

    .. method:: db()

		``@property``

		该方法返回数据库对象，如果不存在则报错

    .. method:: set_database(db_name)

		:param str db_name: 数据库名称

		该方法用来新建数据库及设置数据库名称

    .. method:: coll()

		``@property``

		该方法返回数据表对象，如果不存在则报错

    .. method:: set_collection(coll_name)

		:param str coll_name: 数据表名称

		该方法用来新建数据表及设置数据表名称

    .. method:: execute(coll_name,operator)

		:param str coll_name: 数据表名称
		:param function operator: 执行sql操作函数的函数体

		该方法根据输入的数据表名称创建数据表并调用主体的内部函数体 ``_operator`` 执行数据库操作，返回执行结果，若尝试重连次数超过指定次数则抛错。

    .. method:: fetch(coll_name, filter=None, *args, **kwargs)

		:param str coll_name: 数据表名称
		:param dict filter: 条件字段
		:param str args: 位置参数
		:param dict kwargs: 关键字参数

		::

			def _operator():
				documents = []
				for doc in self.coll.find(filter, *args, **kwargs):
				    documents.append(doc)
				return documents

		该方法将其内部函数体 ``_operator()`` 及传入的数据表名称作为参数，调用方法 ``excute()`` 实现从数据库拉取数据的操作

    .. method:: fetch_source(filter=None, *args, **kwargs)

		:param dict filter: 条件字段
		:param str args: 位置参数
		:param dict kwargs: 关键字参数

		该方法调用 ``fetch`` 返回指定表 ``coll_source`` 的表中查询指定的filter字段的结果

    .. method:: fetch_result(filter=None, *args, **kwargs)

		:param dict filter: 条件字段
		:param str args: 位置参数
		:param dict kwargs: 关键字参数

		该方法调用 ``fetch`` 返回指定表 ``coll_result`` 的表中查询指定的filter字段的结果

    .. method:: insert(coll_name,documents, **kwargs)

		:param str coll_name: 数据表名称
		:param dic documents: 要写入数据表的数据
		:param dict kwargs: 关键字参数

		::

			def _operator():
				return self.coll.insert_many(documents, **kwargs)

		该方法将其内部函数体 ``_operator()`` 及传入的数据表名称作为参数，调用方法 ``excute()`` 实现数据库的批量写入操作。

    .. method:: update(coll_name，filter,documents, **kwargs)

		:param str coll_name: 数据表名称
		:param dict filter: 条件字段
		:param dic documents: 要写入数据表的数据
		:param dict kwargs: 关键字参数

		::

			def _operator():
				return self.coll.update_many(filter,{'$set': document},**kwargs)

		该方法将其内部函数体 ``_operator()`` 及传入的数据表名称作为参数，调用方法 ``excute()`` 实现数据库指定字段的批量更新操作。

    .. method:: close()

		该方法实现断开数据库连接的操作
