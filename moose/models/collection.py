# -*- coding: utf-8 -*-
import os
import json
import inspect
from . import BaseModel
from . import fields
from moose.utils._os import makeparents


class Collection(BaseModel):
    """
    Model for the annotation on a group of images. They are usually for tracking,
    clustering and recognition in terms of a theme.
    Therefore, there are multiple annotation and files in a model, it is more like
    a manager class than a model.
    """
    member_cls   = None
    mark_key     = None
    mark_results = None

    def __init__(self, annotation, app, stats, **context):
        super(Collection, self).__init__(annotation, app, stats, **context)
        self.members = self.create_members()

    def create_members(self):
        members = []
        for mark_result in self.fetch_one():
            member_obj = self.member_cls(mark_result, self.app, self.stats, **self.context)
            members.append(member_obj)
        return members

    def fetch_one(self):
        if not getattr(self, 'mark_results'):
            raise NotImplementedError(
                "Subclass of 'Collection' must implement 'mark_results' to specify the "
                "attribute of annotation data.")
        for item in self.mark_results.get(self.mark_key):
            yield item

    @property
    def filename(self):
        raise NotImplementedError(
            "Subclass of 'Collection' are not allowed to implement property 'filename'."
            "Are you looking for 'filenames'?"
            )

    @property
    def filepath(self):
        raise NotImplementedError(
            "Subclass of 'Collection' are not allowed to implement property 'filepath'."
            "Are you looking for 'filepathes'?"
            )

    @property
    def name(self):
        raise NotImplementedError(
            "Subclass of 'Collection' are not allowed to implement property 'name'."
            "Are you looking for 'names'?"
            )

    def get_children_attr(self, attr_name):
        return [getattr(m, attr_name) for m in self.members]

    @property
    def filenames(self):
        return self.get_children_attr('filename')

    @property
    def filepathes(self):
        return self.get_children_attr('filepath')

    @property
    def names(self):
        return self.get_children_attr('name')

    @property
    def data(self):
        return self.get_children_attr('data')

# duck interface
class MemberModel(object):
    output_suffix = '.json'

    def __init__(self, annotation, app, stats, **context):
        self.annotation = annotation
        self.app   = app
        self.stats = stats
        self.context = context
        self.set_base_context(context)
        self._active()

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
        pass

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    @property
    def filepath(self):
        raise NotImplementedError

    @property
    def normpath(self):
        return os.path.normcase(self.filepath)

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
    def filelink(self):
        return settings.AZURE_FILELINK.format(task_id=self.task_id, file_path=force_bytes(self.filepath))

    @property
    def data(self):
        raise NotImplementedError("Subclass of MemberModel must provide data() method.")

    def to_string(self):
        return json.dumps(self.data, ensure_ascii=False).encode('utf-8')
