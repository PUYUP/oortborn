from .base import *
from .project import *

# check setting load from live server
# this time all live server mark as production grade
if os.environ.get('PRODUCTION', False):
    from .development import *
else:
    from .development import *
