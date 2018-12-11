.. _topics-conn-ops:

=============================
SQL操作
=============================

用户在操作数据库时需要调用数据库接口类，而要执行某次具体的操作必须要有确定的sql语句及配置信息，Operation类将数据库接口类对象作为其参数，配合sql语句模板进行封装来适配不同的数据操作需求，使得在其上的各种动作（Action）可以使用相同的接口。

.. class:: BaseOperation(handler)

    该类是所有operation类的基类，定义了类的必要配置而更多的功能则需子类根据需求自行扩展。

    :param object handler: 数据库接口类对象


    .. attribute:: operation_template = None

		定义查询语句模板默认为None,其子类可根据不同的需求定制sql语句模板

    .. attribute:: base_handler_cls = sqlhandler.BaseSQLHandler

		定义默认数据库操作的接口类为 ``sqlhandler.BaseSQLHandler``

    .. method:: create_from_context(query_context)

		``@classmethod``

		:param dict query_context: 数据库查询配置信息，包括数据库配置信息和数据库接口类

		该方法根据输入的数据库配置信息首先判断是否合法，返回接口类对象


.. class:: BaseQuery(BaseOperation)

	该类是 ``BaseOperation`` 的子类，在继承基类的同时增加了调用数据库接口类执行查询操作。

	.. method:: query(**context)

		:param dict context: 查询语句模板的参数

		该方法根据输入的查询语句参数生成完整的sql语句并调用数据库接口类方法执行查询操作。

.. class:: BaseGuidQuery(BaseQuery)

	该类是``BaseQuery``的子类，返回根据给定参数查询 ``SourceGuid`` 和 ``ResultGuid`` 字段的值。

    :param object handler: 数据库接口类对象


    .. attribute::  operation_template

		定义查询语句的模板，这里定义了查询语句结果需要返回的字段为 ``SourceGuid`` 和 ``ResultGuid``

    .. attribute:: tables = None

		定义查询语句的数据表

    .. attribute:: conditions = None

		定义查询语句的条件


    `operation_template` 为： ::

        "SELECT dr.SourceGuid, dr.DataGuid FROM $tables WHERE $conditions "


.. class:: AllGuidQuery(BaseGuidQuery)

	该类是 ``BaseGuidQuery`` 的子类，指定了查询语句的数据表 ``$table_result dr`` 和查询条件字段 ``dr.ProjectId = {project_id}``

	.. attribute:: tables = "$table_result dr"

		定义查询语句的数据表为 ``table_result`` 并将该表重命名为 ``dr``

	.. attribute:: conditions = "dr.ProjectId = {project_id}"

		定义查询语句的条件数据表中的ProjectId与输入的值进行匹配。

.. class:: StatusGuidQuery(AllGuidQuery)

	该类是 ``AllGuidQuery`` 的子类，它在基类条件的基础上新增了数据表的状态作为条件字段，使查询更精细化。

	.. attribute:: conditions = "dr.ProjectId = {project_id} AND dr.status = {status}"

		定义查询语句模板的条件字段

	.. attribute:: STATUS

        定义查询语句的条件数据表中的数据表状态

    `STATUS` 定义如下： ::

        STATUS = {
            'default': 0,
            'pass': 1,
            'refuse': 2,
            'revised': 3,
            }


.. class:: CreatedTimeGuidQuery(AllGuidQuery)

	该类是 ``AllGuidQuery`` 的子类，它在基类条件的基础上新增了数据表中的数据创建时间字段作为条件字段，用来获取在给定日期时间之前或之后创建的记录。

	.. attribute::   conditions

		定义查询语句模板的条件字段为项目ID和数据表中的数据创建时间

    `conditions` 定义如下：::

        "dr.ProjectId = {project_id} AND dr.Date {less_or_more} '{datetime}'"


.. class:: AccessedTimeGuidQuery(AllGuidQuery)

	该类是 ``AllGuidQuery`` 的子类，它在基类条件的基础上新增了数据表中的最后访问时间作为条件字段，用来获取在给定日期时间之前或之后访问的记录。

	.. attribute:: conditions

		定义查询语句模板的条件字段为项目ID和数据表中的数据最后访问时间

    `conditions` 定义如下：::

        "dr.ProjectId = {project_id} AND dr.LastEditTime {less_or_more} '{datetime}'"

