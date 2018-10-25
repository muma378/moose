.. _topics-drawer:

====================
图形绘制（Drawer）
====================

数据处理中常见的一类工作就是对标注结果的可视化处理，通过将标注的点、线、矩形、多边形等图形绘制到原始
图像上，使得对标注效果可以做快速判断。另一方面，相比于坐标点集合的JSON文件，有些人更偏爱使用
mask图进行图像识别方面的训练，换句话说，这要求将标注结果绘制到一张与原始图像同样大小的黑色的
画布上。

然而在实际情况中，同一张图片往往包含多种图形的标注，例如街景标注中，可能既包含车道线（线），人、车（
多边形）的标注，也需要框出所有的交通灯和交通标志（矩形框）。而且，在绘制的时候，根据标注的实际情况，
绘制方法可能是轮廓也可能是填充。如何既提供通用快速的绘制接口，又能根据实际情况进行扩展（改变绘制方法
、颜色、粗细等），就是 ``toolbox.image.drawer`` 的设计目的。

因此，我们将 ``Shape(图形)`` 这一对象抽象出来，提供了验证和绘制的接口，并且提供默认的绘制实现，
调用绘制接口在图上进行绘制则由 ``Painter(绘制器)`` 完成。开发人员只需要关注图形的初始化和绘制方法
的实现即可。


.. module:: moose.toolbox.image.drawer
   :synopsis: Self-adaptive shapes drawing functions.

.. _topics-shapes-ref:

Shapes（图形）
=========================

**Shapes** 是对被绘制图形的抽象，提供了一系列的绘制图形的基础属性如形状、颜色、线宽等，也提供
了对坐标值的格式进行验证、标准化、绘制的方法。


.. class:: BaseShape(coordinates, label, color=None, filled=None, thickness=None, **options)

    BaseShape是所有图形类的基类，它定义了Shape子类应该包含的属性、需要实现的接口并且为通用
    方法提供了默认实现。

    :param list coordinates: 表示图形的坐标点的集合。对于不同的图形可能有不同的格式要求，例如对于点，
        要求 **coordinates** 的值是包含两个元素的列表 ``[x, y]`` ，对于多边形，要求是 ``[[x1, y1],
        [x2, y2] ... [xn, yn], [x1, y1]]`` 的格式，等等。对于具体格式的检查在 ``_is_valid_coordinates()``
        中有相应的实现。
    :param str label: 该图形对应物体的标签。
    :param tuple color: 该图形被绘制时的颜色，可以是一个整型（灰度图）也可以是包含三个整型的元组（RGB）。
        默认值是 ``default_color = settings.DEFAULT_COLOR`` 。
    :param boolean filled: 该图形被绘制时是采用内部填充的方式还是绘制轮廓的方式，默认值根据类变量
        ``drawn_filled`` 决定，对于线、点等图形不发挥作用。
    :param int thickness: 该图形被绘制时的线的粗细，默认值为 ``default_thickness = settings.DEFAULT_THICKNESS``
    :param dict options: 其他的可选项参数。


    .. attribute:: type

        类变量，表征该绘制图形的名称，如 **Polygon，Point，Rectangle** 等。

    .. method:: _is_list_of_pairs(points)

        ``@classmethod``

        :param tuple points: 坐标点。

        返回bool值，该方法通过调用is_valid_format()和is_valid_value()来对输入点进行校验。

    .. method:: is_valid_format(point)

        ``@classmethod``

        :param tuple point: 坐标点。

        返回bool值，该方法用来判断输入点的类型是否为列表或者元祖，且长度是否为2，若满足则返回 ``True`` ，否则为 ``False`` 。

    .. method:: is_valid_value(point)

        ``@classmethod``

        :param tuple point: 坐标点。

        返回bool值，该方法用来判断输入点中元素是否是整数（或者为可以转换成整数的字符串）。

    .. method:: _equal_points(p1, p2)

        ``@classmethod``

        :param tuple p1: 坐标点。
        :param tuple p2: 坐标点。

        返回bool值，该方法用来判断输入的两个点是否完全相等（x，y是否分别对应相等）。

    .. method:: _is_valid_coordinates(coordinates)

        :param list coordinates: 坐标列表。

        对传入的坐标参数进行校验，默认返回 ``True`` ，子类根据具体图形实现自己的校验方式。

    .. method:: normalize(coordinates)

        :param list coordinates: 表示图形的坐标点的集合。

        该方法是将输入的坐标进行格式化（将其元素中的浮点数转换为 ``int`` ，并将列表转换为 ``tuple`` ）。返回一个内部元素为元祖的列表。

    .. method:: set_color(color)

        :param str color: 颜色。

        设置绘制颜色，如果输入的color为 ``None``，则使用默认的颜色，否则使用输入的颜色。

    .. method:: color()

        ``@property``

        返回该图形的绘制颜色。
        需要注意的是，因为 ``OpenCV`` 中(R, G, B)是反向的，如果 ``self._color`` 是 ``list`` 或者 ``tuple``
        则对其逆序。

    .. method:: draw_on(im)

        :param object im: ``OpenCV`` 图形对象。

        图形被绘制的主要接口，定义了绘制时的默认行为，如果 ``self._filled`` 为 ``True`` ，
        则使用填充方式绘制，否则使用绘制轮廓。

    .. method:: _fill(im)

        ``abstract``

        :param object im: ``OpenCV`` 图形对象。

        该方法用来在被标注对象文件上使用图像上的颜色填充形状，为预留接口，子类必须继承并且实现该方法。

    .. method:: _outline(im)

        ``abstract``

        :param object im: ``OpenCV`` 图形对象。

        该方法用来在被标注对象文件上绘制轮廓的形状，为预留接口，子类必须继承并且实现该方法。


