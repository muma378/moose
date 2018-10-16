# -*- coding: utf-8 -*-
import unittest
import mock
import copy

from moose.connection import sqlhandler
from moose.connection import operations
from moose.utils.module_loading import import_string
from moose.core.exceptions import ImproperlyConfigured

from .config import sql_settings
from .config import template_table_alias as table_alias


class BaseOperationTestCase(unittest.TestCase):

    def setUp(self):
        self.context = {
            "sql_handler": 'moose.connection.mssql.SQLServerHandler',
            "sql_context": sql_settings,
        }

    @mock.patch("moose.connection.operations.issubclass")
    @mock.patch("moose.connection.operations.import_string")
    def test_valid_context(self, mock_import, mock_issubclass):
        MockHandler = mock.Mock(return_value=None)
        mock_import.return_value = MockHandler
        mock_issubclass.return_value = True

        sql_operation = operations.BaseOperation.create_from_context(self.context)
        mock_import.assert_called_with(self.context['sql_handler'])
        mock_issubclass.assert_called_with(MockHandler, sqlhandler.BaseSQLHandler)
        MockHandler.assert_called_with(sql_settings)
        self.assertEqual(sql_operation.handler, None)

    @mock.patch("moose.connection.operations.issubclass")
    @mock.patch("moose.connection.operations.import_string")
    def test_not_subclass(self, mock_import, mock_issubclass):
        mock_issubclass.return_value = False

        with self.assertRaises(ImproperlyConfigured):
            operations.BaseOperation.create_from_context(self.context)

    def test_unknown_import(self):
        self.context['sql_handler'] = 'moose.import.error.module'
        with self.assertRaises(ImproperlyConfigured):
            operations.BaseOperation.create_from_context(self.context)


class BaseQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_exec_query = mock.Mock(return_value="test")
        handler = mock.Mock()
        handler.exec_query = self.mock_exec_query
        self.querier = operations.BaseQuery(handler)

    def test_query(self):
        # test query without params
        self.querier.operation_template = "select * from $table_result"
        self.querier.query()
        self.mock_exec_query.assert_called_with(\
            "select * from {}".format(table_alias['table_result']))

        # test query with params
        self.querier.operation_template = "select * from $table_result where task_id={task_id}"
        self.querier.query(task_id=1000)
        self.mock_exec_query.assert_called_with(\
            "select * from {} where task_id=1000".format(table_alias['table_result']))

        # test query with params missing
        self.querier.operation_template = "select * from $table_result where task_id={task_id}"
        with self.assertRaises(ImproperlyConfigured):
            self.querier.query()

class BaseQueryTest(object):

    query_cls_str = None
    params_operation_map = [
        ({"param1":1}, "operation1")
        ]

    def setUp(self):
        self.mock_exec_query = mock.Mock(return_value="test")
        handler = mock.Mock()
        handler.exec_query = self.mock_exec_query
        query_klass = import_string(self.query_cls_str)
        self.querier = query_klass(handler)

    def test_query(self):
        for context, operation in self.params_operation_map:
            self.querier.query(**context)
            self.mock_exec_query.assert_called_with(operation)


class AllGuidQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.AllGuidQuery"
    params_operation_map = [
        ({"project_id": 1}, "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = 1 ".format(table_alias['table_result'])),
        ({"project_id": "abc"}, "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = abc ".format(table_alias['table_result'])),
        ]

class StatusGuidQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.StatusGuidQuery"
    params_operation_map = [
        ({"project_id": 1, "status": 0}, "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = 1 and dr.status = 0 ".format(table_alias['table_result'])),
        ({"project_id": "abc", "status": 1000}, "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = abc and dr.status = 1000 ".format(table_alias['table_result'])),
        ]

class CreatedTimeGuidQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.CreatedTimeGuidQuery"
    params_operation_map = [
        ({"project_id": 1, "less_or_more": "<", "datetime": "2018-09-30"},
        "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = 1 "
        "and dr.Date < '2018-09-30' ".format(table_alias['table_result'])
        ),
        ({"project_id": "abc", "less_or_more": "=", "datetime": "2018-09-30"},
        "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = abc "
        "and dr.Date = '2018-09-30' ".format(table_alias['table_result'])),
        ]

class CreatedTimeGuidQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.AccessedTimeGuidQuery"
    params_operation_map = [
        ({"project_id": 1, "less_or_more": "<", "datetime": "2018-09-30"}, "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = 1 and dr.LastEditTime < '2018-09-30' ".format(table_alias['table_result'])),
        ({"project_id": 1, "less_or_more": "=", "datetime": "2018-09-30 12:25:00"}, "select dr.SourceGuid, dr.DataGuid from {} dr where dr.ProjectId = 1 and dr.LastEditTime = '2018-09-30 12:25:00' ".format(table_alias['table_result'])),
        ]

class TitlesGuidQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.TitlesGuidQuery"
    params_operation_map = [
        ({"project_id": 1, "titles": "('a', 'b', 'c')"}, "select dr.SourceGuid, dr.DataGuid from {} ds, {} dr where ds.DataGuid = dr.SourceGuid and ds.ProjectId = 1 and dr.ProjectId = 1 and ds.Title in ('a', 'b', 'c') ".format(table_alias['table_source'], table_alias['table_result'])),
        ({"project_id": 1, "titles": "('a')"}, "select dr.SourceGuid, dr.DataGuid from {} ds, {} dr where ds.DataGuid = dr.SourceGuid and ds.ProjectId = 1 and dr.ProjectId = 1 and ds.Title in ('a') ".format(table_alias['table_source'], table_alias['table_result'])),
        ]

class BaseUsersQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.BaseUsersQuery"
    params_operation_map = [
        ({"project_id": 1}, "select DISTINCT pip.id, pip.PersonName  from "
        "{} pip, {} ps  where "
        "pip.ProjectId = 1 and pip.PersonId=ps.id ".format(table_alias['table_person_in_project'], table_alias['table_person'])),
        ]

class UsersInProjectQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.UsersInProjectQuery"
    params_operation_map = [
        ({"project_id": 1}, "select DISTINCT pip.id, pip.PersonName , ps.Account from "
        "{} pip, {} ps  where "
        "pip.ProjectId = 1 and pip.PersonId=ps.id ".format(table_alias['table_person_in_project'], table_alias['table_person'])),
        ]

test_operation = """
SELECT
    pat.id, pat.PersonName, pat.Account, t.Name
FROM
    (
        SELECT
            person.*, pit.TeamId
        FROM
            (
                SELECT DISTINCT
                    pip.id, pip.PersonName, pip.ProviderUserGuid, ps.Account
                FROM
                    {table_person_in_project} pip, {table_person} ps
                WHERE
                    pip.ProjectId = 1000
                AND pip.PersonId = ps.id
            ) AS person
        LEFT JOIN {table_person_in_team} pit ON pit.ProviderUserKey = Person.ProviderUserGuid
    ) AS pat
LEFT JOIN {table_team} AS t ON pat.TeamId = t.Id
"""

class TeamUsersInProjectQueryTestCase(BaseQueryTest, unittest.TestCase):
    query_cls_str = "moose.connection.operations.TeamUsersInProjectQuery"
    params_operation_map = [
        ({"project_id": 1000}, test_operation.format(**table_alias)),
        ]

class DataSourceQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.DataSourceQuery"
    params_operation_map = [
        ({"project_id": 1000}, "select * from {} ds where ds.ProjectId=1000".format(table_alias['table_source'])),
        ]

class DataResultQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.DataResultQuery"
    params_operation_map = [
        ({"project_id": 1000},
        "select * from {} dr where dr.ProjectId=1000".format(table_alias['table_result'])),
        ]

class DataInfoQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.DataInfoQuery"
    params_operation_map = [
        ({"project_id": 1000},
        "select ds.Title, ds.FileName, dr.Status, dr.IsValid, dr.UserGuid, "
        "dr.SourceGuid, dr.DataGuid from {} ds, {} dr where "
        "ds.DataGuid=dr.SourceGuid and dr.ProjectId=1000 and "
        "ds.ProjectId=1000".format(table_alias['table_source'], table_alias['table_result'])
        ),
        ]

class ProjectInfoQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.ProjectInfoQuery"
    params_operation_map = [
        ({"project_id": 1000},
        "select * from {} where id=1000".format(table_alias['table_project'])),
        ]

class ProjectInfoQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.ProjectInfoQuery"
    params_operation_map = [
        ({"project_id": 1000},
        "select * from {} where id=1000".format(table_alias['table_project'])),
        ]

class ProjectInfoByBatchQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.ProjectInfoByBatchQuery"
    params_operation_map = [
        ({"batch_name": "测试任务"},
        "select * from {} where batch='测试任务'".format(table_alias['table_project'])),
        ]

class AcqInfoByGuidTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.AcqInfoByGuidQuery"
    params_operation_map = [
        ({"data_guid": "d18505b5-6527-4f4d-bd0b-76c9c99de8c7"},
        "select * from {} where DataGuid= 'd18505b5-6527-4f4d-bd0b-76c9c99de8c7'"
        "".format(table_alias['table_acquisition'])
        ),
        ]

class AcqInfoByUserQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.AcqInfoByUserQuery"
    params_operation_map = [
        ({"project_id": 1, "user_guid": "d18505b5-6527-4f4d-bd0b-76c9c99de8c7"},
        "select * from {} WHERE ProjectId = 1 and UserGuid = "
        "'d18505b5-6527-4f4d-bd0b-76c9c99de8c7' and isValid = 1"
        "".format(table_alias['table_acquisition'])
        )
        ]

class AcqToMarkByUserQueryTestCase(BaseQueryTest, unittest.TestCase):

    query_cls_str = "moose.connection.operations.AcqToMarkByUserQuery"
    params_operation_map = [
        ({"project_id": 1,
        "user_guid": "d18505b5-6527-4f4d-bd0b-76c9c99de8c7",
        "create_time": "2018-09-30",
        "acquisition_id": 2},
        "select 1,Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'2018-09-30' from {} "
        "WHERE ProjectId = 2 and UserGuid = 'd18505b5-6527-4f4d-bd0b-76c9c99de8c7' "
        "and isValid = 1"
        "".format(table_alias['table_acquisition'])
        )
        ]

