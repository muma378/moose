.. _topics-models:

=================
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

    BaseSQLHandler是所有关系型数据库操作接口类的基类,它定义了Handler子类应该包含的属性、需要实现的接口并且为通用方法提供了默认实现。

    :param dict settings_dict: 包含数据配置的字典。
    :param str host: 要连接的数据库的主机地址
    :param object conn:  连接对象
		
    .. method:: __del__()
		
		该方法主要是用来断开数据库的连接。

    .. method:: __connect()

        该方法是用来通过调用get_connection函数进行数据的连接操作的，如果连接成功返回连接对象，如果没有连接成功或者连接超过指定的次数则抛出错误。
		
    .. method:: get_connection()

        该方法是预留的接口函数，子类必须实现，子类可以根据要连接的数据库类型的不同进行设置并连接。

    .. method:: close()

        该方法主要是用来断开数据库的连接并重置连接和游标。
	
    .. method:: connect()

        该方法是调用__connect()实现连接功能，并实现对于连接请求的间断化处理，保证返回可靠的连接。

    .. method:: exec_query(sql_query)

    	:param str sql_query: sql查询语句。

        该方法用来根据输入的sql执行查询操作，首先判断执行输入的sql是否合法以及连接是否正常，如果都满足条件则执行该条sql语句。

    .. method:: exec_commit(sql_commit)
		
		:param str sql_commit: sql增删改语句。
		
		该方法用来根据输入的sql执行增删改操作，首先判断执行输入的sql是否合法以及连接是否正常，如果都满足条件则执行该条sql语句。

    .. method:: exec_many()	
		
		该方法是预留接口函数，用来批量执行增删改sql语句，子类可根据自行实现。