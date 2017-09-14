
query_all = (
    "select dr.SourceGuid, dr.DataGuid from {table_result} dr where "
    "dr.ProjectId = {project_id}"
    )

STATUS = {
    "default": 0,
    "pass": 1,
    "refuse": 2,
    "revised": 3,
}

# check result for records
query_status = (
    "select dr.SourceGuid, dr.DataGuid from {table_result} dr "
    "where dr.ProjectId = {project_id} and dr.status = {status}"
    )

query_accounts = (
    "select dr.SourceGuid, dr.DataGuid from {table_result} dr, {table_person} ps "
    "where dr.ProjectId = {project_id} and dr.UserGuid = ps.ProviderUserKey and "
    "ps.Account in {accounts}"
    )

query_titles = (
    "select dr.SourceGuid, dr.DataGuid from {table_source} ds, {table_result} dr "
    "where ds.DataGuid = dr.SourceGuid and ds.ProjectId = {project_id} and "
    "dr.ProjectId = {project_id} and ds.Title in {titles}"
    )

# first time to create
query_ctime = (
    "select dr.SourceGuid, dr.DataGuid from {table_result} dr "
    "where dr.ProjectId = {project_id} and dr.Date {less_or_more} '{datetime}'"
    )

# last edit time
query_atime = (
    "select dr.SourceGuid, dr.DataGuid from {table_result} dr "
    "where dr.ProjectId = {project_id} and dr.LastEditTime {less_or_more} '{datetime}'"
    )

query_source = (
    "select ds.DataGuid, ds.title from {table_source} ds where "
    "ds.ProjectId = {project_id}"
    )

list_users = (
    "select DISTINCT pip.id, pip.PersonName, ps.Account from {table_person_in_project} pip, "
    "{table_person} ps where pip.ProjectId = {project_id} and pip.PersonId=ps.id"
    )

# exec sp_help 'tablename'
list_columns = (
    "select COLUMN_NAME from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME = {table_name}"
    )
