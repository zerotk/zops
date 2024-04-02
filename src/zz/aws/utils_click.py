import click


class StringListParamType(click.ParamType):
    """
    Implements a click option for a list of strings.
    """

    name = "list"

    def convert(self, value, param, ctx):
        result = super().convert(value, param, ctx)
        if isinstance(result, str):
            result = result.split(",")
        return result

    def __repr__(self):
        return "STRING_LIST"


STRING_LIST = StringListParamType()
