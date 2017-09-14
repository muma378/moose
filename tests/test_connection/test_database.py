# -*- coding: utf-8 -*-
import unittest
# import mock
from moose.connection.database import SQLServerHandler
from moose.conf import settings

DATABASES = {
    'sqlserver': {
        'HOST': '<host>',
        'PORT': '<port>',
        'USER': '<user>',
        'PASSWORD': '<password>',
        'DATABASE': 'CrowdDB',
        'CHARSET': 'UTF-8',
        'TABLE_ALIAS': {
            'table_result': '[10.0.0.201].CrowdDB.dbo.DataResult',
            'table_source': '[10.0.0.201].CrowdDB.dbo.DataSource',
            'table_person': '[10.0.0.201].CrowdDB.dbo.Person',
            'table_project': '[10.0.0.201].CrowdDB.dbo.Project',
            'table_person_in_project': '[10.0.0.201].CrowdDB.dbo.PersonInProject',
        },
    }
}
class SQLServerHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.db_handler = SQLServerHandler(DATABASES['sqlserver'])
        if self.db_handler.exec_query(r"select * from sys.tables where name='TestData'"):
            self.db_handler.exec_commit("drop table dbo.TestData")
            self.db_handler.exec_commit("create table dbo.TestData (test_id int PRIMARY KEY NOT NULL, test_content varchar(10))")

    def tearDown(self):
        self.db_handler.exec_commit("drop table dbo.TestData")
        # pass

    def test_connect(self):
        # close the connection before testing
        if self.db_handler.conn:
            self.db_handler.close()

        self.assertIsNone(self.db_handler.conn, 'did not close the connection')
        self.assertIsNotNone(self.db_handler.connect(), 'unable to provide a reliable conncetion')

    def test_query(self):
        self.assertEqual(len(self.db_handler.exec_query("select top 5 * from DataAcquisition")), 5)
        # self.assertEqual(len(self.db_handler.exec_query("select top 5 * from sys.tables")), 5)

        self.assertEqual(self.db_handler.exec_query("select ProjectId from DataAcquisition where ProjectId = 1774")[0][0], 1774)
        # self.assertEqual(self.db_handler.exec_query("select id from sys.tables where id = 1")[0][0], 1)

    def test_commit(self):
        self.assertIsNotNone(self.db_handler.exec_query(r"select * from sys.tables where name='TestData'"), 'create tabel failed')

        self.db_handler.exec_commit(r"insert into TestData values (1, 'test1')")
        self.assertIsNotNone(self.db_handler.exec_query("select * from TestData where test_id=1"))

        self.db_handler.exec_commit(r"update TestData set test_content='test2' where test_id=1")
        self.assertEqual(self.db_handler.exec_query(r"select test_content from TestData")[0][0], 'test2', 'update faield')
