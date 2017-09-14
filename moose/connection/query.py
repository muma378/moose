# -*- coding: utf-8 -*-
import logging

from moose.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class BaseQuery(object):
    """
    Class to do the query operation.

    `statement_template`
        Template of sql statement to operate.

    `handler`
        An instance of moose.connection.database.BaseSQLHandler.

    `base_context`
        Dictionary containing information of tables and fields.

    """
    statement_template = None

    def __init__(self, handler, base_context):
        self.handler = handler
        self.base_context = base_context

    def query(self, **context):
        try:
            context.update(self.base_context)
            sql_statement = self.statement_template.format(**context)
        except KeyError as e:
            raise ImproperlyConfigured("Keys missing: %s" % e.message)
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

    def __init__(self, handler, base_context):
        super(BaseGuidQuery, self).__init__(handler, base_context)
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

class UsersInProjectQuery(BaseQuery):
    """
    Get information of users took part in a project. Note the 'id' returned is
    the same with the key '_personInProjectId' in the table `result` in mongodb.
    """
    statement_template = (
        "select DISTINCT pip.id, pip.PersonName, ps.Account from "
        "{table_person_in_project} pip, {table_person} ps where "
        "pip.ProjectId = {project_id} and pip.PersonId=ps.id"
    )
