import sys
import logging
sys.path.insert(0,'/var/www/html')
sys.path.insert(0,'/var/www/html/crunkybot')
logging.basicConfig(stream=sys.stderr)

from crunkybot.app import app as application