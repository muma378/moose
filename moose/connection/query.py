# -*- coding: utf-8 -*-
import logging

from moose.utils import six
from moose.utils.module_loading import import_string
from moose.core.exceptions import ImproperlyConfigured
from . import database

logger = logging.getLogger(__name__)

class SQLOperation(object):
    """
    Class to do the query operation.

    `statement_template`
        Template of sql statement to operate.

    `handler`
        An instance of moose.connection.database.BaseSQLHandler.

    `table_alias`
        Dictionary containing information of tables and fields.

    """
    statement_template = None
    base_handler_cls = database.BaseSQLHandler

    def __init__(self, handler, table_alias):
        self.handler = handler
        self.table_alias = table_alias

    @classmethod
    def create_from_context(cls, query_context):
        handler_cls = query_context['sql_handler']
        handler_settings = query_context['sql_context']

        if isinstance(handler_cls, six.string_types):
            handler_cls = import_string(handler_cls)
        if issubclass(handler_cls, cls.base_handler_cls):
            handler = handler_cls(handler_settings)
        else:
            raise ImproperlyConfigured(\
                "Database handlers must be a subclass of {}.".format(base_cls))

        table_alias = handler_settings['TABLE_ALIAS']
        return cls(handler, table_alias)


class BaseQuery(SQLOperation):

    def query(self, **context):
        try:
            context.update(self.table_alias)
            sql_statement = self.statement_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Keys missing: {}".format(str(e)))
        # execute the query with context provided
        return self.handler.exec_query(sql_statement)


class BaseGuidQuery(BaseQuery):
    """
    Class to query 'SourceGuid' and 'ResultGuid' according to various conditions.
    """

    statement_template = (
        "select dr.SourceGuid, dr.DataGuid from {tables} where {conditions} "
    )
    tables = None
    conditions = None

    def __init__(self, handler, table_alias):
        super(BaseGuidQuery, self).__init__(handler, table_alias)
        self.statement_template = self.statement_template.format(
            tables = self.tables,
            conditions = self.conditions,
        )

class AllGuidQuery(BaseGuidQuery):
    """
    Get all records for a project.
    """
    tables = "{table_result} dr"
    conditions = "dr.ProjectId = {project_id}"

class StatusGuidQuery(AllGuidQuery):
    """
    Get records whose data_result.status matches the given value.
    """
    conditions = "dr.ProjectId = {project_id} and dr.status = {status}"

    STATUS = {
        'default': 0,
        'pass': 1,
        'refuse': 2,
        'revised': 3,
    }

class CreatedTimeGuidQuery(AllGuidQuery):
    """
    Get records created before or after the given datetime.
    """
    conditions = (
        "dr.ProjectId = {project_id} and dr.Date {less_or_more} '{datetime}'"
    )


class AccessedTimeGuidQuery(AllGuidQuery):
    """
    Get records accessed before or after the given datetime.
    """
    conditions = (
        "dr.ProjectId = {project_id} and dr.LastEditTime {less_or_more} '{datetime}'"
    )

class AccountGuidQuery(BaseGuidQuery):
    """
    Get records annotated by specified accounts.
    """
    tables = "{table_result} dr, {table_person} ps"
    conditions = (
        "dr.ProjectId = {project_id} and dr.UserGuid = ps.ProviderUserKey and "
        "ps.Account in {accounts}"
    )

class TitlesGuidQuery(BaseGuidQuery):
    """
    Get records with specified titles in table `DataSource`.
    """
    tables = "{table_source} ds, {table_result} dr"
    conditions = (
        "ds.DataGuid = dr.SourceGuid and ds.ProjectId = {project_id} and "
        "dr.ProjectId = {project_id} and ds.Title in {titles}"
    )

class BaseUsersQuery(BaseQuery):
    statement_template = (
        "select DISTINCT pip.id, pip.PersonName {fields} from "
        "{table_person_in_project} pip, {table_person} ps {tables} where "
        "pip.ProjectId = {project_id} and pip.PersonId=ps.id {conditions}"
    )

    fields = None
    tables = None
    conditions = None

    # def __init__(self, handler, table_alias):
    #     super(BaseUsersQuery, self).__init__(handler, table_alias)
    #     self.statement_template = self.statement_template.format(
    #         fields = self.fields,
    #         tables = self.tables,
    #         conditions = self.conditions,
    #     )