.. class:: Point(BaseShape)

    **Point** 是BaseShape的子类，它定义了图形 **点** 的具体实现。

    .. attribute:: type

        默认值为 **"Point"** 。

    .. attribute:: radius

        定义绘制图形点的半径，默认值为 ``settings.DRAWER_RADIUS``

    .. method:: _is_valid_coordinates(coordinates)

        :param tuple coordinates: 表示图形点的坐标点的集合。

        判断输入格式是否为 ``[x, y]`` 的形式。

    .. method:: draw_on(im)

        :param object im: ``OpenCV`` 图形对象。

        调用 ``cv2.circle`` 进行绘制，具体实现如下：::

            cv2.circle(im, self._coordinates, self.radius, self.color, -1)

.. class:: LineString(BaseShape)

    **LineString** 是BaseShape的子类，它定义了图形 **线** 的具体实现。

    .. attribute:: type

        默认值为 **"LineString"** 。

    .. method:: _is_valid_coordinates(coordinates)

        :param list coordinates: 表示图形线的坐标点的集合。

        判断坐标是否按照 ``[[x0, y0], [x1, y1]]`` 或 ``[[x0, y0], [x1, y1], [x2, y2]]``
        的格式传入。

    .. method:: draw_on(im)

        :param object im: ``OpenCV`` 图形对象。

        调用 ``cv2.line`` 进行绘制，具体实现如下：::

            for start, end in zip(self._coordinates[:-1], self._coordinates[1:]):
                cv2.line(im, start, end, self.color, self._thickness)


.. class:: Polygon(BaseShape)

    **Polygon** 是BaseShape的子类，它定义了图形 **多边形** 的具体实现。与 **点** 和 **线**
    不同的是，在绘制时既可以填充也可以绘制轮廓，默认情况下，我们使用填充的方式进行绘制。

    .. attribute:: type

        默认值为 **"Polygon"**

    .. attribute:: is_closed

        定义该类绘制图形的形状是否是封闭的。

    .. attribute:: drawn_filled

        默认为 ``True`` ，即绘制时默认使用填充的方式。

    .. method:: _is_valid_coordinates(coordinates)

        :param list coordinates: 坐标。

        判断输入点是否是 ``[[x1, y1], [x2, y2] ... [xn, yn], [x1, y1]]`` 的格式。

    .. method:: to_nparray()

        返回将坐标点转换成 ``np.array`` 对象的表示，其中每个元素类型为 ``np.int32`` 。

    .. method:: _fill(im)

        调用 ``cv2.fillPoly`` 进行绘制，具体实现如下：::

            cv2.fillPoly(im, [self.to_nparray()], self.color)


    .. method:: _outline(im)

        调用 ``cv2.polylines`` 进行绘制，具体实现如下：::

            cv2.polylines(im, [self.to_nparray()], self.is_closed, self.color, self._thickness)


.. class:: Rectangle(BaseShape)

    **Rectangle** 是BaseShape的子类，它定义了图形 **矩形** 的具体实现。与 **点** 和 **线**
    不同的是，在绘制时既可以填充也可以绘制轮廓，默认情况下，我们使用绘制轮廓的方式进行绘制。

    .. attribute:: type

        默认值为 **"Rectangle"**

    .. attribute:: drawn_filled=False

        默认为 ``False`` ，即绘制时默认使用绘制轮廓的方式。

    .. method:: _is_valid_coordinates(coordinates)

        :param list coordinates: 坐标。

        判断输入点是否为 ``[[x1, y1], [x2, y2]]`` 的形式。

    .. method:: from_region(region, label, **options)

        ``@classmethod``

        :param list region: 坐标。
        :param str label:   标签。
        :param dict options: 其他可选参数。

        当坐标点格式为 ``[x, y, w, h]`` 调用此类方法来实例化。

    .. method:: from_points(points, label, **options)

        ``@classmethod``

        :param tuple coordinates: 坐标。
        :param str label: 标签。
        :param dict options: 其他可选参数。

        当坐标点格式为 ``[[x1, y1], [x1, y2], [x2, y2,], [x2, y1], [x1, y1]]`` 调用此类方法来实例化。

    .. method:: to_points()

        输出按照 ``[[x1, y1], [x1, y2], [x2, y2,], [x2, y1], [x1, y1]]`` 形式的坐标点表示。

    .. method:: _outline(im)

        调用 ``cv2.rectangle`` 进行绘制，具体实现如下：::

            cv2.rectangle(im, tuple(self._coordinates[0]), tuple(self._coordinates[1]), self.color, self._thickness)


    .. method:: _fill(im)

        调用 ``cv2.rectangle`` 进行绘制，具体实现如下：::

            cv2.rectangle(im, tuple(self._coordinates[0]), tuple(self._coordinates[1]), self.color, -1)


