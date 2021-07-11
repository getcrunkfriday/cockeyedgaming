import sys
import json
import src.crunkybot.twitch.config as cfg
from crunkybot.twitch.dbutils import *


def initialize(command_file, db_location):
	'''
	Initialize command database from a JSON file.
	command_file : path to JSON file.
	'''
	command_db = CommandDB(db_location)
	with open(command_file) as f:
		data = json.load(f)
		for c in data["commands"]:
			sql_str="INSERT INTO commands(command,command_type,permission,num_args,arguments,action) VALUES(%s,%s,%s,%s,%s,%s)"
			command = Command((c['command'], c['command_type'], c['permission'], int(c['num_args']), c['arguments'], c['action']))
			command_db.add_command(command)


if __name__ == "__main__":
	config = cfg.ConfigLoader(sys.argv[1])
	if len(sys.argv) == 2:
		initialize(sys.argv[1])

