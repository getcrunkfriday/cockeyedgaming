import sqlite3 as sql
from typing import Optional, Tuple, Any, Dict, List
import json

INT = "INTEGER"
TEXT = "TEXT"
PRIMARY_KEY = "PRIMARY KEY"
INSERT = "INSERT OR IGNORE"
W = "?"


class Playlist:
	"""Class for entries into the playlists table."""
	def __init__(
		self,
		playlist_name: str,
		user_added: str,
		youtube_id: Optional[str] = None
	):
		self.playlist_name = playlist_name
		self.user_added = user_added
		self.youtube_id = youtube_id
		self.rid = None

	def set_id(self, rid: int) -> None:
		self.rid = rid

	def get_fields(self) -> Tuple[int, str, str, str]:
		return self.rid, self.playlist_name, self.user_added, self.youtube_id


class Track:
	"""Class for entries into the tracks table."""
	def __init__(
		self,
		playlist_id: int,
		youtube_id: str,
		title: str,
		file_location: str,
		user_added: str,
		date_added: str,
		num_plays: int = 0
	):
		self.playlist_id = playlist_id
		self.youtube_id = youtube_id
		self.title = title
		self.file_location = file_location
		self.user_added = user_added
		self.date_added = date_added
		self.num_plays = num_plays
		self.rid = None

	def set_id(self, rid: int) -> None:
		self.rid = rid

	def get_fields(self) -> Tuple[int, int, str, str, str, str, str, int]:
		return (
			self.rid,
			self.playlist_id,
			self.youtube_id,
			self.title,
			self.file_location,
			self.user_added,
			self.date_added,
			self.num_plays
		)


class Request:
	""" Class for entries into the requests table."""
	def __init__(
		self,
		playlist_id: str,
		youtube_id: str,
		title: str,
		file_location: str,
		user_added: str,
		date_added: str
	):
		self.playlist_id = playlist_id
		self.youtube_id = youtube_id
		self.title = title
		self.file_location = file_location
		self.user_added = user_added
		self.date_added = date_added
		self.rid = None

	def set_id(self, rid: int) -> None:
		self.rid = rid

	def get_fields(self) -> Tuple[int, str, str, str, str, str, str]:
		return (
			self.rid,
			self.playlist_id,
			self.youtube_id,
			self.title,
			self.file_location,
			self.user_added,
			self.date_added
		)


class Command:
	def __init__(self, vals: Tuple[str, str, str, int, str, str]):
		self.command = {
			"rid": None,
			"command": vals[0],
			"command_type": vals[1],
			"permission": vals[2],
			"num_args": vals[3],
			"arguments": vals[4],
			"action": vals[5]
		}

	def get_fields(self) -> Tuple[str, str, str, int, str, str]:
		return (
			self["command"],
			self["command_type"],
			self["permission"],
			self["num_args"],
			self["arguments"],
			self["action"]
		)

	def set_id(self, rid: int) -> None:
		self["rid"] = rid

	def __getitem__(self, key: str) -> Any:
		return self.command[key]

	def __setitem__(self, key: str, value: Any) -> None:
		self.command[key] = value


class Shoutout:
	def __init__(self, vals: Tuple[str, str, str, str]):
		self.command = {
			"rid": None,
			"command": vals[0],
			"so_user": vals[1],
			"twitch_clip": vals[2],
			"chat_text": vals[3],
			"was_seen": False
		}

	def get_fields(self) -> Tuple[str, str, str, str]:
		return (
			self["command"],
			self["so_user"],
			self["chat_text"],
			self["twitch_clip"]
		)

	def set_id(self, rid: int) -> None:
		self["rid"] = rid

	def __getitem__(self, key: str) -> str:
		return self.command[key]

	def __setitem__(self, key: str, value: Any) -> None:
		self.command[key] = value


