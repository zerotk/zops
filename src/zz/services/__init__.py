class services:

  def __init__(self, *services):
    from .filesystem import FileSystem
    from .console import Console
    from .formatter import Formatter

    AVAILABLE_SERVICES = dict(
      filesystem = FileSystem.singleton(),
      console = Console(),
      formatter = Formatter.singleton(),
    )
    self._services = { i: j for i, j in AVAILABLE_SERVICES.items() if i in services }

  def __call__(self, f, *args, **kwargs):
    from functools import update_wrapper

    def new_func(*args, **kwargs):
      # ctx = click.get_current_context()
      # ctx.__dict__.update(self._services)
      
      return f(ctx, *args, **kwargs)
    return update_wrapper(new_func, f)

  def __getattr__(self, name: str) -> object:
    return self._services[name]
