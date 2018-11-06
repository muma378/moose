.. _topics-models:

===================
连接器（Connection）
=================

数据处理顾名思义处理的是数据，而数据往往都存放在数据库中，我们要对数据进行操作就需要连接人与数据库的工具--连接器，然而要连接的对象往往都是不同的，一种连接器往往很难适应多种需求，这里我们就需要对那些具

有共性的接口进行抽象出来。如 ``BaseSQLHandler`` 作为关系型数据库接口类的基类， ``MongoDBhandler`` 作为MongoDB(非关系型数据库接口类的基类)， ``BaseOperation`` 

作为执行具体数据操作的基类，开发人员在通过数据库操作数据时，只需要通过继承基类重写某个连接方法实现即可。类似于经典的MVC模式通过控制器（Controller）解耦模型（Model）和视图（View），我们通过抽象出Model

对象来适配不同的数据格式，使得在其上的各种动作（Action）可以使用相同的接口。我们会在接下来的一节讲述该模块的接口。

.. module:: moose.models
   :synopsis: Models base class and common interfaces, fields class.

.. _topics-models-ref:

moose.connection.BaseSQLHandler
=================================

.. class:: moose.connection.sqlhandler.BaseSQLHandler(settings_dict,host,conn)

    BaseSQLHandler为其子类提供一些通用的方法和接口，实现最基础的连接功能，子类根据需求可在其基础上进行扩展。

    :param dict settings_dict: 包含数据配置的字典，包含如 ``HOST`` （要连接的数据库的主机地址），``PORT`` （端口），``USER`` （用户名） ， ``PASSWORD`` （用户密码） 以及 ``CHARSET`` （编码方式），如果需要给数据表起别名还可能包括 ``TABLE_ALIAS`` （给数据表起别名）。
		
    .. method:: __del__()
		
		该方法主要是用来断开数据库的连接。

    .. method:: __connect(settings_dict)

        该方法是预留的接口函数，子类必须实现，子类可以根据要连接的数据库类型的不同进行设置并连接，该方法返回数据库连接对象。
		
    .. method:: get_connection(settings_dict)

        该方法用来判断数据库配置信息是否正确及实现限制重试次数和增加重试间隔时间，如果连接成功则调用 ``_connect()`` 方法返回连接对象，否则抛错。

    .. method:: close()

        该方法首先判断数据库是否断开，若断开则重置连接和游标，否则抛错。

    .. method:: _close()

        该方法定义关闭数据库连接。

    .. method:: _get_cursor()

        该方法返回该连接对象的游标。
	
    .. method:: execute(operation, operator, *args)

        :param str operation: sql语句。
        :param funtion operator: 真正执行sql操作的函数体，该参数根据调用该方法的主体不同而实现不同的功能。
        :param str args: sql语句参数。

        该方法对sql语句进行判断，若存在，则获取该连接的游 标及sql语句模板并传入的函数体 ``operator`` 返回执行结果。

    .. method:: exec_query(operation)

    	:param str operation: sql查询语句。

        ::

            def _operator(cursor, operation, *args):
                cursor.execute(operation)
                result = cursor.fetchall()
                return result

        该方法用来根据输入的sql语句及内部 ``operator`` 函数作为参数调用excute()方法执行查询操作。

    .. method:: exec_commit(operation)
		
		:param str operation: sql增删改语句。

        ::

            def _operator(cursor, operation, *args):
                cursor.execute(operation)
                self._conn.commit()
                naffected = cursor.rowcount
                stdout.info("Operation completed with '{}' rows affected.".format(naffected))
                return naffected
		
		该方法用来根据输入的sql语句及内部 ``operator`` 函数作为参数调用excute()方法执行增删改操作。

    .. method:: exec_many(operation, params_seq)

        :param str operation: sql增删改语句。
        :param str params_seq: 参数列表。	
		
        该方法是预留接口函数，用来批量执行增删改sql语句，子类可根据具体需求自行实现。