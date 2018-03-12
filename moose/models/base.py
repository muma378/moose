# -*- coding: utf-8 -*-
import os
import copy
import json
import inspect

from moose.utils._os import makedirs
from moose.utils.encoding import force_bytes
from moose.conf import settings
import fields

class BaseModel(object):
    """
    Model is a object to parse the annotation for templates, it aims to
    eliminate the difference between projects with the same template. By providing
    an unified interface, the diversity of implementation can be ignored.
    """
    output_suffix = '.json'
    effective_values = ('1', 1)

    def __init__(self, annotation):
        self.annotation = annotation
        self.source = annotation['source']
        self.result = annotation['result']
        self._active()

    def _active(self):
        # get method resolution orders
        for klass in inspect.getmro(self.__class__):
            # get class static variables not all properties
            for field, obj in klass.__dict__.items():
                if isinstance(obj, fields.AbstractMappingField):
                    # replace the field-object with real value
                    self.__setattr__(field, obj.get_val(self.annotation))

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
    def guid(self):
        return self.result['_guid']

    @property
    def user_id(self):
        return self.result['_personInProjectId']

    def datalink(self, task_id):
        return settings.DATALINK_TEMPLATE.format(data_guid=self.guid, task_id=str(task_id))

    def filelink(self, task_id):
        return settings.AZURE_FILELINK.format(task_id=str(task_id), file_path=force_bytes(self.filepath))

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


class BaseTaskInfo(object):
    def __init__(self, task_name):
        pass
