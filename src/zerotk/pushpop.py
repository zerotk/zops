from __future__ import unicode_literals
import contextlib



#===================================================================================================
# PushPop
#===================================================================================================
@contextlib.contextmanager
def PushPopAttr(obj, name, value):
    '''
    A context manager to replace and restore a variable/attribute.

    :param object obj: The object to replace/restore.
    :param unicode name: The variable/attribute to replace/restore.
    :param object value: The value to replace.

    Example::

      with PushPop(sys, 'stdout', StringIO()) as output:
        print "Hello, world!"
        assert output.gettext() == "Hello, world!"
    '''
    old_value = getattr(obj, name)
    setattr(obj, name, value)
    yield value
    setattr(obj, name, old_value)


# Backward compatility.
PushPop = PushPopAttr



#===================================================================================================
# PushPopItem
#===================================================================================================
@contextlib.contextmanager
def PushPopItem(obj, key, value):
    '''
    A context manager to replace and restore a value using a getter and setter.

    :param object obj: The object to replace/restore.
    :param object key: The key to replace/restore in the object.
    :param object value: The value to replace.

    Example::

      with PushPop2(sys.modules, 'alpha', None):
        pytest.raises(ImportError):
          import alpha
    '''
    if key in obj:
        old_value = obj[key]
        obj[key] = value
        yield value
        obj[key] = old_value

    else:
        obj[key] = value
        yield value
        del obj[key]
