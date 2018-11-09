===============================
moose.connection.mssql
===============================	
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