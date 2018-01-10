# -*- coding: utf-8 -*-
import os
import time
import json
import logging
from moose import actions
from moose.connection import database
from moose.connection.cloud import azure
from moose.connection.query import AllGuidQuery
from moose.connection.fetch import BaseFetcher
from demo import settings
from demo.settings import DATABASES

logger = logging.getLogger('moose.actions')

class Upload(actions.AbstractAction):
    def run(self, **kwargs):
        config = kwargs.get('config')
        time.sleep(2)
        logger.info("upload files in '%s'" % config.common['root'])
        containers = azure.list_containers()
        return "upload files in '%s'" % config.common['root']


class Export(actions.AbstractAction):
    def run(self, **kwargs):
        sqlserver = MySQLHandler(DATABASES['mysql'])
        return "export"

class StandardUpload(actions.upload.BaseUpload):
    pass


class PastTasksUpload(actions.upload.BaseUpload):
    def parse(self, kwargs):
        context = super(PastTasksUpload, self).parse(kwargs)
        config = kwargs.get('config')
        context.update({
            'refered_task': config.upload['refered_task']
        })
        return context

    def explore(self, context):
        refered_task = context['refered_task']
        files = self.azure.list_blobs(refered_task)
        # database_config = DATABASES['sqlserver']
        # engine = AllGuidQuery(SQLServerHandler(database_config), database_config['TABLE_ALIAS'])
        # queryset = engine.query(project_id=refered_task)
        context = {
            'sql_hander': database.SQLServerHandler,
            'sql_context': DATABASES['sqlserver'],
            'mongo_handler': database.MongoDBHandler,
            'mongo_context': DATABASES['mongo'],
        }

        fetcher = BaseFetcher(AllGuidQuery, context)
        queryset = fetcher.fetch(project_id=refered_task)
        annotated_files = [q['source']['fileName'].replace('\\', '/') for q in queryset]
        files = filter(lambda x: x not in annotated_files, files)
        return files

    def schedule(self, files, context):
        yield context['task_id'], files

    def index(self, blob_pairs, context):
        refered_task = context['refered_task']
        catalog = []
        for blobname in blob_pairs:
            item = {
                'url': settings.AZURE_FILELINK.format(task_id=refered_task, file_path=blobname),
                'dataTitle': blobname,
            }
            catalog.append(json.dumps(item, ensure_ascii=False).encode(settings.FILE_CHARSET))
        return '\n'.join(catalog)

    def run(self, **kwargs):
        context = self.parse(kwargs)
        files = self.explore(context)
        output = []
        for container_name, blob_pairs in self.schedule(files, context):
            index_file = os.path.join(self.app.data_dirname, container_name+'.json')
            with open(index_file, 'w') as f:
                f.write(self.index(blob_pairs, context))
                logger.info("Index content are written to: %s" % index_file)
            output.append("%s files were found in [%s]." % (len(blob_pairs), container_name))
        return '\n'.join(output)
