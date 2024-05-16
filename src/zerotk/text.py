from __future__ import unicode_literals


"""
Module for string manipulation functions
"""
import six


def dedent(text, ignore_first_linebreak=True, ignore_last_linebreak=True):
    """
    Heavily inspired by textwrap.dedent, with a few changes (as of python 2.7)
        - No longer transforming all-whitespace lines into ''
        - Options to ignore first and last linebreaks of `text`.

    The last option is particularly useful because of ESSS coding standards.
    For example, using the default textwrap.dedent to create a 3-line string would look like this:
        textwrap.dedent('''    line1
            line2
            line3'''
        )

    With these options, you can create a better looking code with:
        dedent(
            '''
            line1
            line2
            line3
            '''
        )

    :param unicode text:
        Text to be dedented (see examples above)

    :param bool ignore_first_linebreak:
        If True, blank characters (\r\n\t ) up to the first '\n' is ignored

    :param bool ignore_last_linebreak:
        If True, black characters (\r\n\t ) after the last '\n' is ignored


    Original docs:
        Remove any common leading whitespace from every line in `text`.

        This can be used to make triple-quoted strings line up with the left edge of the display,
        while still presenting them in the source code in indented form.

        Note that tabs and spaces are both treated as whitespace, but they are not equal: the lines
        "  hello" and "\thello" are  considered to have no common leading whitespace.  (This
        behaviour is new in Python 2.5; older versions of this module incorrectly expanded tabs
        before searching for common leading whitespace.)
    """
    if ignore_first_linebreak and "\n" in text:
        first, others = text.split("\n", 1)
        if first.strip("\n\r\t ") == "":
            text = others
    if ignore_last_linebreak and "\n" in text:
        others, last = text.rsplit("\n", 1)
        if last.strip("\n\r\t ") == "":
            text = others

    import re

    _leading_whitespace_re = re.compile("(^[ ]*)(?:[^ \n])", re.MULTILINE)

    # Look for the longest leading string of spaces and tabs common to
    # all non-empty lines.
    margin = None
    indents = _leading_whitespace_re.findall(text)

    for indent in indents:
        if margin is None:
            margin = indent

        # Current line more deeply indented than previous winner:
        # no change (previous winner is still on top).
        elif indent.startswith(margin):
            pass

        # Current line consistent with and no deeper than previous winner:
        # it's the new winner.
        elif margin.startswith(indent):
            margin = indent

    if margin:
        text = re.sub(r"(?m)^" + margin, "", text)
    return text


def indent(text, indent_=1, indentation="    "):
    """
    Indents multiple lines of text.

    :param list(unicode)|unicode text:
        The text to apply the indentation.

    :param int indent_:
        Number of indentations to add. Defaults to 1.

    :param unicode indentation:
        The text used as indentation. Defaults to 4 spaces.

    :return unicode:
        Returns the text with applied indentation.
    """
    indentation = indent_ * indentation

    lines = text
    if isinstance(lines, six.text_type):
        append_eol = lines.endswith("\n")
        lines = lines.splitlines()
    else:
        append_eol = True

    result = []
    for i in lines:
        if i.strip():
            result.append(indentation + i)
        else:
            result.append(i)
    if result:
        result = "\n".join(result)
        if append_eol:
            result += "\n"
    else:
        result = ""
    return result


def safe_split(s, sep, maxsplit=None, default="", reversed=False):
    """
    Perform a string split granting the size of the resulting list.

    :param unicode s: The input string.
    :param unicode sep: The separator.
    :param int maxsplit: The max number of splits. The len of the resulting len is granted to be maxsplit + 1
    :param default: The default value for filled values in the result.

    :return list(unicode):
        Returns a list with fixed size of maxsplit + 1.
    """
    # NOTE: Can't import "string" module for string.split/string.rsplit because of module name
    # clashing with this module.
    if reversed:
        split = lambda s, *args: s.rsplit(*args)
    else:
        split = lambda s, *args: s.split(*args)

    if maxsplit is None:
        result = split(s, sep)
    else:
        result = split(s, sep, maxsplit)
        result_len = maxsplit + 1
        diff_len = result_len - len(result)
        if diff_len > 0:
            defaults = [default] * diff_len
            if reversed:
                result = defaults + result
            else:
                result = result + defaults
    return result


def format_it(iterable, format_expr="'%s'"):
    """
    Formats an iterable into a string by applying format_expr to each item.

    The resulting string is equivalent to stringifying a list, but unicode
    items won't have the prefix 'u'.

    Ex:
    a = u'My Item'
    b = [a]
    FormatIterable(b) # outputs "['a']", rather than "[u'a']"

    :param object iterable:
    Any iterable object.
    :param unicode format_expr:
    The format expression to use on each item. Defaults to "'%s'" so that the
    string representation of each item is encapsulated in single quotes.
    """
    items = ", ".join((format_expr % (item,) for item in iterable))
    return "[%s]" % (items,)


def match_any(text, regexes):
    """
    Returns whether the given text matches any of the given regular expressions.

    :param unicode text: The text to check for match.
    :param list(unicode) regexes: List of regular expressions.
    :return boolean:
        Return True if the given text matches any of the given regular expressions.
    """
    import re

    for i_regex in regexes:
        if re.match(i_regex, text) != None:
            return True
    return False


