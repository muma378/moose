.. _topics-models:

=================
模型（Model）
=================

外部世界的数据总是复杂的。它们形态万千，格式不一。一方面，同一数据可能会使用JSON，XML或CSV等格式去表示；另一方面，两套数据内部即使意义相同的字段也可能会使用不同的名称去命名，或者用不同的格式来组织。就像通天塔的寓言——上帝为了阻止人类建造通往天堂的高塔而发明了不同的语言。毫无疑问，不同的数据格式给我们的工作也带了不少的麻烦。

类似于经典的 MVC模式_ 通过控制器（Controller）解耦模型（Model）和视图（View），我们通过抽象出Model对象来适配不同的数据格式，使得在其上的各种动作（Action）可以使用相同的接口。我们会在接下来的一节讲述该模块的接口。

.. module:: moose.models
   :synopsis: Models base class and common interfaces, fields class.

.. _topics-models-ref:

moose.models.BaseModel
=========================

.. class:: BaseModel(annotation)

    BaseModel是所有model的基类，它定义了model子类应该包含的属性并且提供了默认实现。

    首先，它读取一个标准格式的标注记录，该记录从数据库中获取，并被组织成一致的格式（{"source": {x: y}, "result": {a: b}}）；然后，会根据我们在声明中对 *Field* 的定义，将字典中的各个字段映射成该对象的属性；最后，我们通过实现规定的接口，保证不同的数据格式提供了一套统一的接口。

    :param annotation: ``annotation`` 代表了一条数据的原始信息和标注结果，它们分别被存放在MongoDB中名为 ``source`` 和 ``result`` 的Document（文档）中，通过 :class:`~moose.connection.fetch` 查询并提取出来。
    :type annotation: dict

    .. attribute:: source

        从MongoDB的Document ``source`` 里取到的所有内容。代表数据上传时的索引文件的内容，一般包含 *url* ，*dataTitle* 等信息。

    .. attribute:: result

        从MongoDB的Document ``result`` 里取到的所有内容。代表图像/文本/音频的标注结果，一般（可能）包含 *Workload* （工作量统计），*effective* （数据有效性）， *markResult* （标注结果集合）等信息。

    .. attribute:: effective_values

        定义了标注结果中的 *effective* 为True的值的集合，默认为 ``('1', 1)``。修改该值会对方法 :meth:`is_effective` 产生影响，

    .. attribute:: output_suffix

        导出文件的后缀名，默认为 ``.json`` 。

    .. method:: _active()

        实例化类体中定义的各个字段，将 ``source`` 和 ``result`` 中的字段映射成该对象的属性。该方法一般不需要覆盖和重载。

    .. method:: filepath()

        ``@property`` ``abstract``

        该方法带有装饰器@property ，以使其表现出属性的特点但是可以被重载。子类必须继承并且实现该方法，并且返回被标注对象的相对路径。

    .. method:: filename()

        ``@property``

        返回文件名，即 ``os.path.basename(self.filepath)`` 。

    .. method:: normpath()

        ``@property``

        返回文件在当前系统的标准路径，即 ``os.path.normpath(self.filepath)`` 。

    .. method:: data()

        ``@property`` ``abstract``

        该方法带有装饰器@property ，以使其表现出属性的特点但是可以被重载。子类必须继承并且实现该方法，并且返回标注结果的可读形式。

    .. method:: guid()

        ``@property``

        返回该条标注结果的 ``guid``。

    .. method:: user_id()

        ``@property``

        返回标注该条数据的用户的 ``personInProjectId`` 字段，该字段可以用来查询对应的用户名及账号。

    .. method:: datalink(task_id)

        该条数据的标注链接。

        :param str task_id: 该条数据对应的任务期数。

    .. method:: filelink(task_id)

        被标注对象文件的url。

        :param str task_id: 该条数据对应的任务期数。

    .. method:: clean_result()

        移除掉所有以"_"开头的字段后的字典 ``result`` 。

    .. method:: to_string()

        ``data`` 返回结果的JSON格式的字符串形式，使用 ``utf-8`` 编码。


我们可以展示一个常见的实现：::

    from moose.models import BaseModel, fields

    class UigurlangModel(BaseModel):
        """
        @template_name: 图像文本单词转写V1.0
        """
        mark_result = fields.ResultMappingField(prop_name='markResult')

        @property
        def filepath(self):
            return self.source['fileName']

        @property
        def data(self):
            return self.mark_result

示例中对 :class:`~moose.models.BaseModel` 的 :meth:`~.filepath` 和 :meth:`~.data` 提供了实现，并且将 ``annotation['result']['markResult']`` 里的值映射到了属性 ``mark_result``。

需要注意的是，这里 :meth:`~.data` 返回的内容正好就是 ``annotation['result']['markResult']`` 。另外一些时候，我们可能需要对标注结果（比如 ``mark_result`` ）里的内容进行修改——移除部分无用字段、改变数据结构、重新进行计算部分结果等等，这个时候就需要对 :meth:`~.data` 进行更多细节的实现，保证返回的结果是我们需要的人类可读（human-readable）的格式。


moose.models.GeoJSONModel
=========================

