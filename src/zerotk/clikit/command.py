from __future__ import unicode_literals
from .console import BufferedConsole
from collections import OrderedDict
import re
import six



#===================================================================================================
# InvalidFixture
#===================================================================================================
class InvalidFixture(KeyError):
    '''
    Exception raised when an unknown argument is added to a command-function.
    '''
    pass


#===================================================================================================
# MissingArgument
#===================================================================================================
class MissingArgument(KeyError):
    '''
    Exception raised when an unknown argument is added to a command-function.
    '''
    pass



#===================================================================================================
# Command
#===================================================================================================
class Command:
    '''
    Holds the information for a command, directly associated with a function that implements it.
    '''

    class DEFAULT(object):
        '''
        Placeholder for positional arguments with default value.

        Usage:

            def Hello(self, console_, p1=DEFAULT('default'):
                console_.Print(p1)

            >hello
            default
            >hello other
            other
        '''


        def __init__(self, default):
            '''
            :param object default:
                The default value for the positional argument.
            '''
            self.default = default


        def CreateArg(self, name):
            '''
            Creates Arg instance for our positional with default argument.

            :param unicode name:
                The name of the argument.
            '''
            return Command.Arg(name, Command.Arg.ARG_TYPE_POSITIONAL, self.default)


    class Arg:
        '''
        Holds meta-information about the associated *function parameter*.
        '''
        NO_DEFAULT = object()

        ARG_TYPE_FIXTURE = "F"
        ARG_TYPE_OPTION = "O"
        ARG_TYPE_POSITIONAL = 'P'
        ARG_TYPE_TRAIL = "T"

        def __init__(self, name, arg_type, default=NO_DEFAULT):
            '''
            :param unicode name:
                The argument name.

            :param ARG_TYPE_XXX arg_type:
                The type of the argument in CliKit scope.
                See ARG_TYPE_XXX constants.

            :param object default:
                The default value for this argument.
            '''
            self.name = name
            self.arg_type = arg_type
            self.default = default
            self.description = '(no description)'
            self.short_description = '(no description)'

            # For the command line, all options with underscores are replaced by hyphens.
            # argparse handles this and replaces back to underscore when setting option values
            if arg_type == self.ARG_TYPE_OPTION:
                self.argparse_name = name.replace('_', '-')
            else:
                self.argparse_name = name


        def __str__(self):
            if self.arg_type == self.ARG_TYPE_TRAIL:
                return '*' + self.argparse_name
            elif any(map(lambda x: self.default is x, (Command.Arg.NO_DEFAULT, True, False))):
                return self.argparse_name
            elif self.default is None:
                return '%s=VALUE' % self.argparse_name
            else:
                return '%s=%s' % (self.argparse_name, self.default)


        def __repr__(self):
            '''
            Representation for debug purposes.
            '''
            return '<Arg %s>' % self.__str__()


        def ConfigureArgumentParser(self, parser):
            '''
            Configures the given parser with an argument matching the information in this class.

            :param parser: argparse.ArgumentParser
            '''
            if self.arg_type == self.ARG_TYPE_FIXTURE:
                return

            if self.arg_type == self.ARG_TYPE_TRAIL:
                parser.add_argument(self.argparse_name, nargs='*')
                return

            if self.arg_type == self.ARG_TYPE_OPTION:
                if isinstance(self.default, bool):
                    # Boolean arguments have a special treatment, since they create a 'store_true'
                    # parameters type that has no arguments. For example, instead of passing
                    # --param=True in the command line, using --param should have the same effect

                    # Boolean options with default=True make no sense to the command line, since
                    # either setting or not setting them would lead to the same effect.
                    assert self.default is not True, 'Can\'t handle boolean options with default=True'

                    parser.add_argument('--%s' % self.argparse_name, action='store_true', default=self.default)
                else:
                    # All other parameter types work as usual and must receive a value
                    parser.add_argument('--%s' % self.argparse_name, default=self.default)
                return

            if self.arg_type is self.ARG_TYPE_POSITIONAL:
                if self.default is self.NO_DEFAULT:
                    parser.add_argument(self.argparse_name)
                else:
                    parser.add_argument(self.argparse_name, nargs='?', default=self.default)
                return

            raise TypeError('Unknown arg_type==%r' % self.arg_type)


    def __init__(self, func, names=None):
        '''
        :param <function> func:
            A function to wrap as a command.

        :param None|unicode|list(unicode) names:
            A list of names for the command.
            By default uses the function name converted to "command style".
            If not None, uses only the names from this argument, ignoring the function name.
        '''
        import inspect

        self.func = func
        if names is None:
            self.names = [func.__name__]  # default to function name
        elif isinstance(names, str):
            self.names = [names]  # a single name
        else:
            self.names = names  # already a list

        signature = inspect.signature(self.func)

        self.args = OrderedDict()
        for i_name, i_param in signature.parameters.items():
            if i_name.endswith("_"):
                self.args[i_name] = self.Arg(i_name, self.Arg.ARG_TYPE_FIXTURE)
            elif not i_param.default:
                self.args[i_name] = self.Arg(i_name, self.Arg.ARG_TYPE_POSITIONAL)

