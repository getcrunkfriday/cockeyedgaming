import discord
import config
import re
import utils
import time
import sqlite3 as sql

client = discord.Client()
youtube_re_str="(http(s)?://www\.youtube\.com/watch\?v=([-A-Za-z0-9_])+)|(http(s)?://www\.youtube\.com/watch/([-A-Za-z0-9_])+)|(http(s)?://youtu\.be/([-A-Za-z0-9_])+)|(http(s)://m\.youtube\.com/watch\?v=([-A-Za-z0-9_])+)"
youtube_re=re.compile(youtube_re_str)

@client.event
async def on_ready():
	print("Crunky is ready to rollllll...")
	await client.change_presence(game=discord.Game(name="Bottin n stuffs"))

@client.event
async def on_message(message):
	print("Message received= "+message.content+" "+message.channel.name)
	if message.channel.server.name.lower() == config.HOST_SERVER and message.channel.name.lower() == config.MUSIC_CHANNEL and message.author != client.user:
		youtube_data=parse_youtube_message(message)	
	return

def parse_youtube_message(message):
	if config.MUSIC_ROLE in [y.name.lower() for y in message.author.roles]:
		match=youtube_re.search(message.content)
		if match:
			print("This is a music request for: "+match[0])
			success=utils.get_vid_info(match[0])
			if success:
				vidid,title,result=success
				if result['duration'] <= 420 and 'Music' in result['categories']:
					# Must be less than 7 minutes.
					# Can test other things with: view_count, like_count, average_rating, etc.
					utils.download_vid(match[0])
				print("Downloading: "+vidid+" - "+title)
				add_to_database(vidid,title,message.author.name)

def add_to_database(vidid,title,added_by):
	conn=sql.connect(config.DB_LOCATION)
	c=conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS playlist (id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added TEXT, num_plays INTEGER)''')
	sql_str="INSERT INTO playlist(playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays) VALUES (?,?,?,?,?,?,?)"
	c.execute(sql_str,(config.DB_PLAYLIST_ID,vidid,title,config.MUSIC_DL_LOCATION+vidid+".mp3",added_by,time.strftime("%Y-%m-%d"),0))
	conn.commit()
	print("Committing...")

client.run(config.DISCORD_TOKEN)

