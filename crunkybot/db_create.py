from application import db
from application.models import Parameters
from application.models import Users
from application.models import Commands
from application.models import Playlist
from application.models import Request

db.create_all()

print("DB created.")