.. class:: GeoJSONModel(annotation)

    GeoJSONModel是 :class:`~moose.models.BaseModel` 的子类，继承了所有的属性和方法。除此之外，根据 `RFC 7946`_ 对 GeoJSON_ 的定义，提供了一些额外的方法去直接访问其中的属性，以跳过过多的嵌套和循环。

    .. attribute:: mark_result

        对 ``result`` 字典中 ``markResult`` 字典的映射，默认实现为::

            mark_result = fields.ResultMappingField(prop_name='markResult')

        如果不是该字段(markResult)表示标注结果的集合，需要对 ``prop_name`` 进行修改。

    .. method:: ifeatures():

        ``@property``

        生成器，被迭代调用以依次返回标注结果的多边形对象（``feature['geometry']``）和对应的属性(``feature['properties']``)。

    .. method:: icoordinates()

        ``@property``

        生成器，被迭代调用以依次返回标注结果的多边形的坐标值(``geometry['coordinates']``)。


同样的，这里我们也展示一个使用 :class:`~moose.models.GeoJSONModel` 的例子：::

    from moose import models

    class SatelliteModel(models.GeoJSONModel):
        """
        @template_name: 卫星图片标注V2.1
        """
        @property
        def filepath(self):
            return self.source['url']

        @property
        def data(self):
            segmentations = []
            for geometry, properties in self.ifeatures:
                segmentations.append({
                    'category': properties['type']['currentDataKey'],
                    'coordinates': geometry['coordinates'],
                })
            return segmentations

示例中的 ``SatelliteModel`` 同样对 :meth:`~.filepath` 和 :meth:`~.data` 提供了实现，但是稍有不同的是，在方法 :meth:`~.data` 中，通过对 :meth:`~.ifeatures` 的迭代，我们获得了所有的被标注对象的标签和坐标值，将其组装并返回。


.. _topics-fields-ref:

moose.models.fields
=====================

通过上面两个例子，大家基本能了解到，所谓Model对数据的建模，是对外部数据进行计算和重组，以使其表现出更一致和更有意义的接口。就像把乐高积木的一块块组件搭建起来，构成一个有门有窗有塔楼的城堡一样。即使每套乐高积木的组件可能不尽相同，但是我们总能通过一些转换和搭配组装起一个基本功能一致的城堡。

与此同时，对于那些不需要计算和重组等复杂操作的数据，我们提供了 ``fields`` 这一模块，用以完成字典的键到类的属性的映射，避免多层嵌套的引用。


fields.AbstractMappingField
----------------------------

.. class:: fields.AbstractMappingField

    抽象类，定义了 get_val() 这一虚函数，它的所有子类都应实现该方法。


fields.CommonMappingField
----------------------------

.. class:: fields.CommonMappingField(dict_name, prop_name, default=None)

    :class:`~.AbstractMappingField` 的子类，定义了对 ``source`` 或 ``result`` 表的键值的映射。

    :param str dict_name: 只能为 ``source`` 或 ``result``，代表所选择映射的表；
    :param str prop_name: 代表 ``source`` 或 ``result`` 对应表中的键名；
    :param default: ``prop_name`` 不存在是默认返回的值。

    .. method:: get_val(anno):

        从对应表（dict_name）中取出对应键值（prop_name）的过程。 ::

            def get_val(self, anno):
        		return anno[self.dict_name].get(self.prop_name, self.default)

        :param dict anno: 同 :class: `~.BaseModel` 的实例化参数 ``annotation`` 一样，通过 :class:`~moose.connection.fetch` 查询并提取出来的结果。

fields.SourceMappingField
----------------------------

.. class:: fields.SourceMappingField(prop_name, default=None)

    :class:`~.CommonMappingField` 的子类，定义了对 ``source`` 表的键值的映射。

    .. attribute:: dict_name

        为常量"source"。


fields.ResultMappingField
----------------------------

.. class:: fields.ResultMappingField(prop_name, default=None)

    :class:`~.CommonMappingField` 的子类，定义了对 ``result`` 表的键值的映射。

    .. attribute:: dict_name

        为常量"result"。


fields.LambdaMappingField
----------------------------

.. class:: fields.LambdaMappingField(lambda_fn)

    :class:`~.AbstractMappingField` 的子类，定义了匿名函数 ``lambda_fn`` 完成相应的函数映射。

    :param lambda lambda_fn: 定义了从 ``anno`` 到 ``fn(anno)`` 的过程映射。


下面这个例子你已经见到过了，我们稍作了修改： ::

    from moose.models import BaseModel, fields

    class UigurlangModel(BaseModel):
        """
        @template_name: 图像文本单词转写V1.0
        """
        file_name = fields.SourceMappingField(prop_name='url')
        mark_result = fields.ResultMappingField(prop_name='markResult')

        @property
        def data(self):
            return {
                "filename": self.file_name,
                "data": self.mark_result
                }

其中 ``data`` 与下面的例子是一样的作用： ::

    class UigurlangModel(BaseModel):

        @property
        def data(self):
            return {
                "filename": self.source['url'],
                "data": self.result['markResult']
                }

看起来似乎下面这种写法更简洁，然而当实际操作中你被无尽的 ``[]`` 和 ``''`` 淹没的时候，就不会这样认为了！


.. _MVC模式: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller
.. _GeoJSON: http://geojson.org/
.. _RFC 7946: https://tools.ietf.org/html/rfc7946
