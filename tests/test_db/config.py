# -*- coding: utf-8 -*-

mssql_settings = {
    'HOST': '<host>',
    'PORT': '<port>',
    'USER': '<user>',
    'PASSWORD': '<password>',
    'DATABASE': '<database>',
    'CHARSET': 'UTF-8',
    'TABLE_ALIAS': {
        'table_result': '[10.0.0.201].CrowdDB.dbo.DataResult',
        'table_source': '[10.0.0.201].CrowdDB.dbo.DataSource',
        'table_person': '[10.0.0.201].CrowdDB.dbo.Person',
        'table_project': '[10.0.0.201].CrowdDB.dbo.Project',
        'table_person_in_project': '[10.0.0.201].CrowdDB.dbo.PersonInProject',
    },
}

mysql_settings = {
    'HOST': '<host>',
    'PORT': '<port>',
    'USER': '<user>',
    'PASSWORD': '<password>',
    'DATABASE': '<database>',
    'CHARSET': 'utf8',
    'TABLE_ALIAS': {
        'table_result': 'dataresult',
        'table_source': 'datasource',
        'table_person': 'person',
        'table_project': 'task',
        'table_person_in_project': 'person_in_task',
    },
}
