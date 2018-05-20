# edit the URI below to add your RDS password and your AWS URL
# The other elements are the same as used in the tutorial
# format: (user):(password)@(db_identifier).amazonaws.com:3306/(db_name)
from urllib import quote_plus as urlquote

#SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://cockeyedgaming:Djdesertf0x@crunkybot.cfa3vir9mjyz.us-west-2.rds.amazonaws.com:3306/crunkydb'

# Uncomment the line below if you want to work with a local DB
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

SQLALCHEMY_POOL_RECYCLE = 3600

WTF_CSRF_ENABLED = True
SECRET_KEY = 'dsaf0897sfdg45sfdgfdsaqzdf98sdf0a'
