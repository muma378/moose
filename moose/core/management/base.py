# -*- coding: utf-8 -*-
"""
Base classes for writing management commands (named commands which can
be executed through ``moose-admin`` or ``manage.py``).
"""
from __future__ import unicode_literals
import os
import sys
from argparse import ArgumentParser

import moose
from moose.core.exceptions import ImproperlyConfigured
from moose.core.management.color import color_style, no_style
from moose.core.configs.registry import find_matched_conf
from moose.utils.encoding import force_str, force_text


class checks(object):
    """adaptor for moose.core.checks"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class CommandError(Exception):
    """
    Exception class indicating a problem while executing a management
    command.

    If this exception is raised during the execution of a management
    command, it will be caught and turned into a nicely-printed error
    message to the appropriate output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.
    """
    pass


class SystemCheckError(CommandError):
    """
    The system check framework detected unrecoverable errors.
    """
    pass


class CommandParser(ArgumentParser):
    """
    Customized ArgumentParser class to improve some error messages and prevent
    SystemExit in several occasions, as SystemExit is unacceptable when a
    command is called programmatically.
    """
    def __init__(self, cmd, **kwargs):
        self.cmd = cmd
        super(CommandParser, self).__init__(**kwargs)

    def parse_args(self, args=None, namespace=None):
        # Catch missing argument for a better error message
        if (hasattr(self.cmd, 'missing_args_message') and
                not (args or any(not arg.startswith('-') for arg in args))):
            self.error(self.cmd.missing_args_message)
        return super(CommandParser, self).parse_args(args, namespace)

    def error(self, message):
        if self.cmd._called_from_command_line:
            super(CommandParser, self).error(message)
        else:
            raise CommandError("Error: %s" % message)



def handle_default_options(options):
    """
    Include any default options that all commands should accept here
    so that ManagementUtility can handle them before searching for
    user commands.
    """
    if options.settings:
        os.environ['MOOSE_SETTINGS_MODULE'] = options.settings
    if options.pythonpath:
        sys.path.insert(0, options.pythonpath)


class OutputWrapper(object):
    """
    Wrapper around stdout/stderr
    """
    @property
    def style_func(self):
        return self._style_func

    @style_func.setter
    def style_func(self, style_func):
        if style_func and self.isatty():
            self._style_func = style_func
        else:
            self._style_func = lambda x: x

    def __init__(self, out, style_func=None, ending='\n'):
        self._out = out
        self.style_func = None
        self.ending = ending

    def __getattr__(self, name):
        return getattr(self._out, name)

    def isatty(self):
        return hasattr(self._out, 'isatty') and self._out.isatty()

    def write(self, msg, style_func=None, ending=None):
        ending = self.ending if ending is None else ending
        if ending and not msg.endswith(ending):
            msg += ending
        style_func = style_func or self.style_func
        self._out.write(force_str(style_func(msg)))


class BaseCommand(object):
    """
    the base class from which all management commands ultimately derive.

    Use this class if you want access to all of the mechanisms which
    parse the command-line arguments and work out what code to call in
    response; if you don't need to change any of that behavior,
    consider using one of the subclasses defined in this file.

    If you are interested in overriding/customizing various aspects of
    the command-parsing and -execution behavior, the normal flow works
    as follows:

    1. ``moose-admin`` or ``manage.py`` loads the command class
       and calls its ``run_from_argv()`` method.

    2. The ``run_from_argv()`` method calls ``create_parser()`` to get
       an ``ArgumentParser`` for the arguments, parses them, performs
       any environment changes requested by options like
       ``pythonpath``, and then calls the ``execute()`` method,
       passing the parsed arguments.

    3. The ``execute()`` method attempts to carry out the command by
       calling the ``handle()`` method with the parsed arguments; any
       output produced by ``handle()`` will be printed to standard
       output and, if the command is intended to produce a block of
       SQL statements, will be wrapped in ``BEGIN`` and ``COMMIT``.

    4. If ``handle()`` or ``execute()`` raised any exception (e.g.
       ``CommandError``), ``run_from_argv()`` will  instead print an error
       message to ``stderr``.

    Thus, the ``handle()`` method is typically the starting point for
    subclasses; many built-in commands and command types either place
    all of their logic in ``handle()``, or perform some additional
    parsing work in ``handle()`` and then delegate from it to more
    specialized methods as needed.

    Several attributes affect behavior at various steps along the way:

    ``help``
        A short description of the command, which will be printed in
        help messages.

    """

    help = ''
    _called_from_command_line = False
    requires_system_checks = False

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.stdout = OutputWrapper(stdout or sys.stdout)
        self.stderr = OutputWrapper(stderr or sys.stderr)
        if no_color:
            self.style = no_style()
        else:
            self.style = color_style()
            self.stderr.style_func = self.style.ERROR

    def get_version(self):
        return moose.get_version()

    def create_parser(self, prog_name, subcommand):
        parser = CommandParser(
            self, prog="%s %s" % (os.path.basename(prog_name), subcommand),
            description=self.help or None,
        )

        parser.add_argument('--version', action='version', version=self.get_version())
        parser.add_argument(
            '-v', '--verbosity', action='store', dest='verbosity', default=1,
            type=int, choices=[0, 1, 2, 3],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output',
        )
        parser.add_argument(
            '--settings',
            help=(
                'The Python path to a settings module, e.g. '
                '"myproject.settings.main". If this isn\'t provided, the '
                'MOOSE_SETTINGS_MODULE environment variable will be used.'
            ),
        )
        parser.add_argument(
            '--pythonpath',
            help='A directory to add to the Python path, e.g. "/home/mooseprojects/myproject".',
        )

        parser.add_argument('--traceback', action='store_true', help='Raise on CommandError exceptions')
        parser.add_argument(
            '--no-color', action='store_true', dest='no_color', default=False,
            help="Don't colorize the command output.",
        )
        self.add_arguments(parser)
        return parser

    def add_argument(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass

    def print_help(self, prog_name, subcommand):
        """
        Print the help message for this command, derived from
        ``self.usage()``.
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Moose settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        self.raw_command_line = ' '.join(argv)
        self.prog = argv[0]
        self.name = argv[1]

        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        handle_default_options(options)
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            if options.traceback or not isinstance(e, CommandError):
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(1)
        finally:
            try:
                # connections.close_all()
                pass
            except ImproperlyConfigured:
                # Ignore if connections aren't setup at this point (e.g. no
                # configured settings).
                pass

    def execute(self, *args, **options):
        """
        Try to execute this command, performing system checks if needed (as
        controlled by the ``requires_system_checks`` attribute, except if
        force-skipped).
        """
        if options['no_color']:
            self.style = no_style()
            self.stderr.style_func = None
        if options.get('stdout'):
            self.stdout = OutputWrapper(options['stdout'])
        if options.get('stderr'):
            self.stderr = OutputWrapper(options['stderr'], self.stderr.style_func)

        try:
            if self.requires_system_checks and not options.get('skip_checks'):
                self.check()
            output = self.handle(*args, **options)
            if output:
                # if self.output_transaction:
                #     connection = connections[options.get('database', DEFAULT_DB_ALIAS)]
                #     output = '%s\n%s\n%s' % (
                #         self.style.SQL_KEYWORD(connection.ops.start_transaction_sql()),
                #         output,
                #         self.style.SQL_KEYWORD(connection.ops.end_transaction_sql()),
                #     )

                style_output = self.style.SUCCESS(output)
                self.stdout.write(style_output)
        finally:
            pass

        return output

    def check(self, app_configs=None, tags=None, display_num_errors=False,
              include_deployment_checks=False, fail_level=checks.ERROR):
        """
        Uses the system check framework to validate entire Moose project.
        Raises CommandError for any serious message (error or critical errors).
        If there are only light messages (like warnings), they are printed to
        stderr and no exception is raised.
        """
        pass

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError('subclasses of BaseCommand must provide a handle() method')

    def comment(self):
        """
        The default comment on running the command.

        """
        return self.raw_command_line


