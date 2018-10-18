.. _topics-drawer:

=================
图形绘制（Drawer）
=================

数据处理中常见的一类工作就是对标注结果的可视化处理，通过将标注的点、线、矩形、多边形等图形绘制到原始
图像上，使得对标注效果可以做快速判断。另一方面，相比于坐标点集合的JSON文件，有些人更偏爱使用
mask图进行图像识别方面的训练，换句话说，这要求将标注结果绘制到一张与原始图像同样大小的黑色的
画布上。

然而在实际情况中，同一张图片往往包含多种图形的标注，例如街景标注中，可能既包含车道线（线），人、车（
多边形）的标注，也需要框出所有的交通灯和交通标志（矩形框）。而且，在绘制的时候，根据标注的实际情况，
绘制方法可能是轮廓也可能填充。这种情况下，将所有的绘制方法抽象成函数，通过参数来区分会导致过多的
细节需要在绘制的时候处理，更不用说对于数据格式的校验处理了。如何快速地完成此类需求，
就是`toolbox.drawer`的设计目的。

我们将`Shape(图形)`这一对象抽象出来，提供了验证和绘制的接口，另一方面，我们也根据经验提供了默
认的实现，大部分情况下，只需要按照统一的参数进行初始化和调用绘制接口即可。而调用绘制接口并在图上
进行绘制又由`Painter(绘制器)`去完成。这就将前面所提的所有需求变成了将标注结果实例化成图形。


.. module:: moose.toolbox.image.drawer
   :synopsis: Self-adaptive shapes drawing functions.

.. _topics-shapes-ref:

Shapes（图形）
=========================

.. class:: BaseShape(object)

    BaseShape是所有Shape的基类，它定义了Shape子类应该包含的属性并且提供了默认实现。

    这个类用来展示一个图形对象，它定义了`coordinates`坐标, `label`标签,'color'颜色,'thickness'线宽,'filled'填充等属性，；最后，我们通过实现规定的接口，保证不同的数据格式提供了一套统一的接口。


	.. attribute:: type

        定义该类绘制图形的形状。

	.. attribute:: default_color

        定义图像的默认颜色。

	.. attribute:: default_thickness

        定义绘制图像的默认线宽。

	.. attribute:: drawn_filled

        定义默认的_filled默认为None，即默认绘制轮廓的形状

	.. attribute:: _coordinates

        坐标,定义了如何组织点来表示形状，通过不同的坐标结构来表示不同的图形形状。

    .. attribute:: _label

        定义形状对象的标签，例如。汽车、自行车、卡车等。

    .. attribute:: _color

		定义形状对象的颜色，一般用来定义彩色图片和黑白图片

    .. attribute:: _filled

		_filled默认是None,它定义了在被标注对象文件上绘制轮廓的形状或者使用图像上的颜色填充形状

    .. attribute:: _thickness

        定义了形状对象的厚度

	.. attribute:: _options

        _option是一个字典，可以通过修改_option属性对形状对象进行调整，包含_color，_filled，_thickness等键值对。

    .. method:: _is_valid_coordinates(coordinates)

		:param list coordinates: 坐标列表。

		判断给定的坐标进行校验，默认返回True。该方法可根据子类需求自行定制。

    .. method:: _is_list_of_pairs(points)

		``@classmethod``

		:param tuple coordinates: 坐标点。

		返回bool值，该方法通过调用is_valid_format()和is_valid_value()来对输入点进行校验。

        该方法带有装饰器@classmethod ，可以被类调用。

    .. method:: is_valid_format(point)

        ``@classmethod``

		:param tuple coordinates: 坐标点。

        返回bool值，该方法用来判断输入点的类型是否为列表或者元祖且长度是否为2,若满足则返回True,否则为False。

    .. method:: is_valid_value(point)

       ``@classmethod``

	   :param tuple coordinates: 坐标点。

        返回bool值，该方法用来判断输入点中元素是否是整数(可以转换成整数的字符串)。

	.. method:: normalize(coordinates)

		:param list coordinates: 坐标列表。

        该方法是将输入的坐标进行格式化(将其元素中的浮点数转换为int，并将列表转换为tuple)。返回一个内部元素为元祖的列表

    .. method:: _equal_points(point1, point2)

        ``@classmethod``

		:param tuple coordinates: 坐标点。

        返回bool值，该方法用来输入的两个点是否完全相等(x,y是否分别对应相等)。

    .. method:: set_color(color)

		:param str coordinates: 颜色。

		该方法用来设置颜色，如果输入的color为None,则使用默认的颜色，否则使用输入的颜色。

    .. method:: color()

		``@property``

		因为OpenCV中(R, G, B)是反向的，如果_color是list或者tuple则对其实现逆序。同时若画布为灰度图像时颜色为整数。

    .. method:: draw_on(im)

		:param object im: 被标注对象文件。

		该方法用来定义图形在图像上绘制时的默认行为，如果self._filled存在则使用图像上的颜色填充形状，否则绘制轮廓的形状。

    .. method:: _fill(im)

		``abstract``

		:param object im: 被标注对象文件。

        该方法用来在被标注对象文件上使用图像上的颜色填充形状，为预留接口，子类必须继承并且实现该方法。

    .. method:: _outline(im)

		``abstract``

		:param object im: 被标注对象文件。

		该方法用来在被标注对象文件上绘制轮廓的形状，为预留接口，子类必须继承并且实现该方法。


