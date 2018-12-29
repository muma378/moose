.. _contributing:

======================
参与Moose的开发
======================

GitLab Workfow
========================

我们遵循基于GitLab的工作流，所以在参与到Moose的开发之前，最好先了解下 `GitLab Workflow: An Overview`_ 以尽快熟悉基本流程。简而言之，GitLab Workflow将软件开发分解成10个步骤，我们在此之上略有调整以适合Moose的开发工作模式，分别是：

1. IDEA。
2. ISSUE：讨论一个idea的最好办法就是为它创建一个issue，你的团队和同事会帮你一起在 **Issue Tracker** 中打磨和完善它；
3. PLAN：一旦讨论达成一致，就是时间开始编码了。但是！我们需要根据优先级以及前置条件来调整我们的工作顺序，在 **Issue Board** 中来制定开发计划；
4. CODE：创建该issue的feature分支和Merge Request，拉取到本地并开始编码；
5. COMMIT：在该feature分支中提交你的代码；
6. TEST：编写脚本或单元测试在 **GitLab CI** 中测试你的代码，确保所有单元测试能通过；
7. REVIEW：当代码可以工作，单元测试和编译都能通过时，就可以开始进入代码审查阶段了。代码审查主要是为了保证编码风格、模块设计等非功能性问题和整体是否一致，没有问题则合并；
8. FEEDBACK：检查各阶段在整个流程中的时间开销，研究是否有提升的地方。

*GitLab Workflow: An Overview* 详细解释了GitLab如何支持以上工作流，我们不再赘述，只挑非通用的地方进行说明。

参与讨论
====================

Moose所有的讨论都在 `Issue Tracker`_ 中进行，使用该工具创建并跟踪你的idea，bug fix或是相关文档的进展。

* 标签为 ``Bug`` 的issue意味这是一个需要修复的问题，描述清楚bug产生的步骤、期望行为以及实际结果，有助于尽快定位问题原因（选择template -> Bug 会提示需要描述的内容）。我们将优先级由上至下分为 ``Top Priority`` ， ``P1`` ， ``P2`` 和无，按照重要性和紧急程度予以标识；

.. note::

	书写良好的bug报告可以帮助开发者尽快定位问题，减少重现bug和解决的时间。在报告bug时请遵照以下原则：

	* 检查 **Open Issues** 中是否已有你发现的bug，如果已经有了，请查看报告信息和comments，如果你有新的发现，可以留下comment，或者考虑直接提交解决该bug的 **Merge Request**；
	* 在 **Issues** 中添加一个 **完整的，可再现的，特定bug的报告** 。这个bug的测试用例越小越好，请注意附上相关文件以保证其他开发者能重现。可以参考StackOverflow上关于 `如何创建一个最小的-完整的-可验证的例子`_  的指导来编写你的issue;
	* 最好的方式是提供一个可以重现这个bug的单元测试（并失败）的 **Merge Request** ；

* 标签为 ``Proposal`` 的issue意味这是一个有待实现的想法，是一个尚未开始的功能。描述这个想法希望达到的目的、旨在解决的问题，给出使用的场景和示例，如果可以的话还可以提供实现它的关键代码（template -> Proposal）；
* 标签为 ``Enhancement`` 的issue意味这是一个对旧有功能进行增强或修改的需求，通常是因为旧有功能不再适应新的业务场景，频繁的修改、重复的代码、工作量的增加都意味着代码需要重构，又或者只是需要添加单元测试。所有对旧有模块的修改和补充都应该打上`Enhancement`标签并且标上优先级 (template -> Enhancement)；
* 标签为 ``Document`` 的issue意味着这是一个说明性的文档的修改和添加，描述这篇文档要说明的对象、编写的目的和关键点、最好能够列出大纲，这能帮助其他人在编写文档的时候按照你想的方向前进（template -> Document）；


计划安排
==================

* 如果一个issue足够简单或者已经经过充分的讨论，提出者了解所有细节或是希望用代码进行说明：那么将该Issue的Assignee指给自己，并进入代码提交流程；
* 如果尚无issue的解决思路，只是发现某个bug或在功能上提出新的需求，那么：

	* 指定Assignee给Maintainer，并cc给 dataproc 组（通过指令 ``/cc @dataproc`` ）；
	* Maintainer负责回复和组织对该issue的讨论，安排开发计划和时间周期，将Assignee指给相应的负责人，并将标签置为 ``Todo`` ；
	* 对于不需要安排开发计划的issue，（可能是Issue本身描述不清、无法实现、被其他计划包含或不在功能设计之内等），说明理由并关掉。


代码提交
===================

开发人员收到新的开发任务时（有issue的Assignee是自己），就进入到编码阶段，此时：

* 修改Issue标签从 ``Todo`` 为 ``Doing`` ；
* 参照分支命名风格，在本地创建分支，并在任一commit中提及该 **issue number** （#xxx 的形式）；
* 完成编码后创建Merge Request，并将MR的Assignee指给Maintainer；
* 注意在提交MR之前，除了功能代码外，也需提供相应的单元测试证明代码work，并确保所有的单元测试能跑通；

Coding style
-----------------

* 除非特殊声明的情况，Moose的编码风格遵照 `PEP 8`_ ；
* Moose Cookbook提供了一些Moose使用上的建议和惯例说明，除了用户，开发者也应该了解它，确保你的想法（反映在风格上）和设计者是一致的；

分支命名风格
----------------

* 分支创建分为功能增加和bug修改两种，两者都基于master分支创建；
* 分支名应该足够简短且具有代表性，包含1~4个单词，使用中横线分割，表示本次修改主要做什么（可以省略动词）。例如：empty-nil-blank、rm-default-type-submit、rebuild-model-properties；
* 如果该分支的创建是为了增加新功能，加上 feature/* 前缀；
* 如果该分支的创建是为了修复临时的紧急的bug，加上hotfix/* 前缀，并将修改结果应用到上个patch中（通过 `cherry-pick`_ ）；

提交操作
------------------

详细操作流程如下：

1. 更新你本地的代码(git pull);
2. 创建你的 feature或bugfix 分支 (git checkout -b feature/my-new-feature)；
3. 提交修改 (git commit -am 'Add some feature; fixed \#23’)；
4. 推送到你的远端分支上 (git push origin feature/my-new-feature)
5. 创建 **Merge Request**，并指定Assignee为Maintainer；

测试
------------------

运行单元测试，linux 和 macOS下： ::

    $ ./runtest.sh tests/tests_dirs/


windows下： ::

    $ runtest.bat tests/tests_dirs/


或者使用tox： ::

    $ tox -e new


See also
=================

* `Cycle Analytics`_
* `Gitflow Workflow`_
* `Introduction to GitLab Flow`_
* `The 11 Rules of GitLab Flow`_


.. _GitLab Workflow\: An Overview: https://about.gitlab.com/2016/10/25/gitlab-workflow-an-overview/
.. _Cycle Analytics: https://docs.gitlab.com/ee/user/project/cycle_analytics.html
.. _Gitflow Workflow: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
.. _Introduction to GitLab Flow: https://docs.gitlab.com/ee/workflow/gitlab_flow.html
.. _The 11 Rules of GitLab Flow: https://about.gitlab.com/2016/07/27/the-11-rules-of-gitlab-flow/
.. _Issue Tracker: http://git.datatang.com/xiaoyang/Moose/issues
.. _如何创建一个最小的-完整的-可验证的例子: https://stackoverflow.com/help/mcve
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _cherry-pick: https://backlog.com/git-tutorial/cn/stepup/stepup7_4.html