class AppCommand(BaseCommand):
    """
    A management command which takes one or more installed application labels
    as arguments, and does something with each of them.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_app_config()``, which will be called once for each application.
    """
    missing_args_message = "Enter at least one application label."

    def add_arguments(self, parser):
        parser.add_argument('args', metavar='app_label', nargs='+', help='One or more application label.')

    def handle(self, *app_labels, **options):
        from moose.apps import apps
        try:
            app_configs = [apps.get_app_config(app_label) for app_label in app_labels]
        except (LookupError, ImportError) as e:
            raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)
        output = []
        for app_config in app_configs:
            app_output = self.handle_app_config(app_config, **options)
            if app_output:
                output.append(app_output)
        return '\n'.join(output)

    def handle_app_config(self, app_config, **options):
        """
        Perform the command's actions for app_config, an AppConfig instance
        corresponding to an application label given on the command line.
        """
        raise NotImplementedError(
            "Subclasses of AppCommand must provide"
            "a handle_app_config() method.")


class ConfigsCommand(BaseCommand):
    """
    A management command which takes one application label and one or more
    config description as arguments. The config will be handled by the
    application in sequence.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_config()``, which will be called once for each config.
    """
    multiple_configs_allowed = True
    # use_conf_desc_allowed = True
    config_desc_usage = (
        "`conf_desc` is a literal representation on a config file, "
        "4 ways are provided to find a config file for the application:\n"
        "1. full path to the config file;\n"
        "2. basename of the config file;\n"
        "3. by tag with the letter 't', eg. `-c t:tag_name`\n"
        "4. by attribute and value with letter 'a', eg. `-c a:section.option=val`"
        )

    def add_arguments(self, parser):
        parser.add_argument(
            'args', metavar='app_label', nargs=1,
            help='Specify an application label.'
            )

        # if self.use_conf_desc_allowed:
        #     help_text = self.config_desc_usage
        # else:
        #     help_text = "Full path to or the basename of the config file."

        if self.multiple_configs_allowed:
            parser.add_argument(
                '-c', '--config', metavar='config_descs', action='append',
                help=help,
                )
        else:
            # only one config description was allowed to specified
            parser.add_argument(
                '-c', '--config', metavar='config_desc', action='store',
                help=help,
            )


    def handle(self, app_label, **options):
        from moose.apps import apps
        try:
            app_config = apps.get_app_config(app_label)
        except (LookupError, ImportError) as e:
            raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)

        if self.multiple_configs_allowed:
            configs = options['config']
        else:
            configs = [options['config'], ]

        output = []
        for conf_desc in configs:
            config_loader = find_matched_conf(app_config, conf_desc)
            if not config_loader:
                raise CommandError("No matched config found for the description '%s', aborted." % conf_desc)
            app_output = self.handle_config_loader(app_config, config_loader, **options)
            if app_output:
                output.append(app_output)
        return '\n'.join(output)


    def handle_config_loader(self, app_config, config_loader, **options):
        """
        Perform the command's actions for app_config with a config_loader,
        an AppConfig instance corresponding to an application label given on the command line.
        """
        raise NotImplementedError(
            "Subclasses of AppCommand must provide a "
            "handle_config_loader() method.")


class LabelCommand(BaseCommand):
    """
    A management command which takes one or more arbitrary arguments
    (labels) on the command line, and does something with each of
    them.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_label()``, which will be called once for each label.

    If the arguments should be names of installed applications, use
    ``AppCommand`` instead.
    """
    label = 'label'
    missing_args_message = "Enter at least one %s." % label

    def add_arguments(self, parser):
        parser.add_argument('args', metavar=self.label, nargs='+')

    def handle(self, *labels, **options):
        output = []
        for label in labels:
            label_output = self.handle_label(label, **options)
            if label_output:
                output.append(label_output)
        return '\n'.join(output)

    def handle_label(self, label, **options):
        """
        Perform the command's actions for ``label``, which will be the
        string as given on the command line.
        """
        raise NotImplementedError('subclasses of LabelCommand must provide a handle_label() method')