.. class:: Point(BaseShape)

	Point是所有BaseShape的子类，它定义了基于BaseShape类的点在该类的具体实现

	.. attribute:: type="Point"

        定义该类绘制图形的形状为点。

	.. attribute:: radius

        定义绘制图形点的半径

	.. method:: _is_valid_coordinates(coordinates)

		:param tuple coordinates: 坐标

		该方法用来对给定的坐标进行校验，若为真则返回True 否则返回False。

	.. method:: normalize(coord)

		:param list coord: 坐标

		该方法是将输入的坐标进行格式化(将其元素中的浮点数转换为int)。返回一个内部元素为int的元祖。

	.. method:: draw_on(im)

		:param object im: 被标注对象文件

		该方法利用线宽厚度为负值在被标注文件上绘制画圆形成点形状


.. class:: LineString(BaseShape)

	LineString是所有BaseShape的子类，它定义了基于BaseShape类的线在该类的具体实现

	.. attribute:: type="LineString"

        定义该类绘制图形的形状为线串。

	.. method:: _is_valid_coordinates(coordinates)

		:param list coordinates: 坐标。

		返回bool值，该方法通过调用is_valid_format()和is_valid_value()来对输入点进行校验且需满足长度大于等于2。

	.. method:: draw_on(im)

		:param object im: 被标注对象文件

		该方法通过循环利用zip()形成的列表，依次连接当前点和下一点绘制线段。


.. class:: Polygon(BaseShape)

	Polygon是所有BaseShape的子类，它定义了基于BaseShape类的多边形在该类的具体实现

	.. attribute:: type="Polygon"

        定义该类绘制图形的形状为多边形。

	.. attribute:: is_closed

        定义该类绘制图形的形状必须是封闭的。

	.. attribute:: drawn_filled=True

        定义使用图像上的颜色填充形状


	.. method:: _is_valid_coordinates(coordinates)

		:param list coordinates: 坐标。

		返回bool值，该方法通过调用is_valid_format()和is_valid_value()来对输入点进行校验且需满足长度大于2且坐标的第一个点和最后一个点必须完全相等。

	.. method:: to_nparray()

		返回将坐标转化成一个占4个字节的数组。

	.. method:: _fill(im)

		该方法实现在被标注对象文件上使用图像上的颜色填充绘制多边形。

	.. method:: _outline(im)

		该方法实现在被标注对象文件上绘制多边形的轮廓形状。



.. class:: Rectangle(BaseShape)

	Rectangle是所有BaseShape的子类，它定义了基于BaseShape类的矩形在该类的具体实现

	.. attribute:: type="Rectangle"

        定义该类绘制图形的形状为矩形。

	.. attribute:: drawn_filled=False

        定义绘制轮廓的形状

	.. method:: _is_valid_coordinates(coordinates)

		:param list coordinates: 坐标。

		返回bool值，该方法通过调用is_valid_format()和is_valid_value()来对输入点进行校验且需满足长度等于2。

	.. method:: from_region(region, label, **options)

		``@classmethod``

		:param list region: 坐标。
		:param str label:   标签。
		:param dict options: 参数。

		该方法通过判断输入的坐标类型及坐标长度等于4，若为真则返回该类的实例对象，否则抛错

	.. method:: from_points(points, label, **options)

		``@classmethod``

		:param tuple coordinates: 坐标。
		:param str label: 标签。
		:param dict options: 参数。

		该方法实现若输入的坐标长度等于5且第一个元素和最后一个元素重合，对其进行调整，返回该类的实例对象

	.. method:: to_points()

		返回根据第一个和第二个元素形成的完整坐标

	.. method:: _outline(im)

		该方法实现在被标注对象文件上绘制指定线宽的矩形轮廓形状

	.. method:: _fill(im)

		该方法实现在被标注对象文件上绘制线宽等于-1的矩形轮廓形状


