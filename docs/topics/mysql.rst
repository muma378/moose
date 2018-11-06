==========================
moose.connection.mysql
==========================

.. class:: MySQLHandler(BaseSQLHandler)
	
	MySQLHandler是BaseSQLHandler的子类，它定义了基于BaseSQLHandler类的在MySQL数据中的实现。
	
	.. attribute:: db_name = 'MySQL'
		
		定义该数据库名称为 ``MySQL``

	.. method:: _connect(settings_dict)
			
		:param dict settings_dict: 包含数据配置的字典，包含如 ``HOST`` （要连接的数据库的主机地址），``PORT`` （端口），``USER`` （用户名） ， ``PASSWORD`` （用户密码） 以及 ``CHARSET`` （编码方式），如果需要给数据表起别名还可能包括 ``TABLE_ALIAS`` （给数据表起别名）。
		
		该方法根据输入的数据库配置返回MySQL数据库的连接对象。