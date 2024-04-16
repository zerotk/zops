from __future__ import unicode_literals
'''
Module for string manipulation functions
'''
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
    if ignore_first_linebreak and '\n' in text:
        first, others = text.split('\n', 1)
        if first.strip('\n\r\t ') == '':
            text = others
    if ignore_last_linebreak and '\n' in text:
        others, last = text.rsplit('\n', 1)
        if last.strip('\n\r\t ') == '':
            text = others

    import re
    _leading_whitespace_re = re.compile('(^[ ]*)(?:[^ \n])', re.MULTILINE)

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
        text = re.sub(r'(?m)^' + margin, '', text)
    return text


def indent(text, indent_=1, indentation='    '):
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
        append_eol = lines.endswith('\n')
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
        result = '\n'.join(result)
        if append_eol:
            result += '\n'
    else:
        result = ''
    return result


def safe_split(s, sep, maxsplit=None, default='', reversed=False):
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
        split = lambda s,*args: s.rsplit(*args)
    else:
        split = lambda s,*args: s.split(*args)

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
    items = ', '.join((format_expr % (item,) for item in iterable))
    return '[%s]' % (items,)


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
