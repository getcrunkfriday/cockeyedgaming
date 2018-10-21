import sqlite3 as sql

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

class MusicDB:
	def __init__(self,db_location):
		self.connection_=sql.connect(db_location)
		cur = self.connection_.cursor()
		cur.execute('''CREATE TABLE IF NOT EXISTS tracks(id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added DATE, num_plays INT)''')
		cur.execute('''CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added DATE)''')
		cur.execute('''CREATE TABLE IF NOT EXISTS playlists(id INTEGER PRIMARY KEY, playlist_name TEXT, user_added TEXT, UNIQUE(playlist_name))''')
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
			return (False,"Track with YouTube ID "+track.youtube_id_+" is already in playlist "+track.playlist_id_)
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