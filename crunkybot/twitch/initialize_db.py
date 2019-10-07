import mysql.connector as sql
import sys
import crunkycfg as cfg 
import os
import os.path
import json
from dbutils import *

# TODO: make this path in crunkycfg.py
db_location=db_location=DBLocation(cfg.AWS_DB_HOST, cfg.AWS_DB_PORT, cfg.AWS_DB_COMMANDDB_GETCRUNKFRIDAY, cfg.AWS_DB_USERNAME, cfg.AWS_DB_PASSWORD)

def initialize(command_file):
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
	if len(sys.argv) == 2:
		initialize(sys.argv[1])

