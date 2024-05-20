import distutils
from collections.abc import MutableMapping
from collections import OrderedDict


class TemplateEngine(object):
    """
    Provide an easy and centralized way to change how we expand templates.
    """

    __singleton = None

    @classmethod
    def singleton(cls):
        if cls.__singleton is None:
            cls.__singleton = cls()
        return cls.__singleton

    @classmethod
    def run(
        cls,
        text,
        variables,
        alt_expansion=False,
        recursive_expansion=False,
        trim_blocks=False
    ):
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
            trim_blocks=trim_blocks,
            lstrip_blocks=trim_blocks,
            keep_trailing_newline=True,
            undefined=StrictUndefined,
            **kwargs,
        )

        def expandit(text_):
            before = None
            result = str(text_)
            while before != result:
                before = result
                result = env.from_string(result, template_class=Template).render(
                    **variables
                )
                if not recursive_expansion:
                    break
            return result

        env.filters["expandit"] = expandit

        def is_empty(text_):
            return not bool(expandit(text_).strip())

        env.tests["empty"] = is_empty

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
                Recursively merges hash b into a so that keys from b take precedence over keys
                from a.

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
