# -*- coding: utf-8 -*-

table_alias = {
    'table_result': '[10.0.0.201].CrowdDB.dbo.DataResult',
    'table_source': '[10.0.0.201].CrowdDB.dbo.DataSource',
    'table_person': '[10.0.0.201].CrowdDB.dbo.Person',
    'table_project': '[10.0.0.201].CrowdDB.dbo.Project',
    'table_person_in_project': '[10.0.0.201].CrowdDB.dbo.PersonInProject',
    'table_person_in_team': '[10.0.0.201].CrowdDB.dbo.PersonInTeam',
    'table_team': '[10.0.0.201].CrowdDB.dbo.Team',
    'table_acquisition': '[10.0.0.201].CrowdDB.dbo.DataAcquisition',
}

template_table_alias = {
    'table_result': '$table_result',
    'table_source': '$table_source',
    'table_person': '$table_person',
    'table_project': '$table_project',
    'table_person_in_project': '$table_person_in_project',
    'table_person_in_team': '$table_person_in_team',
    'table_team': '$table_team',
    'table_acquisition': '$table_acquisition',
}

sql_settings = {
    'HOST': '<host>',
    'PORT': '<port>',
    'USER': '<user>',
    'PASSWORD': '<password>',
    'DATABASE': '<database>',
    'CHARSET': 'UTF-8',
    'TABLE_ALIAS': table_alias,
}


mongo_settings = {
    'HOST': '<host>',
    'PORT': '<port>',
    'USER': '<user>',
    'PASSWORD': '<password>',
}