class TemplateEngine(object):
    """
    Provide an easy and centralized way to change how we expand templates.
    """

    __singleton = None

    @classmethod
    def get(cls):
        if cls.__singleton is None:
            cls.__singleton = cls()
        return cls.__singleton

    def expand(self, text, variables, alt_expansion=False):
        from jinja2 import Environment
        from jinja2 import StrictUndefined
        from jinja2 import Template

        if alt_expansion:
            kwargs = dict(
                block_start_string="{{%",
                block_end_string="%}}",
                variable_start_string="{{{",
                variable_end_string="}}}",
            )
        else:
            kwargs = {}

        env = Environment(
            # trim_blocks=True,
            # lstrip_blocks=True,
            keep_trailing_newline=True,
            undefined=StrictUndefined,
            **kwargs
        )

        def is_empty(text_):
            return not bool(expandit(text_).strip())

        env.tests["empty"] = is_empty

        def expandit(text_):
            before = None
            result = str(text_)
            while before != result:
                before = result
                result = env.from_string(result, template_class=Template).render(
                    **variables
                )
                break
            return result

        env.filters["expandit"] = expandit

        def dashcase(text_):
            result = ""
            for i, i_char in enumerate(str(text_)):
                r = i_char.lower()
                if i > 0 and i_char.isupper():
                    result += "-"
                result += r
            return result

        env.filters["dashcase"] = dashcase

        def quoted(value):
            if isinstance(value, str):
                return '"%s"' % value
            else:
                return ['"%s"' % i for i in value]

        env.filters["quoted"] = quoted

        def dmustache(text_):
            return "{{" + str(text_) + "}}"

        env.filters["dmustache"] = dmustache

        def env_var(text_):
            return "${" + expandit(text_) + "}"

        env.filters["env_var"] = env_var

        def to_json(text_):
            if isinstance(text_, bool):
                return "true" if text_ else "false"
            if isinstance(text_, list):
                return "[" + ", ".join([to_json(i) for i in text_]) + "]"
            if isinstance(text_, (int, float)):
                return str(text_)
            return '"{}"'.format(text_)

        env.filters["to_json"] = to_json

        import stringcase

        env.filters["camelcase"] = stringcase.camelcase
        env.filters["spinalcase"] = stringcase.spinalcase
        env.filters["pascalcase"] = stringcase.pascalcase

        def is_enabled(o):
            result = o.get("enabled", None)
            if result is None:
                return True
            result = env.from_string(result, template_class=Template).render(
                **variables
            )
            result = bool(distutils.util.strtobool(result))
            return result

        env.filters["is_enabled"] = is_enabled

        def combine(*terms, **kwargs):
            """
            NOTE: Copied from ansible.
            """
            import itertools
            from functools import reduce

            def merge_hash(a, b):
                """
                Recursively merges hash b into a so that keys from b take precedence over keys from a

                NOTE: Copied from ansible.
                """

                # if a is empty or equal to b, return b
                if a == {} or a == b:
                    return b.copy()

                # if b is empty the below unfolds quickly
                result = a.copy()

                # next, iterate over b keys and values
                for k, v in b.items():
                    # if there's already such key in a
                    # and that key contains a MutableMapping
                    if (
                        k in result
                        and isinstance(result[k], MutableMapping)
                        and isinstance(v, MutableMapping)
                    ):
                        # merge those dicts recursively
                        result[k] = merge_hash(result[k], v)
                    else:
                        # otherwise, just copy the value from b to a
                        result[k] = v

                return result

            recursive = kwargs.get("recursive", False)
            if len(kwargs) > 1 or (len(kwargs) == 1 and "recursive" not in kwargs):
                raise RuntimeError("'recursive' is the only valid keyword argument")

            dicts = []
            for t in terms:
                if isinstance(t, MutableMapping):
                    dicts.append(t)
                elif isinstance(t, list):
                    dicts.append(combine(*t, **kwargs))
                else:
                    raise RuntimeError("|combine expects dictionaries, got " + repr(t))

            if recursive:
                return reduce(merge_hash, dicts)
            else:
                return dict(itertools.chain(*map(lambda x: x.items(), dicts)))

        env.filters["combine"] = combine

        def dedup(lst, key):
            """Remove duplicates from ta list of dictionaries."""
            result = OrderedDict()
            for i_dict in lst:
                k = i_dict[key]
                v = result.get(k, {})
                v.update(i_dict)
                result[k] = v
            result = list(result.values())
            return result

        env.filters["dedup"] = dedup

        def dfilteredkeys(dct, value):
            """Filter dictionary list by the value."""
            return [i_key for (i_key, i_value) in dct.items() if i_value == value]

        env.filters["dfilteredkeys"] = dfilteredkeys

        def dvalues(lst, key):
            """In a list of dictionaries, for each item returns item["key"]."""
            return [i.get(key) for i in lst]

        env.filters["dvalues"] = dvalues

        def d_items_str(dct, skip=[]):
            return ["{}{}".format(i, j) for i, j in dct.items() if i not in skip]

        env.filters["d_items_str"] = d_items_str

        def d_values_str(dct, skip=[]):
            return [str(j) for i, j in dct.items() if i not in skip]

        env.filters["d_values_str"] = d_values_str

        result = expandit(text)
        return result
