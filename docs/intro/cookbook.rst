.. _intro-cookbook:

===================
Moose Cookbook
===================


安装
---------------

- 使用 `虚拟环境`_；
- Moose目前并不稳定，功能和bug修复的更新非常频繁，安装开发者版本并且依靠 ``git pull`` 获取最新更新是一个更好的选择，详细查看 `安装开发者版本`_；
- 为了避免由于依赖库的兼容性问题导致安装失败，我们尽可能减少了安装Moose时的依赖，移除了部分不常用但在某些模块会使用到的第三方库，因此如果在使用过程中抛出导入异常，手动安装这些模块即可，包括：
	- MySQL-python>=1.2.5
	- pysmb>=1.1.17
	- Pillow>=3.4.1


创建项目和App
---------------

- Moose中，project和app名 **使用单个单词** ，不要有中横线或下划线，长度控制在5~12个间，没必要是项目的完整译名，取一个唯一的关键词即可（不关键也没有关系;-)）；
- 项目（project）和app的界限并没有那么严格和清晰，同一个项目完全既可以创建project也可以使用app。如果有的话，那么把一些 **相似的项目** ，或者一个 **大项目下不同的执行方式** （比如采集分为线上、线下、众包）作为不同的app放在一个project下，会是一个好的主意；
- 我们默认为每个app创建了一些文件，这在 `快速上手教程 — 创建一个新的application`_ 中已有说明。但是有些逻辑放在这些模块中可能并不合适，如下的文件命名规则为你提供了一些参考： ::

    appname/
        configs.py	# 适合存放与app相关的环境变量，例如路径、时长等
        files.py		# 适合存放文件对象抽象及处理方面的逻辑
        check.py		# 适合存放标注结果检查的逻辑
        metadata.py 	# 适合存放metadata解析及生成相关的逻辑
        info/			# 存放与该app运行或业务相关的文本文件（excel, csv, pdf）
        scripts/		# 简单的可执行的脚本

- 如果一个project下多个model或action相似，可以将其抽象、提取，放至里层的project目录下。同样的，如果创建的app需要一个共同的定制的模板，也可以在里层的project下创建app模板： ::

    projectname/
        projectname/
            __init__.py
            settings.py
            template.cfg
            regular/		# 定制化的app创建模板
                __init__.py
                actions.py-tpl
                apps.py-tpl
                models.py-tpl
                tests.py.tpl
            models/		# 提取通用model模块
                cityscape.py     # 街景标注通用模板
                ocr.py 			# OCR通用模板
            actions/		# 提取通用action模块
                ...

  并可以通过创建时指定路径以按照定制的模板创建app： ::

    $ python manage.py startapp appname --template projectname/regular/

  具体细节可以参考 `datatang/regular`_ 。


App实战
---------------

- 对于一个简单的任务，我们提供了 ``SimpleAction`` ，继承并在 *execute* 方法中提供实现，可以最快地开始；对于一个标准化的任务，如果没有已经提供的实现，需要继承 ``CommonAction`` 并实现所有接口（否则会抛出 **NotImplementedError** ），这有点麻烦，但对于代码的标准化有很大好处；
- ``CommonAction`` 中方法 *parse* 和 *set_environ* ， *schedule* 和 *set_context* 看起来功能有些重合，然而实际上，*parse* 和 *schedule* 旨在提供主要的流程的实现，通常在一类动作（例如上传）的基类中提供实现， *set_environ* 和 *set_context* 则被用于其子类中，需要对参数进行局部添加和修改的情况里 [1]_ ；
- 通常情况下，我们对要完成的工作提供了标准化的实现，继承对应的基类并在其预留的接口里改动以适配当前任务是最好的选择。例如:


**上传**

- 我们为上传提供了 ``SimpleUpload``，继承后指定要上传的文件的名称的模式即可，例如： ::

    default_pattern = "*.jpg"

  即可对根路径下所有满足 ``*.jpg`` 的文件进行上传处理；
- 上传任务中，变化最多的就是索引文件的格式，我们提供了接口 *index(blob_paris, context)* 作为修改索引格式的入口（当然如果需要额外信息的话，需要在之前流程中修改context里的内容）；
- 当同一个文件被多次用于不同期数的标注中，应该考虑上传一次文件，后续的索引使用完整的文件url代替。 ``ReferredUpload`` 提供了默认的实现；
-  ``SimpleUpload`` 中的参数 **dirs** 可帮助你一次完成；当需要将一个文件夹下的数据平均上传到多期任务中时， ``AverageUpload`` 提供了默认的实现；当进行视频追踪类标注，即一系列的图片（指按照一定规则从视频里抽帧的图片）需要按照每300张一条数据的方式上传时， ``VideosUpload`` 提供了相应的实现；