.. _topics-painter-ref:

Painter（绘制器）
=========================

.. class:: GeneralPainter(object)

	GeneralPainter是所有Painter的基类，它定义了Painter子类应该包含的属性并且提供了默认实现。

    这个类用来展示一个图形对象，它定义了`coordinates`坐标, `label`标签,'color'颜色,'thickness'线宽,'filled'填充等属性，；最后，我们通过实现规定的接口，保证不同的数据格式提供了一套统一的接口。

	.. attribute:: shape_line_cls = LineString
		线串类

	.. attribute:: shape_point_cls = Point

        点类
	.. attribute:: shape_polygon_cls = Polygon

		多边形类

	.. attribute:: shape_rectangle_cls = Rectangle

		矩形类

	.. attribute:: persistent_pallet  = {}

		持久化托盘

	.. attribute:: image_path

		定义图片标注后存放的路径

	.. attribute:: im

		根据图片地址利用CV2读取的图片对象

	.. attribute:: _autofill

		定义是否自动添加随机颜色

	.. attribute:: _use_default

		用户没有提供pallet，全部统一使用一种颜色来填充；

	.. attribute:: _persistent

		定义托盘是否设置持久化

	.. attribute:: _pallet

		定义如果托盘没有设置持久化等于True，则重置托盘

	.. attribute:: _shapes

		定义图形对象列表

	.. method:: get_color(label)

		:param str label: 颜色标签

		该方法实现通过输入的颜色标签获取颜色，若托盘不存在则自动填充随机颜色

	.. method:: add_color(label, color)

		:param str label: 颜色标签
		:param tuple color: 颜色

		该方法实现为托盘添加颜色

	.. method:: update_pallet(pallet)

		:param dict pallet: 托盘

		该方法实现将原有的托盘更新成输入的托盘

	.. method:: add_shape(shape)

		:param object shape: 图形对象

		该方法实现向图形列表添加图形对象

	.. method:: from_shapes(shapes)

		:param generator shapes 图形对象生成器

		该方法实现在图形对象是生成器的情况下将其添加到图形对象列表中

	.. method:: clear()

		该方法用来清空图形对象列表

	.. method:: add_line(p1, p2, label, **options)

		:param tuple p1: 点坐标
		:param tuple p2: 点坐标
		:param str label: 图形标签
		:param dict options: 参数

		添加线图形对象

	.. method:: add_point(p, lable, **options)

		:param tuple p: 点坐标
		:param str label: 图形标签
		:param dict options: 参数

		添加点图形对象

	.. method:: add_rectangle(p1, p2, label, **options)

		:param tuple p1: 点坐标
		:param tuple p2: 点坐标
		:param str label: 图形标签
		:param dict options: 参数

		添加矩形图形对象

	.. method:: add_polygon(pts, label, **options)

		:param tuple pts: 点坐标
		:param str label: 图形标签
		:param dict options:参数

		添加多边形图形对象

	.. method:: render(canvas)

		:param object canvas: 画布即目标图像文件

		该方法实现将每个图形对象画在画布上，返回该画布

	.. method:: draw(filename)

		:param str filename: 图片对象名称

		该方法实现不在原始的对象文件上绘制，而是复制一份原始文件进行绘制，重新生成一个文件名为filename的图像文件

	.. method::masking(filename)

		:param str filename: 图片对象名称

		该方法实现不在原始的对象文件上绘制，通过在一个零形矩阵上进行绘制，生成一个文件名为filename的图像文件


	.. method::blend(filename, alpha=0.7, gamma=0.0)

		:param str filename: 图片对象名称
		:param int alpha: 第一个数组元素的权重值
		:param int gamma: 标量，在按位与计算中将标量加到每个和中，调整整体颜色

		该方法实现原始图片和mask图片的叠加，生成一个文件名为filename的图像文件
