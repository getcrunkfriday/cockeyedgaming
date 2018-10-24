import sqlite3 as sql
import json

class Playlist:
	''' Class for entriest into the playlists table.'''
	def __init__(self,playlist_name,user_added):
		self.playlist_name_=playlist_name
		self.user_added_=user_added
		self.rid_=None
	def set_id(self,rid):
		self.rid_=rid
	def get_fields(self):
		return (self.rid_,self.playlist_name_,self.user_added_)

class Track:
	'''Class for entries into the tracks table.'''
	def __init__(self,playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays=0):
		self.playlist_id_=playlist_id
		self.youtube_id_=youtube_id
		self.title_=title
		self.file_location_=file_location
		self.user_added_=user_added
		self.date_added_=date_added
		self.num_plays_=num_plays
		self.rid_=None
	def set_id(self,rid):
		self.rid_=rid
	def get_fields(self):
		return (self.rid_,self.playlist_id_,self.youtube_id_,self.title_,self.file_location_,self.user_added_,self.date_added_,self.num_plays_)

class Request:
	''' Class for entries into the requests table.'''
	def __init__(self,playlist_id,youtube_id,title,file_location,user_added,date_added):
		self.playlist_id_=playlist_id
		self.youtube_id_=youtube_id
		self.title_=title
		self.file_location_=file_location
		self.user_added_=user_added
		self.date_added_=date_added
		self.rid_=None
	def set_id(self,rid):
		self.rid_=rid
	def get_fields(self):
		return (self.rid_,self.playlist_id_,self.youtube_id_,self.title_,self.file_location_,self.user_added_,self.date_added_)

class Command:
    def __init__(self,vals):
        self.dict_={
        	"rid": None,
            "command": vals[0],
            "command_type": vals[1],
            "permission": vals[2],
            "num_args": vals[3],
            "arguments": vals[4],
            "action": vals[5]
        }
    def get_fields(self):
    	return (self["command"],self["command_type"],self["permission"],self["num_args"],self["arguments"],self["action"])
    def set_id(self,rid):
    	self["rid"]=rid
    def __getitem__(self,key):
        return self.dict_[key]
    def __setitem__(self,key,value):
        self.dict_[key]=value

class Shoutout:
    # shoutouts(command,chat_text,twitch_clip)
    def __init__(self,vals):
        self.dict_={
        	"rid": None,
            "command": vals[0],
            "so_user": vals[1],
            "twitch_clip": vals[2],
            "chat_text": vals[3],
            "was_seen": False
        }
    def get_fields(self):
    	return (self["command"],self["so_user"],self["chat_text"],self["twitch_clip"])
    def set_id(self,rid):
    	self["rid"]=rid
    def __getitem__(self,key):
        return self.dict_[key]
    def __setitem__(self,key,value):
        self.dict_[key]=value

class CommandDB:
	''' Helper functions for the commands database. '''
	def __init__(self,db_location):
		self.connection_=sql.connect(db_location)
		cur = self.connection_.cursor()
		cur.execute('''CREATE TABLE IF NOT EXISTS commands (id INTEGER PRIMARY KEY, command TEXT, command_type TEXT, permission TEXT, num_args INTEGER, arguments TEXT, action TEXT, UNIQUE(command))''')
		cur.execute('''CREATE TABLE IF NOT EXISTS shoutouts (id INTEGER PRIMARY KEY, command TEXT, so_user TEXT, chat_text TEXT, twitch_clip TEXT, UNIQUE(command, so_user))''')
		self.connection_.commit()
	def init_db(self,command_file):
		cur = self.connection_.cursor()
		with open(command_file) as f:
			data = json.load(f)
			for c in data["commands"]:
				sql_str="INSERT OR IGNORE INTO commands(command,command_type,permission,num_args,arguments,action) VALUES(?,?,?,?,?,?)"
				print "Inserting",c["command"]
				cur.execute(sql_str,(c["command"],c["command_type"],c["permission"],int(c["num_args"]),c["arguments"],c["action"]))
			self.connection_.commit()
	def load_commands(self):
	    commands={}
	    cur=self.connection_.cursor()
	    sql_str="""SELECT * FROM commands"""
	    cur.execute(sql_str)
	    rows=cur.fetchall()
	    print "Rows=",rows
	    for row in rows:
	        cmd=Command(row[1:])
	        commands[row[1]]=cmd
	    return commands
	def load_shoutouts(self):
	    shoutouts={}
	    cur=self.connection_.cursor()
	    sql_str="""SELECT * FROM shoutouts"""
	    cur.execute(sql_str)
	    rows=cur.fetchall()
	    print "Rows=", rows
	    for row in rows:
	        cmd=Shoutout(row[1:])
	        shoutouts[cmd['so_user'].lower()]=cmd
	    return shoutouts
	def add_command(self,command):
		cur = self.connection_.cursor()
		cur.execute('''INSERT OR IGNORE INTO commands (command, command_type, permission, num_args, arguments, action) VALUES(?,?,?,?,?,?)''', command.get_fields())
		self.connection_.commit()
		return command
	def add_shoutout(self,shoutout):
		cur = self.connection_.cursor()
		command=Command((shoutout["command"], "CHAT","MODERATOR","0","","chat(%s,'"+" : ".join([shoutout["chat_text"],shoutout["twitch_clip"]])+"')"))
		cur.execute('''INSERT OR IGNORE INTO shoutouts (command,so_user,chat_text,twitch_clip) VALUES(?,?,?,?)''', shoutout.get_fields())
		cur.execute('''INSERT OR IGNORE INTO commands (command, command_type, permission, num_args, arguments, action) VALUES(?,?,?,?,?,?)''', command.get_fields())
		self.connection_.commit()
		return (shoutout,command)
	def remove_command(self,command):
		cur = self.connection_.cursor()
		cur.execute('''DELETE FROM commands WHERE command=?''',(command["command"],))
		self.connection_.commit()
	def get_command(self,command_name):
		cur = self.connection_.cursor()
		cur.execute('''SELECT * FROM commands WHERE command=?''', (command_name,))
		cmd_obj=cur.fetchone()
		if cmd_obj:
			return Command(cmd_obj[1:])
		else:
			return None
	def remove_shoutout(self,shoutout):
		cur = self.connection_.cursor()
		cur.execute('''DELETE FROM commands WHERE command=?''',(shoutout["command"],))
		cur.execute('''DELETE FROM shoutouts WHERE command=?''',(shoutout["command"],))
		self.connection_.commit()
	def get_shoutout(self,so_user):
		cur = self.connection_.cursor()
		cur.execute('''SELECT * FROM shoutouts WHERE so_user=?''',(so_user,))
		so_obj=cur.fetchone()
		if so_obj:
			return Shoutout(so_obj[1:])
		else:
			return None


