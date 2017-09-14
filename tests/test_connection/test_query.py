# -*- coding: utf-8 -*-
import unittest

from moose.connection import query
from moose.connection.database import SQLServerHandler


SQLSERVER_SETTING = {
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

handler = SQLServerHandler(SQLSERVER_SETTING)

class AllGuidQueryTestCase(unittest.TestCase):
    def test_query(self):
        q = query.AllGuidQuery(handler, SQLSERVER_SETTING['TABLE_ALIAS'])
        result = q.query(project_id=16652)
        self.assertEqual(len(result), 8306)


class StatusGuidQueryTestaCase(unittest.TestCase):

    def test_query(self):
        q = query.StatusGuidQuery(handler, SQLSERVER_SETTING['TABLE_ALIAS'])
        result = q.query(project_id=16652, status=q.STATUS['pass'])
        self.assertEqual(len(result), 1269)
