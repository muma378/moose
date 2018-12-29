# -*- coding: utf-8 -*-
import string

from moose.utils import six
from moose.utils.module_loading import import_string
from moose.core.exceptions import ImproperlyConfigured
from . import sqlhandler

import logging
logger = logging.getLogger(__name__)

class BaseOperation(object):
    """
    Class to do the query operation.

    `operation_template`
        Template of sql statement to operate.

    `handler`
        An instance of moose.connection.sqlhandler.BaseSQLHandler.

    `table_alias`
        Dictionary containing information of map from aliases to tables' name.

    """
    operation_template = None
    base_handler_cls   = sqlhandler.BaseSQLHandler

    def __init__(self, handler):
        self.handler = handler

    @classmethod
    def create_from_context(cls, query_context):
        handler_cls      = query_context['sql_handler']
        handler_settings = query_context['sql_context']

        if isinstance(handler_cls, six.string_types):
            try:
                handler_cls = import_string(handler_cls)
            except ImportError as e:
                raise ImproperlyConfigured(\
                    "SQL handler specified is not an importable module: {}.".format(handler_cls))

        if issubclass(handler_cls, cls.base_handler_cls):
            handler = handler_cls(handler_settings)
        else:
            raise ImproperlyConfigured(\
                "Database handlers must be a subclass of {}.".format(cls.base_handler_cls))

        return cls(handler)


class BaseQuery(BaseOperation):

    def query(self, **context):
        try:
            operation = self.operation_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Key missing: {}".format(str(e)))
        # execute the query with context provided
        return self.handler.exec_query(operation)


class BaseGuidQuery(BaseQuery):
    """
    Class to query 'SourceGuid' and 'ResultGuid' according to various conditions.
    """

    operation_template = (
        "select dr.SourceGuid, dr.DataGuid from $tables where $conditions "
    )
    tables     = None
    conditions = None

    def __init__(self, handler):
        super(BaseGuidQuery, self).__init__(handler)
        self.operation_template = string.Template(self.operation_template).safe_substitute(
            tables = self.tables,
            conditions = self.conditions,
        )

class AllGuidQuery(BaseGuidQuery):
    """
    Get all records for a project.
    """
    tables = "$table_result dr"
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
    tables = "$table_result dr, $table_person ps"
    conditions = (
        "dr.ProjectId = {project_id} and dr.UserGuid = ps.ProviderUserKey and "
        "ps.Account in {accounts}"
    )

class TitlesGuidQuery(BaseGuidQuery):
    """
    Get records with specified titles in table `DataSource`.
    """
    tables = "$table_source ds, $table_result dr"
    conditions = (
        "ds.DataGuid = dr.SourceGuid and ds.ProjectId = {project_id} and "
        "dr.ProjectId = {project_id} and ds.Title in {titles}"
    )

class BaseUsersQuery(BaseQuery):

    operation_template = (
        "select DISTINCT pip.id, pip.PersonName $fields from "
        "$table_person_in_project pip, $table_person ps $tables where "
        "pip.ProjectId = {project_id} and pip.PersonId=ps.id $conditions"
    )

    fields = ""
    tables = ""
    conditions = ""

    def __init__(self, handler):
        super(BaseUsersQuery, self).__init__(handler)
        self.operation_template = string.Template(self.operation_template).safe_substitute(
            fields = self.fields,
            tables = self.tables,
            conditions = self.conditions,
        )


class UsersInProjectQuery(BaseUsersQuery):
    """
    Get information of users took part in a project. Note the 'id' returned is
    the same with the key '_personInProjectId' from the coll `result`(in mongodb).
    """
    fields = ", ps.Account"


class UserGuidInProjectQuery(BaseQuery):
    """
    Get user guid in project from name and project_id provided
    """
    operation_template = (
        "select ProviderUserGuid from $table_person_in_project "
        "where PersonName = '{user_name}' and ProjectId = {project_id}"
    )