class MusicDB:
	'''Helper functions for the music and playlist database. '''
	def __init__(self,db_location):
		self.connection_=sql.connect(db_location)
		cur = self.connection_.cursor()
		cur.execute('''CREATE TABLE IF NOT EXISTS tracks(id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added DATE, num_plays INT)''')
		cur.execute('''CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added DATE)''')
		cur.execute('''CREATE TABLE IF NOT EXISTS playlist_requests (id INTEGER PRIMARY KEY, playlist_id INTEGER)''')
		cur.execute('''CREATE TABLE IF NOT EXISTS playlists(id INTEGER PRIMARY KEY, playlist_name TEXT, user_added TEXT, UNIQUE(playlist_name))''')
		self.connection_.commit()
	def add_playlist(self,playlist):
		cur=self.connection_.cursor()
		cur.execute('''INSERT OR IGNORE INTO playlists(playlist_name,user_added) VALUES(?,?)''',playlist.get_fields()[1:])
		rid=cur.lastrowid
		self.connection_.commit()
		return (True, rid)
	def add_track_to_playlist(self,track):
		cur=self.connection_.cursor()
		cur.execute('''SELECT * FROM tracks WHERE (playlist_id=? AND youtube_id=?)''',(track.playlist_id_,track.youtube_id_,))
		entry = cur.fetchone()
		if entry is None:
			cur.execute('''INSERT INTO tracks(playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays) VALUES(?,?,?,?,?,?,?)''',track.get_fields()[1:])
			rid=cur.lastrowid
			self.connection_.commit()
			return (True,rid)
		else:
			return (True,entry[0])
		return (False, "DB error.")
	def get_playlist_by_id(self,playlist_id):
		cur=self.connection_.cursor()
		cur.execute('''SELECT * FROM playlists WHERE (playlist_id=?)''',(playlist_id,))
		entry = cursor.fetchone()
		if entry is not None:
			playlist=Playlist(*entry[1:])
			playlist.set_id(entry[0])
			return playlist
		else:
			return False
	def get_playlist_by_name(self,playlist_name):
		cur=self.connection_.cursor()
		cur.execute('''SELECT * FROM playlists WHERE (playlist_name=?)''',(playlist_name,))
		entry = cur.fetchone()
		if entry is not None:
			playlist=Playlist(*entry[1:])
			playlist.set_id(entry[0])
			return playlist
		else:
			return False
	def get_tracks(self,playlist_id):
		cur=self.connection_.cursor()
		cur.execute('''SELECT * FROM tracks WHERE (playlist_id=?)''',(playlist_id,))
		rows = cur.fetchall()
		tracks=[]
		for row in rows:
			tracks.append(Track(*row[1:]))
		return tracks
	def get_track_requests(self):
		cur=self.connection_.cursor()
		cur.execute('''SELECT * FROM requests''')
		rows = cur.fetchall()
		tracks=[]
		for row in rows:
			tracks.append(Request(*row[1:]))
			cur.execute('''DELETE FROM requests WHERE id=?''', (row[0],))
		self.connection_.cursor()
		return tracks
	def pop_playlist_request(self):
		# Make a "Pop" method that gets the next playlist and deletes it from the DB.
		cur=self.connection_.cursor()
		cur.execute('''SELECT * FROM playlist_requests''')
		row = cur.fetchone()
		if row:
			playlist_id=row[1]
			cur.execute('''DELETE FROM playlist_requests WHERE playlist_id=?''', (playlist_id,))
        	con.commit()
        	cur.execute('''SELECT * FROM tracks WHERE playlist_id=?''', (playlist_id,))
        	pl_rows=cur.fetchall()
        	tracks=[]
        	for pl_row in pl_rows:
        		tracks.append(Track(*row[1:]))
        	return tracks
        return None
	def purge_requests(self):
		cur=self.connection_.cursor()
		cur.execute('''DROP TABLE requests''')
		self.connection_.commit()