.. class:: AccountGuidQuery(BaseGuidQuery)

	该类是 ``BaseGuidQuery`` 的子类，它将基类的单表查询通过 ``dr.UserGuid = ps.ProviderUserKey`` 连接变成多表联合查询且查询条件字段为数据表dr中的ProjectId字段
	和数据表ps中的Account字段，获取指定帐户的记录

	.. attribute::  tables = "$table_result dr, $table_person ps"

		定义查询语句中数据表为 ``table_result`` 及 ``table_person`` 并将它们重命名为 ``dr`` 和 ``ps``

    该方法定义了查询语句模板的条件字段为 ``ps.Account`` 、 ``dr.ProjectId`` 、 ``ps.Account`` 以及 ``dr.UserGuid = ps.ProviderUserKey``

    `conditions` 定义如下：

    ::

	"dr.ProjectId = {project_id} AND dr.UserGuid = ps.ProviderUserKey AND ps.Account in {accounts}"


.. class:: TitlesGuidQuery(BaseGuidQuery)

	该类是 ``BaseGuidQuery`` 的子类，它将基类的单表查询通过 ``ds.DataGuid = dr.SourceGuid`` 连接变成多表联合查询且查询条件字段为 ``ds.Title`` 、 ``ds.DataGuid = dr.SourceGuid`` 及ProjectId字段等，获取指定标题的记录。

	.. attribute::   tables = "$table_source ds, $table_result dr"

		定义查询语句中数据表为 ``table_source`` 及 ``table_result`` 并将它们重命名为 ``ds`` 和 ``dr``


    该方法定义了查询语句模板的条件字段为 ``ds.Title`` 、 ``ds.DataGuid = dr.SourceGuid`` 和 ``ds.ProjectId = {project_id}`` 以及 ``dr.ProjectId = {project_id}``

    `conditions` 定义如下：

    ::

    "ds.DataGuid = dr.SourceGuid AND ds.ProjectId = {project_id} AND  dr.ProjectId = {project_id} AND ds.Title in {titles}"

.. class:: BaseUsersQuery(BaseQuery)

	该类是 ``BaseQuery`` 的子类，定义了查询模板的条件为表 ``table_person_in_project`` 中的字段 ``ProjectId`` 等于表 ``table_person`` 中的字段 ``id`` 及查询字段并预留了扩展字段供子类使用。


	.. attribute::   fields = ""

		定义查询语句中预留的查询字段，默认为空

	.. attribute::   tables = ""

		定义查询语句中预留的数据表，默认为空

	.. attribute::   conditions = ""

		定义查询语句中预留的条件，默认为空

    `operation_template` 定义如下：

    ::

	"SELECT DISTINCT pip.id, pip.PersonName $fields FROM $table_person_in_project pip, $table_person ps $tables WHERE pip.ProjectId = {project_id} AND pip.PersonId=ps.id $conditions"

.. class:: UsersInProjectQuery(BaseUsersQuery)

	该类是 ``BaseUsersQuery`` 的子类，实现对查询字段的扩展，返回用户参与项目的信息

	.. attribute::   fields = ", ps.Account"

		该属性定义了向模板中添加了查询字段 ``ps.Account``


.. class:: UserGuidInProjectQuery(BaseQuery)

	该类定义模板实现根据提供的 ``PersonName`` 和 ``project_id`` 中获取用户guid( ``ProviderUserGuid``)

    `operation_template` 定义如下：

    ::

	"SELECT ProviderUserGuid FROM $table_person_in_project WHERE PersonName = '{user_name}' AND ProjectId = {project_id}"


.. class:: TeamUsersInProjectQuery(BaseQuery)

	该类定义模板用来获取指定用户参与项目的信息

    `operation_template` 定义如下：

    ::

	'''
	SELECT pat.id, pat.PersonName, pat.Account, t.Name
		FROM
		    (
		        SELECT
		            person.*, pit.TeamId
		        FROM
		            (
		                SELECT DISTINCT
		                    pip.id, pip.PersonName, pip.ProviderUserGuid, ps.Account
		                FROM
		                    $table_person_in_project pip, $table_person ps
		                WHERE
		                    pip.ProjectId = {project_id}
		                AND pip.PersonId = ps.id
		            ) AS person
		        LEFT JOIN $table_person_in_team pit ON pit.ProviderUserKey = Person.ProviderUserGuid
		    ) AS pat
		LEFT JOIN $table_team AS t ON pat.TeamId = t.Id
	'''


.. class:: DataSourceQuery(BaseQuery)

	该类继承了基类 ``BaseQuery`` ,定义了根据表 ``table_source`` 中匹配字段 ``ProjectId`` 进行查询的模板。

    `operation_template` 定义如下：

    ::

	"SELECT * FROM $table_source ds WHERE ds.ProjectId={project_id}"


.. class:: DataResultQuery(BaseQuery)

	该类继承了基类 ``BaseQuery`` ,定义了根据表 ``table_result`` 中匹配字段 ``ProjectId`` 进行查询的模板。

    `operation_template` 定义如下：

    ::

	"SELECT * FROM $table_result ds WHERE ds.ProjectId={project_id}"


