try:
    from .local_config import *
except ImportError:
    pass

try:
    from .instance_config import *
except ImportError:
    pass
