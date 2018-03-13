# -*- coding: utf-8 -*-
import os
import json
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
    member_cls = None
    mark_key = None

    def __init__(self, annotation):
        super(Collection, self).__init__(annotation)
        if not getattr(self, 'mark_results'):
            raise NotImplementedError(
                "Subclass of 'Collection' must implement 'mark_results' to specify the "
                "attribute possess annotation data.")
        self.members = []
        for mark_result in self.mark_results.get(self.mark_key):
            self.members.append(self.member_cls(mark_result))

    @property
    def filename(self):
        raise NotImplementedError(
            "Subclass of 'GroupModel' are not allowed to implement property 'filename'."
            "Are you looking for 'filenames'?"
            )

    @property
    def filepath(self):
        raise NotImplementedError(
            "Subclass of 'GroupModel' are not allowed to implement property 'filepath'."
            "Are you looking for 'filepathes'?"
            )

    @property
    def name(self):
        raise NotImplementedError(
            "Subclass of 'GroupModel' are not allowed to implement property 'name'."
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
    def __init__(self, annotation):
        self.annotation = annotation

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
    def data(self):
        raise NotImplementedError("Subclass of MemberModel must provide data() method.")

    def to_string(self):
        return json.dumps(self.data, ensure_ascii=False).encode('utf-8')

    def export(self, root):
        filepath = os.path.join(root, self.normpath)
        makeparents(filepath)
        filename, _ = os.path.splitext(filepath)
        filepath = filename + self.output_suffix
        with open(filepath, 'w') as f:
            f.write(self.to_json())
