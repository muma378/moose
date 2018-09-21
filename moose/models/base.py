# -*- coding: utf-8 -*-
import os
import copy
import json
import inspect

from moose.utils._os import makedirs, makeparents, safe_join
from moose.utils.encoding import force_bytes, iri_to_uri
from moose.conf import settings
from . import fields

import logging
logger = logging.getLogger(__name__)

class FieldMissing(Exception):
    """Required field is not provided"""
    pass

class FieldInvalid(Exception):
    """Required field is somehow invalid"""
    pass

class BaseModel(object):
    """
    Model is a object to parse the annotation for templates, it aims to
    eliminate the difference between projects with the same template. By providing
    an unified interface, the diversity of implementation can be ignored.
    """
    output_suffix = '.json'
    effective_values = ('1', 1, 'true')


    def __init__(self, annotation, app, stats, **context):
        self.annotation = annotation
        self.source = annotation['source']
        self.result = annotation['result']
        self.app    = app
        self.stats  = stats
        self.context = context
        self._active()
        self.set_base_context(context)

    def _active(self):
        # get method resolution orders
        for klass in inspect.getmro(self.__class__):
            # get class static variables not all properties
            for field, obj in klass.__dict__.items():
                if isinstance(obj, fields.AbstractMappingField):
                    # replace the field-object with real value
                    self.__setattr__(field, obj.get_val(self.annotation))

    def set_base_context(self, context):
        self.title   = context['title']
        self.task_id = str(context['task_id'])
        self.set_context(context)

    def set_context(self, context):
        """
        Entry point for subclassed models to set custom context
        """
        pass

    def set_up(self):
        """
        Entry point for subclassed models to prepare before downloading
        """
        pass

    @property
    def filepath(self):
        raise NotImplementedError

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    @property
    def normpath(self):
        return os.path.normpath(self.filepath)

    @property
    def name(self):
        name, _ = os.path.splitext(self.filename)
        return name

    @property
    def dest_root(self):
        return safe_join(self.app.data_dirname, self.title)

    @property
    def dest_filepath(self):
        return safe_join(self.dest_root, self.filepath)

    @property
    def guid(self):
        return self.result['_guid']

    @property
    def user_id(self):
        return self.result['_personInProjectId']

    @property
    def datalink(self):
        return settings.DATALINK_TEMPLATE.format(task_id=self.task_id, data_guid=self.guid)

    @property
    def filelink(self):
        iri = settings.AZURE_FILELINK.format(task_id=self.task_id, file_path=self.filepath)
        return iri_to_uri(iri)

    # when the property `effective` or `Effective` was existed,
    # return true if the value was '1'
    def is_effective(self):
        if self.result.has_key("effective"):
            return self.result['effective'] in self.effective_values
        elif self.result.has_key("Effective"):
            return self.result['Effective'] in self.effective_values
        else:
            raise NotImplementedError("Unknown property to get the validity.")

    def clean_result(self):
        result = copy.deepcopy(self.result)
        for k in result.keys():
            if k.startswith('_'):
                result.pop(k)
        return result

    @property
    def data(self):
        raise NotImplementedError("Subclass of BaseModel must provide data() method.")

    def to_string(self):
        return force_bytes(json.dumps(self.data, ensure_ascii=False))

    @property
    def user_info(self):
        if self.context.has_key('users_table'):
            try:
                return self.context['users_table'][self.user_id]
            except KeyError as e:
                return (None, None)
                raise FieldInvalid(\
                    "Unable to find id:'{}' in `users_table`.".format(self.user_id))
        else:
            raise FieldMissing("Field `users_table` is missing in the context.")

    def overview(self):
        return [self.filepath, self.datalink, ] + list(self.user_info)


class BaseTaskInfo(object):
    def __init__(self):
        pass

    @classmethod
    def create_from_task_id(cls, task_id):
        pass

    @classmethod
    def create_from_title(cls, title):
        pass

    @property
    def users_table(self):
        pass