.. _topics-painter-ref:

Painter（绘制器）
=========================

.. class:: GeneralPainter(image_path, pallet=None, autofill=False, use_default=False, persistent=True)

    **GeneralPainter** 提供了整合多个图形，对图像按照多种方式进行绘制的能力。为 ``GeneralPainter``
    提供图片的完整路径和待绘制的 ``Shapes`` 列表，即可输出效果图（draw），掩模图（masking）
    和合成图（blend）。对于输出图形的颜色，既可以在实例化 ``Shapes`` 的时候定义，也可以向
    ``GeneralPainter`` 提供一个pallet（调色板），指定每个label和color的映射关系，来控制
    图形绘制颜色的选择。

    :param str image_path: 图片路径，如果不存在会抛出 ``IOError`` 。
    :param dict pallet: 标签和颜色的映射表，提供了 ``shape`` 的label对应的颜色。
    :param bool autofill: 当 ``shape`` 的label在 ``pallet`` 中不存在时，是否随机生成
        一个颜色，如果为 ``False`` 时，会抛出 ``ImproperlyConfigured`` 。
    :param bool use_default: 为 ``True`` 时，使用 ``shape`` 的color属性的值作为绘制的
        颜色。
    :param bool persistent: 当 ``autofill`` 为 ``True`` 时，是否所有图形绘制使用相同的
        label到color的映射。

    .. attribute:: shape_line_cls

        指定实例化图形 **线** 的类，默认为 ``LineString``。

    .. attribute:: shape_point_cls

        指定实例化图形 **点** 的类，默认为 ``Point``。

    .. attribute:: shape_polygon_cls

        指定实例化图形 **多边形** 的类，默认为 ``Polygon``。

    .. attribute:: shape_rectangle_cls

        指定实例化图形 **矩形** 的类，默认为 ``Rectangle``。


    .. method:: get_color(label)

        :param str label: 图形标签

        返回图形标签对应的颜色，该值受 ``pallet`` ， ``autofill`` ， ``use_default`` 的影响，有以下三种可能：

        1. 当 ``use_default`` 为 ``True`` 的时候，返回 ``None`` ；
        2. 当 ``use_default`` 为 ``False`` ，``pallet`` 包含该label对应的color，返回该值；
        3. 当 ``use_default`` 为 ``False`` ，``pallet`` 不包含该label，且 ``autofill`` 为 ``True`` 时，随机返回一种颜色；

    .. method:: add_color(label, color)

        :param str label: 图形标签
        :param tuple color: 颜色

        添加一对标签和颜色的对应关系到 ``pallet`` 中。

    .. method:: update_pallet(pallet)

        :param dict pallet: 标签和颜色的映射表

        更新 ``pallet`` 的标签和颜色的映射。

    .. method:: add_shape(shape)

        :param object shape: 图形对象

        添加一个待绘制的图形对象。

    .. method:: from_shapes(shapes)

        :param list shapes: 图形对象列表或生成器

        添加多个待绘制的图形对象。

    .. method:: clear()

        清空待绘制的图形对象列表。

    .. method:: add_line(p1, p2, label, **options)

        :param tuple p1: 点坐标
        :param tuple p2: 点坐标
        :param str label: 图形标签
        :param dict options: 参数

        实例化并添加线图形对象。

    .. method:: add_point(p, lable, **options)

        :param tuple p: 点坐标
        :param str label: 图形标签
        :param dict options: 参数

        实例化并添加点图形对象。

    .. method:: add_rectangle(p1, p2, label, **options)

        :param tuple p1: 点坐标
        :param tuple p2: 点坐标
        :param str label: 图形标签
        :param dict options: 参数

        实例化并添加矩形图形对象。

    .. method:: add_polygon(pts, label, **options)

        :param tuple pts: 点坐标
        :param str label: 图形标签
        :param dict options: 参数

        实例化并添加多边形图形对象。

    .. method:: render(canvas)

        :param object canvas: 待绘制的目标图像文件

        绘制图形列表中的图形到canvas上：::

            for shape in self._shapes:
                shape.set_color(self.get_color(shape._label))
                shape.draw_on(canvas)
            return canvas

    .. method:: draw(filename)

        :param str filename: 图片对象名称

        将图形列表中的图形绘制到原始图像中。

    .. method:: masking(filename)

        :param str filename: 图片对象名称

        将图形列表中的图形绘制到与原始图像等尺寸的所有值为 (0, 0, 0) 的图像上。


    .. method:: blend(filename, alpha=0.7, gamma=0.0)

        :param str filename: 图片对象名称
        :param int alpha: 第一个数组元素的权重值
        :param int gamma: 标量，在按位与计算中将标量加到每个和中，调整整体颜色

        叠加原始图片和mask图，按照如下公式生成：::

            dst = alpha * src1 + (1 - alpha) * src2 + gamma