**导出**

- 导出总是涉及到提取数据，使用参数 ``use_cache`` 和 ``cache_lifetime`` 控制是否缓存提取到的结果以及缓存多长时间；
- 打开开关 ``download_source`` （设置为Ture），开始下载原始文件。这会使得程序变成多线程，如果这使得调试不方便，将 ``settings.DEBUG`` 设置为True，打开调试模式，下载将会变成单线程；
- ``TaskExport`` 和 ``SimpleExport`` 没有太大区别，除了 ``TaskExport`` 会根据task id自动获取到标题和批次信息，不再需要手动提供；
- 对于所有继承Export系列类的子类，*handle_model(data_model)* 是控制导出流程的入口。如果需要对数据处理的逻辑进行定制，从这里开始；
- 对于图像类导出任务，我们提供了 ``ImageExport`` ，它基本能解决80%的此类任务；


Tips
---------------

- 不要用 ``capitalize()``，除了首字母变大写，也会让其他字母变小写;
- 不要使用 ``import sys;reload(sys);sys.setdefaultencoding('utf-8')`` 以及任何你不了解但好像能work的代码片段，StackOverflow_ 有一个关于为什么禁止使用的讨论；
- Moose为很多常用的代码片段提供了shortcuts，使用这些函数，减少不必要的冗余，使所有代码看起来更加统一和标准：
	- 使用 **moose.shortcuts** 模块的 *ivist* 代替os.walk对文件夹进行遍历;
	- 使用 **moose.utils._os** 模块的 *npath* (native path)和 *upath* (unicode path) 替代对路径的encode和decode，因为不同平台上文件系统编码会有所区别；
	- 使用 **moose.utils._os** 模块的 *ppath* (posix path)和 *wpath* (windows path)替代对路径分隔符的replace（例如 ``path.replace(‘\\’, '/')`` ）；
	- 使用 **moose.utils._os** 模块的在路径前加上 *normpath* ，将路径分隔符（“\”，“\_\_”）标准化；
	- 使用 **moose.utils._os** 模块的 *makedirs* 和 *makeparents* 替代os.makedirs和os.makedirs(dirname(filepath)) ，在创建文件夹前会先判断文件夹是否已经存在；
	- 使用 **moose.utils._os** 模块的 *safe_join* 代替os.path.join，在合并路径之前会先检查拼接的路径是否在同一根路径下；
	- 使用 **moose.utils.encoding** 模块的 *smart_str* 和 *smart_unicode* 代替encode和decode，对于Python 2 和Python 3具有更好的兼容性；
	- 使用 **moose.utils.encoding** 模块的 *iri_to_uri* 和 *uri_to_iri* 进行uri和iri之间的转换，使用 *escape_uri_path* ；
	- 使用 **moose.utils.serialize** 模块的 *load_xlsx* 和 *dump_xlsx* 代替自己对excel文件进行load和dump操作；
	- 使用 **moose.utils.serialize** 模块的 *load_csv* 和 *dump_csv* 代替自己对csv文件进行load和dump操作；
	- 当除了将只有 *self* 参数的方法变成属性，还需要保存值避免重复计算时，使用 **moose.utils.functional** 模块的 *cached_property* 代替装饰器property；
	- 使用 **moose.utils.listutils** 模块的 *stripl* 对列表中的每个字符串进行strip处理； *slice* 和 *islice* 对一个整数进行平均切片操作；使用 *islicel* 对列表进行平均切片；
	- 使用 **moose.utils.module_loading** 模块的 *import_string* 代替import_module来动态导入类或函数；
	- 使用 **moose.utils.lru_cache** 模块的 *lru_cache* 装饰器缓存带参数的函数结果；
	- 使用 **moose.utils.xmlutils** 模块的 *dict2xml* 和 *xml2dict* 完成无属性的的xml和json格式的转换 [2]_ ；



.. _虚拟环境: https://virtualenv.pypa.io/
.. _安装开发者版本: https://moose-datatang.readthedocs.io/zh_CN/latest/intro/install.html#id3
.. _快速上手教程 — 创建一个新的application: https://moose-datatang.readthedocs.io/zh_CN/latest/intro/quickstart.html#application
.. _datatang/regular: http://git.datatang.com/xiaoyang/datatang/tree/master/datatang/regular
.. _StackOverflow: https://stackoverflow.com/questions/3828723/why-should-we-not-use-sys-setdefaultencodingutf-8-in-a-py-script

.. [1] ``SimpleAction`` 和 ``CommonAction`` 还没有按照如上的描述实现，主要是对旧代码的兼容问题导致这一修改比较棘手；
.. [2] 还未实现
