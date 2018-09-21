.. _topics-actions:

=================
动作（Actions）
=================

``Action`` 是对客观世界里的一套动作的抽象，它将具体的动作按照流程化的方式分解，以使它更容易被理解和复用。

数据处理的世界也存在一系列可以被复用的行为，我们定义模块 ``actions`` ，并且对其中最常见的操作进行抽象，帮助使用者只需要实现最少的“动作”。

.. module:: moose.actions
   :synopsis: Base and commonly used actions.

.. _topics-actions-ref:

moose.actions.base
====================

.. class:: base.AbstractAction

    AbstractAction是所有actions的抽象类，它定义了接口 `run()` 作为action的子类被调用的入口。

    .. method:: run(**kwargs)

        所有Action类的入口。

        :param dict kwargs: action 执行所需要的参数列表。


.. class:: base.BaseAction(app_config, stdout=None, stderr=None, style=None)

    BaseAction定义了Action的初始化参数和标准流程，所有Action类都应继承该类，并按照它提供的流程去分解过程并对方法进行实现。

    :param app_config: App的对象表示，提供了该app的路径等信息。
    :type app_config: moose.apps.AppConfig
    :param stdout: 标准输出，子类通过调用 `self.stdout.write()` 输出到标准输出。
    :type stdout: moose.core.OutputWrapper
    :param stderr: 标准错误输出对象，子类通过调用 `self.stderr.write()` 输出到标准错误输出。
    :type stderr: moose.core.OutputWrapper
    :param style: 定义输出的格式和显示效果。
    :type style: moose.core.Style

    .. attribute:: stats_class

        类变量，定义用于统计的类，默认值为 ``"moose.actions.stats.StatsCollector"``

    .. attribute:: stats_dump

        类变量，是否输出统计结果，默认为 ``True``

    .. method:: run(**kwargs)

        定义了具体流程，如下： ::

            def run(self, **kwargs):
                environment = self.parse(kwargs)
                for context in self.schedule(environment):
                    stats_id = self.execute(context)
                    self.stats.close_action(self, stats_id)
                self.teardown(environment)
                return '\n'.join(self.output
