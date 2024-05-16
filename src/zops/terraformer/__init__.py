VERSION = "0.0.1"
from .apply_log import TerraformApplyLog
from .authentication import TerraformAuthentication
from .exceptions import TerraformError
from .exceptions import TerraformRuntimeError
from .exceptions import TerraformVersionError
from .plan import TerraformChange
from .plan import TerraformPlan
from .workspace import TerraformWorkspace


try:
    from . import _version

    __version__ = _version.__version__
except:
    __version__ = "0.0.0-dev"