class UserGuidInProjectQuery(BaseUsersQuery):
    """
    Get user guid in project from name and project_id provided
    """
    statement_template = (
        "select ProviderUserGuid from {table_person_in_project} "
        "where PersonName = '{user_name}' and ProjectId = {project_id}"
    )

class UsersInProjectQuery(BaseUsersQuery):
    """
    Get information of users took part in a project. Note the 'id' returned is
    the same with the key '_personInProjectId' in the table `result` in mongodb.
    """
    statement_template = (
        "select DISTINCT pip.id, pip.PersonName, ps.Account from "
        "{table_person_in_project} pip, {table_person} ps "
        "where pip.ProjectId = {project_id} and pip.PersonId=ps.id"
    )

class TeamUsersInProjectQuery(BaseUsersQuery):
    """
    Get information of users took part in a project. Note the 'id' returned is
    the same with the key '_personInProjectId' in the table `result` in mongodb.
    """
    statement_template = """
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
                    pip.ProjectId = {project_id}
                AND pip.PersonId = ps.id
            ) AS person
        LEFT JOIN {table_person_in_team} pit ON pit.ProviderUserKey = Person.ProviderUserGuid
    ) AS pat
LEFT JOIN {table_team} AS t ON pat.TeamId = t.Id
"""

class BaseInfoQuery(BaseQuery):
    pass

class DataResultQuery(BaseQuery):

    statement_template = (
        "select * from {table_result} dr where dr.ProjectId={project_id}"
    )

class DataSourceQuery(BaseQuery):

    statement_template = (
        "select * from {table_source} ds where ds.ProjectId={project_id}"
    )

class DataInfoQuery(BaseQuery):

    statement_template = (
        "select ds.Title, ds.FileName, dr.Status, dr.IsValid, dr.UserGuid, "
        "dr.SourceGuid, dr.DataGuid from {table_source} ds, {table_result} "
        "dr where ds.DataGuid=dr.SourceGuid and dr.ProjectId={project_id} "
        "and ds.ProjectId={project_id}"
    )

class ProjectInfoQuery(BaseQuery):

    statement_template = (
        "select * from {table_project} where id={project_id}"
    )

class ProjectInfoByBatchQuery(BaseQuery):

    statement_template = (
        "select * from {table_project} where batch= '{batch_name}'"
    )

class AcqInfoByGuid(BaseQuery):

    statement_template = (
        "select * from {table_acquisition} where DataGuid= '{data_guid}'"
    )

class AcqInfoByUserguidQuery(BaseQuery):

    statement_template = (
        "select * from {table_acquisition} WHERE ProjectId = {project_id} "
        "and UserGuid = '{user_guid}' and isValid = 1"
    )

class AcqToMarkByUserguidQuery(BaseQuery):

    statement_template = (
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'{create_time}' from {table_acquisition} "
        "WHERE ProjectId = {acquisition_id} and UserGuid = '{user_guid}' "
        "and isValid = 1"
    )

class BaseInsert(SQLOperation):

    def execute(self, **context):
        try:
            context.update(self.table_alias)
            sql_statement = self.statement_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Keys missing: {}".format(str(e)))
        # execute the query with context provided
        naffected = self.handler.exec_commit(sql_statement)
        return naffected

class BulkInsert(SQLOperation):

    def execute(self, rows, **context):
        try:
            context.update(self.table_alias)
            sql_statement = self.statement_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Keys missing: {}".format(str(e)))
        # execute the query with context provided
        return self.handler.exec_many(sql_statement, rows)


class AcqToMarkByTitle(BaseInsert):

    statement_template = (
        "insert into {table_source} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,{create_time} from {table_acquisition} "
        "WHERE ProjectId in {acquisition_ids} and substring(Title, 6, 5) in ({groups})"
    )

class AcqToMarkByUserguid(BaseInsert):

    statement_template = (
        "insert into {table_source} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'{create_time}' from {table_acquisition} "
        "WHERE ProjectId = {acquisition_id} and UserGuid = '{user_guid}' "
        "and isValid = 1"
    )

class AcqToMarkByDataguid(BaseInsert):

    statement_template = (
        "insert into {table_source} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'{create_time}' from {table_acquisition} "
        "WHERE DataGuid = '{data_guid}' and isValid = 1"
    )

class AcqsToMarkByDataguids(BulkInsert):
    statement_template = (
        "insert into {table_source} (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) values "
        "({project_id},'%s','%s',%d,'%s',%s,'%s','{create_time}')"
    )
