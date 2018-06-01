# edit the URI below to add your RDS password and your AWS URL
# The other elements are the same as used in the tutorial
# format: (user):(password)@(db_identifier).amazonaws.com:3306/(db_name)
from urllib import quote_plus as urlquote

#SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://cockeyedgaming:Djdesertf0x@crunkybot.cfa3vir9mjyz.us-west-2.rds.amazonaws.com:3306/crunkydb'
# DB parameters.
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
SQLALCHEMY_POOL_RECYCLE = 3600
WTF_CSRF_ENABLED = True
SECRET_KEY = 'c7a38fff-9bab-4b8e-b3ca-5cb55ec439a3'

#Twitch parameters.
TWITCH_CLIENTID="i202c5n9be1v8cppav0fic5gfqe7jm"
TWITCH_SECRET="blztot2h6y8l5j7bh0ljf6qziqxy81"

#Celery parameters
SOCKETIO_REDIS_URL = 'redis://localhost:6379/0'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CSRF_ENABLED = True