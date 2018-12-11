.. _topics-conn-sqlhandler:

===================
SQL连接
===================


.. _topics-conn-basehandler:

moose.connection.sqlhander
==============================

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


.. _topics-conn-sqlserver:

moose.connection.mssql
==================================

操作关系型数据库 ``SQLServer`` 我们通常有两种方式即 ``pymssql`` 和 ``_mssql`` ，``pymssql`` 是在 ``_mssql`` 上作了封装,是为了遵守python的DBAPI规范接口，查询时通常都使用 ``pymssql`` 但其在执行增删改操作时会抛错，所以使用相对原生的 ``_mssql``。

.. class:: SQLServerHandler(BaseSQLHandler)

	SQLServerHandler是BaseSQLHandler的子类，它定义了基于BaseShape类的在SQLServer数据中的实现，这里一般用来进行查询操作。

	.. attribute:: db_name = 'SQLServer'

		定义该数据库名称为 ``SQLServer``

	.. method:: _connect(settings_dict)

		:param dict settings_dict: 包含数据配置的字典，包含如 ``HOST`` （要连接的数据库的主机地址），``PORT`` （端口），``USER`` （用户名） ， ``PASSWORD`` （用户密码） 以及 ``CHARSET`` （编码方式），如果需要给数据表起别名还可能包括 ``TABLE_ALIAS`` （给数据表起别名）。

		该方法根据输入的数据库配置返回SQLServer数据库的连接对象。

	.. method:: exec_many(operation, params_seq)

		:param str operation: 要执行的sql语句模板
		:param str params_seq: 要执行的sql语句参数

		::

			def _operator(cursor, operation, *args):
				if len(args) == 1:
					params_seq = args[0]
				else:
					raise SuspiciousOperation
				# see ref: http://pymssql.org/en/stable/pymssql_examples.html
				cursor.executemany(operation, params_seq)
				self._conn.commit()
				naffected = cursor.rowcount
				stdout.info("Operation completed with '{}' rows affected.".format(naffected))
				return naffected


		该方法根据输入的模板、参数及内部函数 ``_operator`` 作为参数调用 ``excute()方法`` 批量操作数据库的操作，返回执行结果


.. class:: PrimitiveMssqlHandler(BaseShape)

	在执行插入、更新或删除操作时，使用基本的mssql而不是 ``SQLServerHandler`` 。

	.. attribute:: db_name = '_mssql'

		定义该数据库名称为 ``_mssql``

	.. method:: _connect(settings_dict)

		:param dict settings_dict: 包含数据配置的字典，包含如 ``HOST`` （要连接的数据库的主机地址），``PORT`` （端口），``USER`` （用户名） ， ``PASSWORD`` （用户密码） 以及 ``CHARSET`` （编码方式），如果需要给数据表起别名还可能包括 ``TABLE_ALIAS`` （给数据表起别名）。

		该方法根据输入的数据库配置返回SQLServer数据库的连接对象。

	.. method:: _get_cursor()

		返回位None的游标，与其他数据库驱动程序不同的是，``_mssql`` 执行没有游标的操作。

	.. method:: exec_query(operation)

		:param str operation: 要执行的sql查询语句模板

		::

			def _operator(cursor, operation, *args):
				result = self._conn.execute_query(operation)
				return result

		该方法根据输入的查询sql语句模板及差异化的内部函数体 ``_operator`` 作为参数调用 ``excute()`` 执行数据库查询操作，返回执行结果

	.. method:: exec_commit(operation)

		:param str operation: 要执行的sql增删改语句模板

		::

			def _operator(cursor, operation, *args):
				self._conn.execute_non_query(operation)
				naffected = self._conn.rows_affected
				stdout.info("Operation completed with '{}' rows affected.".format(naffected))
				return naffected

		该方法根据输入的查询sql语句模板及差异化的内部函数体 ``_operator`` 作为参数调用 ``excute()`` 执行数据库增删改操作，返回执行结果



moose.connection.mysql
=============================

.. class:: MySQLHandler(BaseSQLHandler)

	MySQLHandler是BaseSQLHandler的子类，它定义了基于BaseSQLHandler类的在MySQL数据中的实现。

	.. attribute:: db_name = 'MySQL'

		定义该数据库名称为 ``MySQL``

	.. method:: _connect(settings_dict)

		:param dict settings_dict: 包含数据配置的字典，包含如 ``HOST`` （要连接的数据库的主机地址），``PORT`` （端口），``USER`` （用户名） ， ``PASSWORD`` （用户密码） 以及 ``CHARSET`` （编码方式），如果需要给数据表起别名还可能包括 ``TABLE_ALIAS`` （给数据表起别名）。

		该方法根据输入的数据库配置返回MySQL数据库的连接对象。
