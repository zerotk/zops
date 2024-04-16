VERSION = "0.0.1"
from .apply_log import TerraformApplyLog
from .authentication import TerraformAuthentication
from .exceptions import TerraformError, TerraformRuntimeError, TerraformVersionError
from .plan import TerraformChange, TerraformPlan
from .workspace import TerraformWorkspace

try:
    from . import _version

    __version__ = _version.__version__
except:
    __version__ = "0.0.0-dev"