class TeamUsersInProjectQuery(BaseQuery):
    """
    Get information of users took part in a project. Note the 'id' returned is
    the same with the key '_personInProjectId' in the table `result` in mongodb.
    """
    operation_template = """
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
                    $table_person_in_project pip, $table_person ps
                WHERE
                    pip.ProjectId = {project_id}
                AND pip.PersonId = ps.id
            ) AS person
        LEFT JOIN $table_person_in_team pit ON pit.ProviderUserKey = Person.ProviderUserGuid
    ) AS pat
LEFT JOIN $table_team AS t ON pat.TeamId = t.Id
"""

class DataSourceQuery(BaseQuery):

    operation_template = (
        "select * from $table_source ds where ds.ProjectId={project_id}"
    )

class DataResultQuery(BaseQuery):

    operation_template = (
        "select * from $table_result dr where dr.ProjectId={project_id}"
    )


class DataInfoQuery(BaseQuery):

    operation_template = (
        "select ds.Title, ds.FileName, dr.Status, dr.IsValid, dr.UserGuid, "
        "dr.SourceGuid, dr.DataGuid from $table_source ds, $table_result "
        "dr where ds.DataGuid=dr.SourceGuid and dr.ProjectId={project_id} "
        "and ds.ProjectId={project_id}"
    )

class ProjectInfoQuery(BaseQuery):

    operation_template = (
        "select * from $table_project where id={project_id}"
    )

class ProjectInfoByBatchQuery(BaseQuery):

    operation_template = (
        "select * from $table_project where batch='{batch_name}'"
    )

class AcqInfoByGuidQuery(BaseQuery):

    operation_template = (
        "select * from $table_acquisition where DataGuid= '{data_guid}'"
    )

class AcqInfoByUserQuery(BaseQuery):

    operation_template = (
        "select * from $table_acquisition WHERE ProjectId = {project_id} "
        "and UserGuid = '{user_guid}' and isValid = 1"
    )

class AcqToMarkByUserQuery(BaseQuery):

    operation_template = (
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'{create_time}' from $table_acquisition "
        "WHERE ProjectId = {acquisition_id} and UserGuid = '{user_guid}' "
        "and isValid = 1"
    )

class BaseInsert(BaseOperation):

    def execute(self, **context):
        try:
            operation = self.operation_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Key missing: {}".format(str(e)))
        # execute the query with context provided
        naffected = self.handler.exec_commit(operation)
        return naffected


class AcqToMarkByTitle(BaseInsert):

    operation_template = (
        "insert into $table_source (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,{create_time} from $table_acquisition "
        "WHERE ProjectId in ({acquisition_ids}) and substring(Title, 6, 5) in ({groups})"
    )

class AcqToMarkByUser(BaseInsert):

    operation_template = (
        "insert into $table_source (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'{create_time}' from $table_acquisition "
        "WHERE ProjectId = {acquisition_id} and UserGuid = '{user_guid}' "
        "and isValid = 1"
    )

class AcqToMarkByDataguid(BaseInsert):

    operation_template = (
        "insert into $table_source (ProjectID,Title,DataGuid,"
        "DataVersion,UserGuid,Duration,FileName,CreateTime) "
        "select {project_id},Title,DataGuid,DataVersion,UserGuid,"
        "Duration,FileName,'{create_time}' from $table_acquisition "
        "WHERE DataGuid = '{data_guid}' and isValid = 1"
    )


class BulkInsert(BaseOperation):

    def execute(self, params_seq, **context):
        try:
            operation = self.operation_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Key missing: {}".format(str(e)))
        # execute the query with context provided
        return self.handler.exec_many(operation, params_seq)


class BulkAcqToMarkByDataguid(BulkInsert):

    operation_template = (
        "insert into $table_source ({project_id},%s,%s,%s,%s,%f,%s,{create_time}) "
    )