.. class:: DataInfoQuery(BaseQuery)

	该类继承了基类 ``BaseQuery`` ,定义了根据 ``table_source.DataGuid=table_result.SourceGuid``查询指定项目信息的模板。

    `operation_template` 定义如下：

    ::

    "SELECT ds.Title, ds.FileName, dr.Status, dr.IsValid, dr.UserGuid, dr.SourceGuid, dr.DataGuid "
    "FROM $table_source ds, $table_result dr WHERE ds.DataGuid=dr.SourceGuid AND "
    "dr.ProjectId={project_id} AND ds.ProjectId={project_id}"


.. class:: ProjectInfoQuery(BaseQuery)

	该类定义了根据输入指定项目ID返回该项目所有信息的模板

    `operation_template` 定义如下：

    ::

	"SELECT * FROM $table_project WHERE id={project_id}"


.. class:: ProjectInfoByBatchQuery(BaseQuery)

	该类定义了根据输入的 ``batch`` 字段返回该项目所有信息的模板

    `operation_template` 定义如下：

    ::

	"SELECT * FROM $table_project WHERE batch='{batch_name}'"


.. class:: AcqInfoByGuidQuery(BaseQuery)

	该类定义了根据输入的 ``DataGuid`` 字段返回该项目所有信息的模板

    `operation_template` 定义如下：

    ::

	"SELECT * FROM $table_acquisition WHERE DataGuid= '{data_guid}'"

.. class:: AcqInfoByUserQuery(BaseQuery)

	该类定义了根据输入的 ``ProjectId`` 、 ``UserGuid`` 字段且 ``isValid = 1`` 返回该项目所有信息的模板

    `operation_template` 定义如下：

    ::

	"SELECT * FROM $table_acquisition WHERE ProjectId = {project_id} AND UserGuid = '{user_guid}' AND isValid = 1"

.. class:: AcqToMarkByUserQuery(BaseQuery)

	该类定义了根据输入的 ``ProjectId`` 、 ``UserGuid`` 字段且 ``isValid = 1`` 返回该项目指定输出字段的模板

    `operation_template` 定义如下：

    ::

	"SELECT {project_id},Title,DataGuid,DataVersion,UserGuid,Duration,FileName,'{create_time}' "
	"FROM $table_acquisition WHERE ProjectId = {acquisition_id} AND UserGuid = '{user_guid}' "
	"AND isValid = 1"

.. class:: BaseInsert(BaseOperation)

	该类继承了 ``BaseOperation`` ，定义了单条数据插入的方法，其子类可通过修改sql语句模板进行不同的操作。

	.. method:: execute(**context)

		:param dict context: 查询语句模板的参数

		该方法根据输入的模板参数按照指定的sql语句执行插入数据操作，返回插入后的结果。


.. class:: AcqToMarkByUser(BaseInsert)

	该类定义了一个根据条件字段为 ``ProjectId`` 、 ``UserGuid`` 且 ``isValid = 1`` 查询得到数据然后插入指定数据表 ``table_source`` 的模板

    `operation_template` 定义如下：

    ::

	"INSERT INTO $table_source (ProjectID,Title,DataGuid,DataVersion,UserGuid,Duration,FileName, "
	"CreateTime) SELECT {project_id},Title,DataGuid,DataVersion,UserGuid,Duration,FileName, "
	"'{create_time}' FROM $table_acquisition WHERE ProjectId = {acquisition_id} AND UserGuid = "
	"'{user_guid}' AND isValid = 1"

.. class:: AcqToMarkByDataguid(BaseInsert)

	该类定义了一个根据条件字段为 ``DataGuid`` 且 ``isValid = 1`` 查询得到数据然后插入指定数据表 ``table_source`` 的模板

    `operation_template` 定义如下：

    ::

    "INSERT INTO $table_source (ProjectID,Title,DataGuid,DataVersion,UserGuid,Duration,FileName, "
    "CreateTime) SELECT {project_id},Title,DataGuid,DataVersion,UserGuid,Duration,FileName, "
    "'{create_time}' FROM $table_acquisition WHERE DataGuid = '{data_guid}' AND isValid = 1"

.. class:: BulkInsert(BaseOperation)

	该类继承了 ``BaseOperation`` ，定义了 ``批量`` 插入数据的方法，其子类可通过修改sql语句模板进行不同的操作。

	.. method:: execute(**context)

		:param dict context: 查询语句模板的参数

		该方法根据输入的模板参数按照指定的sql语句执行插入数据操作，返回插入后的结果。

.. class:: BulkAcqToMarkByDataguid(BulkInsert)

    `operation_template` 定义如下：

    ::

	"INSERT INTO $table_source ({project_id},%s,%s,%s,%s,%f,%s,{create_time})"