class CommandDB:
	"""Helper functions for the commands database."""
	def __init__(self, db_location: str):
		self.db_location = db_location
		self.connection = sql.connect(db_location)
		self.is_open = True
		cur = self.connection.cursor()
		cur.execute(f'''CREATE TABLE IF NOT EXISTS chat_commands (id {INT} {PRIMARY_KEY}, command {TEXT}, command_type {TEXT}, permission {TEXT}, num_args {INT}, arguments {TEXT}, action {TEXT}, UNIQUE(command))''')
		cur.execute(f'''CREATE TABLE IF NOT EXISTS shoutouts (id {INT} {PRIMARY_KEY}, command {TEXT}, so_user {TEXT}, chat_text {TEXT}, twitch_clip {TEXT}, UNIQUE(command, so_user))''')
		self.connection.commit()

	def init_db(self, command_file: str) -> None:
		cur = self.connection.cursor()
		with open(command_file) as f:
			data = json.load(f)
			for c in data["commands"]:
				sql_str = f"{INSERT} chat_commands(command,command_type,permission,num_args,arguments,action) VALUES({W},{W},{W},{W},{W},{W})"
				cur.execute(sql_str, (c["command"], c["command_type"], c["permission"], int(c["num_args"]), c["arguments"], c["action"]))
			self.connection.commit()

	def close(self):
		if self.is_open:
			self.connection.close()
			self.is_open = False

	def open(self):
		if not self.is_open:
			self.connection = sql.connect(self.db_location)
			self.is_open = True

	def load_commands(self) -> Dict:
		self.open()
		commands = {}
		cur = self.connection.cursor()
		sql_str = """SELECT * FROM chat_commands"""
		cur.execute(sql_str)
		rows = cur.fetchall()
		self.close()
		for row in rows:
			cmd = Command(row[1:])
			commands[row[1]] = cmd
		return commands

	def load_shoutouts(self) -> Dict:
		self.open()
		shoutouts = {}
		cur = self.connection.cursor()
		sql_str = """SELECT * FROM shoutouts"""
		cur.execute(sql_str)
		rows = cur.fetchall()
		self.close()
		for row in rows:
			cmd = Shoutout(row[1:])
			shoutouts[cmd['so_user'].lower()] = cmd
		return shoutouts

	def add_command(self, command: Command) -> Command:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''{INSERT} INTO chat_commands (command, command_type, permission, num_args, arguments, action) VALUES({W},{W},{W},{W},{W},{W})''', command.get_fields())
		self.connection.commit()
		self.close()
		return command

	def add_shoutout(self, shoutout: Shoutout) -> Tuple[Shoutout, Command]:
		self.open()
		cur = self.connection.cursor()
		command = Command((shoutout["command"], "CHAT", "MODERATOR", 0, "", "chat(%s,%u,'"+" : ".join([shoutout["chat_text"], shoutout["twitch_clip"]])+"')"))
		cur.execute(f'''{INSERT} INTO shoutouts (command,so_user,chat_text,twitch_clip) VALUES({W},{W},{W},{W})''', shoutout.get_fields())
		cur.execute(f'''{INSERT} INTO chat_commands (command, command_type, permission, num_args, arguments, action) VALUES({W},{W},{W},{W},{W},{W})''', command.get_fields())
		self.connection.commit()
		self.close()
		return shoutout, command

	def remove_command(self, command: Command):
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''DELETE FROM chat_commands WHERE command={W}''', (command["command"],))
		self.connection.commit()
		self.close()

	def get_command(self, command_name: str) -> Optional[Command]:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''SELECT * FROM chat_commands WHERE command={W}''', (command_name,))
		cmd_obj = cur.fetchone()
		self.close()
		if cmd_obj:
			return Command(cmd_obj[1:])
		else:
			return None

	def remove_shoutout(self, shoutout: Shoutout):
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''DELETE FROM chat_commands WHERE command={W}''', (shoutout["command"],))
		cur.execute(f'''DELETE FROM shoutouts WHERE command={W}''', (shoutout["command"],))
		self.connection.commit()
		self.close()

	def get_shoutout(self, so_user: str) -> Optional[Shoutout]:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''SELECT * FROM shoutouts WHERE so_user={W}''', (so_user,))
		so_obj = cur.fetchone()
		self.close()
		if so_obj:
			return Shoutout(so_obj[1:])
		else:
			return None

class MusicDB:
	"""Helper functions for the music and playlist database."""
	def __init__(self, db_location: str):
		self.db_location = db_location
		self.connection = sql.connect(db_location)
		self.is_open = True
		cur = self.connection.cursor()
		cur.execute(f'''CREATE TABLE IF NOT EXISTS tracks(id {INT} {PRIMARY_KEY}, playlist_id {INT}, youtube_id {TEXT}, title {TEXT}, file_location {TEXT}, user_added {TEXT}, date_added DATE, num_plays {INT})''')
		cur.execute(f'''CREATE TABLE IF NOT EXISTS requests(id {INT} {PRIMARY_KEY}, playlist_id {INT}, youtube_id {TEXT}, title {TEXT}, file_location {TEXT}, user_added {TEXT}, date_added DATE)''')
		cur.execute(f'''CREATE TABLE IF NOT EXISTS playlist_requests (id {INT} {PRIMARY_KEY}, playlist_id {INT}, num_requests {INT})''')
		cur.execute(f'''CREATE TABLE IF NOT EXISTS playlists(id {INT} {PRIMARY_KEY}, playlist_name {TEXT}, user_added {TEXT}, youtube_id {TEXT}, UNIQUE(playlist_name,youtube_id))''')
		self.connection.commit()

	def close(self) -> None:
		if self.is_open:
			self.connection.close()
			self.is_open = False

	def open(self) -> None:
		if not self.is_open:
			self.connection =sql.connect(self.db_location)
			self.is_open = True

	def add_playlist(self, playlist: Playlist) -> Tuple[bool, int]:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''{INSERT} INTO playlists(playlist_name,user_added,youtube_id) VALUES({W},{W},{W})''', playlist.get_fields()[1:])
		rid = cur.lastrowid
		self.connection.commit()
		self.close()
		return True, rid

	def add_track_to_playlist(self, track: Track) -> Tuple[bool, int]:
		self.open()
		cur=self.connection.cursor()
		cur.execute(f'''SELECT * FROM tracks WHERE (playlist_id={W} AND youtube_id={W})''', (track.playlist_id, track.youtube_id,))
		entry = cur.fetchone()
		if entry is None:
			cur.execute(f'''INSERT INTO tracks(playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays) VALUES({W},{W},{W},{W},{W},{W},{W})''', track.get_fields()[1:])
			rid=cur.lastrowid
			self.connection.commit()
			self.close()
			return True, rid
		else:
			self.close()
			return True, entry[0]

	def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
		self.open()
		cur=self.connection.cursor()
		cur.execute(f'''SELECT * FROM playlists WHERE (id={W})''', (playlist_id,))
		entry = cur.fetchone()
		if entry is not None:
			playlist=Playlist(*entry[1:])
			playlist.set_id(entry[0])
			self.close()
			return playlist
		else:
			self.close()
			return None

	def get_playlist_by_youtube_id(self, youtube_id: str) -> Optional[Playlist]:
		self.open()
		cur=self.connection.cursor()
		cur.execute(f'''SELECT * FROM playlists WHERE (youtube_id={W})''', (youtube_id,))
		entry = cur.fetchone()
		if entry is not None:
			playlist=Playlist(*entry[1:])
			playlist.set_id(entry[0])
			self.close()
			return playlist
		else:
			self.close()
			return None

	def get_playlist_by_name(self, playlist_name: str) -> Optional[Playlist]:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''SELECT * FROM playlists WHERE (playlist_name={W})''', (playlist_name,))
		entry = cur.fetchone()
		if entry is not None:
			playlist=Playlist(*entry[1:])
			playlist.set_id(entry[0])
			self.close()
			return playlist
		else:
			self.close()
			return None

	def get_playlists(self) -> List[Playlist]:
		self.open()
		cur = self.connection.cursor()
		cur.execute('''SELECT * FROM playlists''')
		rows = cur.fetchall()
		self.close()
		playlists = []
		for row in rows:
			playlist = Playlist(*row[1:])
			playlist.set_id(row[0])
			playlists.append(playlist)
		return playlists

	def remove_track_from_playlist(self, playlist_id: int, track: Track) -> None:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''DELETE FROM tracks WHERE (playlist_id={W} AND youtube_id={W})''', (playlist_id, track.youtube_id))
		self.connection.commit()
		self.close()

	def remove_playlist(self, playlist_id: int) -> None:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''DELETE FROM tracks WHERE playlist_id={W}''', (playlist_id,))
		cur.execute(f'''DELETE FROM playlists WHERE id={W}''', (playlist_id,))
		self.connection.commit()
		self.close()

	def get_tracks(self, playlist_id: int) -> List[Track]:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''SELECT * FROM tracks WHERE (playlist_id={W})''', (playlist_id,))
		rows = cur.fetchall()
		self.close()
		tracks = []
		for row in rows:
			track = Track(*row[1:])
			track.set_id(row[0])
			tracks.append(track)
		return tracks

	def get_track_requests(self) -> List[Request]:
		self.open()
		cur = self.connection.cursor()
		cur.execute('''SELECT * FROM requests''')
		rows = cur.fetchall()
		tracks = []
		for row in rows:
			tracks.append(Request(*row[1:]))
			cur.execute(f'''DELETE FROM requests WHERE id={W}''', (row[0],))
		self.connection.commit()
		self.close()
		return tracks

	def add_playlist_request(self, playlist: Playlist, num_requests: int = 1) -> None:
		self.open()
		cur = self.connection.cursor()
		cur.execute(f'''INSERT INTO playlist_requests(playlist_id,num_requests) VALUES({W},{W})''', (playlist.rid, num_requests))
		self.connection.commit()
		self.close()

	def add_playlists_request(self, playlists: List[Playlist]) -> None:
		for playlist in playlists:
			self.add_playlist_request(playlist, len(playlists))

	def pop_playlist_request(self) -> Optional[Tuple[List[int], List[Track]]]:
		# Make a "Pop" method that gets the next playlist and deletes it from the DB.
		self.open()
		cur = self.connection.cursor()
		cur.execute('''SELECT * FROM playlist_requests''')
		rows = cur.fetchall()
		if rows:
			tracks = []
			playlist_ids = []
			num_playlists = rows[0][2]
			for i in range(num_playlists):
				playlist_request_id = rows[i][0]
				playlist_id = rows[i][1]
				playlist_ids.append(playlist_id)
				cur.execute(f'''DELETE FROM playlist_requests WHERE id={W}''', (playlist_request_id,))
				self.connection.commit()
				cur.execute(f'''SELECT * FROM tracks WHERE playlist_id={W}''', (playlist_id,))
				pl_rows = cur.fetchall()
				for pl_row in pl_rows:
					tracks.append(Track(*pl_row[1:]))
			self.close()
			return playlist_ids, tracks
		self.close()
		return None

	def purge_playlist_requests(self) -> None:
		self.open()
		cur = self.connection.cursor()
		cur.execute('''DROP TABLE playlist_requests''')
		self.connection.commit()
		self.close()

	def purge_requests(self) -> None:
		self.open()
		cur = self.connection.cursor()
		cur.execute('''DROP TABLE requests''')
		self.connection.commit()
		self.close()