class BaseInsertTestCase(unittest.TestCase):
    def setUp(self):
        self.mock_exec_commit = mock.Mock(return_value=100)
        handler = mock.Mock()
        handler.exec_commit = self.mock_exec_commit
        self.operator = operations.BaseInsert(handler)

    def test_execute(self):
        # test query without params
        self.operator.operation_template = "insert into $table_source (a, b, c)"
        self.operator.execute()
        self.mock_exec_commit.assert_called_with(\
            "insert into {} (a, b, c)".format(table_alias['table_source']))

        # test execute with params
        self.operator.operation_template = "insert into $table_source (a, b, c) select * from $table_source where ProjectId={task_id}"
        self.operator.execute(task_id=1000)
        self.mock_exec_commit.assert_called_with(\
            "insert into {} (a, b, c) select * from {} where ProjectId=1000".format(table_alias['table_source'], table_alias['table_source']))

        # test execute with params missing
        self.operator.operation_template = "insert into $table_source (a, b, c) select * from $table_source where ProjectId={task_id}"
        with self.assertRaises(ImproperlyConfigured):
            self.operator.execute()


class BaseInsertTest(object):

    operate_cls_str = None
    params_operation_map = [
        ({"param1":1}, "operation1")
        ]

    def setUp(self):
        self.mock_exec_commit = mock.Mock(return_value=100)
        handler = mock.Mock()
        handler.exec_commit = self.mock_exec_commit

        operator_klass = import_string(self.operate_cls_str)
        self.operator = operator_klass(handler)

    def test_execute(self):
        for context, operation in self.params_operation_map:
            self.operator.execute(**context)
            self.mock_exec_commit.assert_called_with(operation)

class AcqToMarkByTitleTestCase(BaseInsertTest, unittest.TestCase):
    operate_cls_str = "moose.connection.operations.AcqToMarkByTitle"
    params_operation_map = [
        ({"project_id": 1, "create_time": '2018-09-30', 'acquisition_ids': "'1', '2', '3'", "groups": "'G0001', 'G0002'"},
        "insert into {} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select 1,Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,2018-09-30 from {} "
        "WHERE ProjectId in ('1', '2', '3') and substring(Title, 6, 5) "
        "in ('G0001', 'G0002')".format(table_alias['table_source'], table_alias['table_acquisition']))
        ]

class AcqToMarkByUserTestCase(BaseInsertTest, unittest.TestCase):
    operate_cls_str = "moose.connection.operations.AcqToMarkByUser"
    params_operation_map = [
        ({"project_id": 1, "create_time": '2018-09-30', 'acquisition_id': 2, "user_guid": 'd18505b5-6527-4f4d-bd0b-76c9c99de8c7'},
        "insert into {} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select 1,Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'2018-09-30' from {} WHERE ProjectId = "
        "2 and UserGuid = 'd18505b5-6527-4f4d-bd0b-76c9c99de8c7' "
        "and isValid = 1".format(table_alias['table_source'], table_alias['table_acquisition']))
        ]

class AcqToMarkByDataguidTestCase(BaseInsertTest, unittest.TestCase):

    operate_cls_str = "moose.connection.operations.AcqToMarkByDataguid"
    params_operation_map = [
        ({"project_id": 1, "create_time": '2018-09-30', "data_guid": 'd18505b5-6527-4f4d-bd0b-76c9c99de8c7'},
        "insert into {} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select 1,Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'2018-09-30' from {} WHERE DataGuid"
        " = 'd18505b5-6527-4f4d-bd0b-76c9c99de8c7' and isValid = 1"
        "".format(table_alias['table_source'], table_alias['table_acquisition']))
        ]


class BuckInsertTestCase(unittest.TestCase):
    def setUp(self):
        self.mock_exec_many = mock.Mock(return_value=100)
        handler = mock.Mock()
        handler.exec_many = self.mock_exec_many
        self.operator = operations.BulkInsert(handler)

    def test_execute(self):
        # test query without params
        self.operator.operation_template = "insert into $table_source (a, b, c)"
        self.operator.execute((1, 2, 3))
        self.mock_exec_many.assert_called_with(\
            "insert into {} (a, b, c)".format(table_alias['table_source']), (1, 2, 3))

        # test execute with params
        self.operator.operation_template = "insert into $table_source (a, b, c) select * from $table_source where ProjectId={task_id}"
        self.operator.execute((1, 2, 3), task_id=1000)
        self.mock_exec_many.assert_called_with(\
            "insert into {} (a, b, c) select * from {} where ProjectId=1000".format(table_alias['table_source'], table_alias['table_source']), (1, 2, 3))

        # test execute with params missing
        self.operator.operation_template = "insert into $table_source (a, b, c) select * from $table_source where ProjectId={task_id}"
        with self.assertRaises(ImproperlyConfigured):
            self.operator.execute((1, 2, 3))
