import sqlite3
import sys
import crunkycfg as cfg 
import os
import os.path
import json

# TODO: make this path in crunkycfg.py
db_path=cfg.DB_PATH

def initialize(command_file):
	'''
	Initialize command database from a JSON file.

	command_file : path to JSON file.
	'''
	con=sqlite3.connect(db_path)
	cur=con.cursor()
	cur.execute('''DROP TABLE IF EXISTS commands''')
	cur.execute('''DROP TABLE IF EXISTS shoutouts''')
	cur.execute('''CREATE TABLE commands (id INTEGER PRIMARY KEY, command TEXT, command_type TEXT, permission TEXT, num_args INTEGER, arguments TEXT, action TEXT)''')
	cur.execute('''CREATE TABLE shoutouts (id INTEGER PRIMARY KEY, command TEXT, so_user TEXT, chat_text TEXT, twitch_clip TEXT)''')
	con.commit()
	with open(command_file) as f:
		data = json.load(f)
		for c in data["commands"]:
			sql_str="INSERT INTO commands(command,command_type,permission,num_args,arguments,action) VALUES(?,?,?,?,?,?)"
			print "Inserting",c["command"]
			cur.execute(sql_str,(c["command"],c["command_type"],c["permission"],int(c["num_args"]),c["arguments"],c["action"]))
		con.commit()

if __name__ == "__main__":
	if len(sys.argv) == 2:
		initialize(sys.argv[1])