#         # Meta-info from function inspection
#         args, trail, self.kwargs, defaults = self._ParseFunctionArguments(self.func)
#
#         # Holds a dict, mapping the arg name to an Arg instance. (See Arg class)
#         self.args = OrderedDict()
#
#         first_default = len(args) - len(defaults)
#         for i, i_arg in enumerate(args):
#             if i_arg.endswith('_'):
#                 self.args[i_arg] = self.Arg(i_arg, self.Arg.ARG_TYPE_FIXTURE)
#             elif i < first_default:
#                 self.args[i_arg] = self.Arg(i_arg, self.Arg.ARG_TYPE_POSITIONAL)
#             else:
#                 default = defaults[i - first_default]
#
#                 if isinstance(default, Command.DEFAULT):
#                     self.args[i_arg] = default.CreateArg(i_arg)
#
#                 elif default is True:
#                     # I couldn't find a reasonable way to handle bool args with default=True since
#                     # Passing --option or not would have the same result, therefore, these args
#                     # cannot be used in clikit commands.
#                     raise RuntimeError(
#                         "Clikit commands are not allowed to have " + \
#                         "boolean parameters that default to True."
#                     )
#                 else:
#                     self.args[i_arg] = self.Arg(i_arg, self.Arg.ARG_TYPE_OPTION, default)
#
#         # Adds trail (*args) to the list of arguments.
#         # - Note that these arguments have a asterisk prefix.
#         if trail is not None:
#             self.args[trail] = self.Arg(trail, self.Arg.ARG_TYPE_TRAIL)

        # Meta-info from
        description, long_description, arg_descriptions = self._ParseDocString(self.func.__doc__ or '')
        self.description = description or '(no description)'
        self.long_description = long_description or '(no description)'
        for i_arg, i_description in six.iteritems(arg_descriptions):
            try:
                self.args[i_arg].description = i_description
            except KeyError as e:
                raise RuntimeError('%s: argument not found for documentation entry.' % six.text_type(e))


    def _ParseFunctionArguments(self, func):
        '''
        Parses function arguments returning meta information about it.

        :return tuple:
            [0]: args: The list with the name of all the function arguments.
            [1]: trail?
            [2]: kwargs: if the function is using it, otherwise None.
            [3]: defaults: The defaults value for the argument (if given any)
        '''
        import inspect
        args, trail, kwargs, defaults = inspect.getargspec(func)
        defaults = defaults or []
        return args, trail, kwargs, defaults


    PARAM_RE = re.compile(':param (.*):(.*)$')

    def _ParseDocString(self, docstring):
        '''
        Parses the (function) docstring for the general and arguments descriptions.

        :param docstring: A well formed docstring of a function.
        :rtype: tuple(unicode, unicode, list(unicode))
        :returns:
            Returns the function description (doc's first line) and the description of each
            argument (sphinx doc style).
        '''

        # States:
        # 0: Starting to process
        # 1: Loaded short_description
        # 2: Loaded long_description
        state = 0
        short_description = ''
        long_description = []
        arg_descriptions = {}

        lines = docstring.split('\n')
        for i_line in lines:
            i_line = i_line.strip()

            if state == 0:
                if not i_line:
                    continue
                short_description = i_line
                state = 1

            m = self.PARAM_RE.match(i_line)
            if m:
                state = 2
                arg, doc = m.groups()
                arg_descriptions[arg.strip()] = doc.strip()
            elif state == 1:
                long_description.append(i_line)
                continue

        long_description = '\n'.join(long_description)
        long_description = long_description.rstrip('\n')
        return short_description, long_description, arg_descriptions


    def FormatHelp(self):
        '''
        Format help for this command.

        :return unicode:
        '''
        console = BufferedConsole()
        console.Print('Usage:')
        positionals = [i for i in self.args.values() if i.arg_type in (self.Arg.ARG_TYPE_POSITIONAL, self.Arg.ARG_TYPE_TRAIL)]
        optionals = [i for i in self.args.values() if i.arg_type == self.Arg.ARG_TYPE_OPTION]
        console.Print('%s %s %s' % (
            ','.join(self.names),
            ' '.join(['<%s>' % i for i in positionals]),
            ','.join(['[--%s]' % i for i in optionals]),
        ), indent_=1, newlines=2)
        console.Print('Parameters:')
        for i in positionals:
            console.Print('<teal>%s</>   %s' % (i.argparse_name, i.description), indent_=1)
        console.Print()
        console.Print('Options:')
        for i in optionals:
            if any(map(lambda x: i.default is x, (Command.Arg.NO_DEFAULT, None, True, False))):
                console.Print('--%s   %s' % (i.argparse_name, i.description), indent_=1)
            else:
                console.Print('--%s   %s [default: %s]' % (i.argparse_name, i.description, i.default), indent_=1)
        return console.GetOutput()


    def ConfigureArgumentParser(self, parser):
        '''
        Configures the given parser with all arguments of this command.

        :param parser: argparse.ArgumentParser
        '''
        for i_arg in six.itervalues(self.args):
            i_arg.ConfigureArgumentParser(parser)


    def Call(self, fixtures, argd):
        '''
        Executes the function filling the fixtures and options parameters.

        :param dict(unicode : tuple(callable, callable)) fixtures:
            Map of fixtures to pass to the function as requested.

        :param argd:
            Map of option values as passed by the user in the command line.

        :return:
            Returns the command function result.
        '''
        args = []
        finalizers = []
        for i_arg in six.itervalues(self.args):
            if i_arg.arg_type == i_arg.ARG_TYPE_FIXTURE:
                try:
                    fixture, finalizer = fixtures[i_arg.name]
                except KeyError as exception:
                    raise InvalidFixture(six.text_type(exception))
                args.append(fixture())
                finalizers.append(finalizer)
                continue

            if i_arg.arg_type == i_arg.ARG_TYPE_TRAIL:
                args += argd.get(i_arg.name, ())
                continue

            if i_arg.arg_type == i_arg.ARG_TYPE_POSITIONAL:
                arg = argd.get(i_arg.name, i_arg.default)
                if arg is self.Arg.NO_DEFAULT:
                    raise TypeError(i_arg.name)
                else:
                    args.append(arg)
                continue

            if i_arg.arg_type == i_arg.ARG_TYPE_OPTION:
                arg = argd.get(i_arg.name, i_arg.default)
                args.append(arg)
                continue

        result = self.func(*args)

        for i_finalizer in finalizers:
            i_finalizer()

        return result


    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
