import discord
import config
import re
import utils
import time
import sqlite3 as sql
import random
import sys
import config
from dbutils import *

client = discord.Client()
client_user = client.user
youtube_re_str="(http(s)?://www\.youtube\.com/watch\?v=([-A-Za-z0-9_])+)|(http(s)?://www\.youtube\.com/watch/([-A-Za-z0-9_])+)|(http(s)?://youtu\.be/([-A-Za-z0-9_])+)|(http(s)://m\.youtube\.com/watch\?v=([-A-Za-z0-9_])+)"
youtube_re=re.compile(youtube_re_str)
db=DiscordDB(db_location=config.DB_LOCATION)
dj_responses=["${song} ?! FUCK YEAH ${username}! <:CockeyPuff:446555460682776576>",
                "${song} is my jaammmmmmm ${username}!", 
                "... ${song}... really ${username}?... alright, we'll add it anyways. <:CockeyRage:365682294134013952>"]


@client.event
async def on_ready():
    print("Crunky is ready to rollllll...")
    await client.change_presence(game=discord.Game(name="Bottin n stuffs"))
    for x in client.get_all_emojis():
         print(x)


@client.event
async def on_message(message):
    if message.channel.server.name.lower() == config.HOST_SERVER and message.channel.name.lower() == config.MUSIC_CHANNEL and message.author != client.user:
        youtube_data=await parse_youtube_message(message)
    elif message.channel.server.name.lower() == config.HOST_SERVER and message.author != client.user:
        message_data=await parse_social_message(message)
    return

@client.event
async def on_message_edit(before_message,after_message):
    db_message=db.get_message_by_id(before_message.id)
    db_message.message_id_=after_message.id
    db_message.mentions_=",".join(after_message.mentions)
    db_message.content_=after_message.content
    db_message.reactions_=",".join(after_message.reactions)
    db.update_message(before_message.id,db_message)
    return db_message

@client.event
async def on_reaction_add(reaction,user):
    db_message=db.get_message_by_id(reaction.message.id)
    reaction=Reaction(user.id,db_message.id,reaction.emoji.id)
    db.add_reaction(reaction)
    return reaction

async def parse_social_message(message):
    author=message.author
    db_user=db.get_user_by_id()
    # If user is not in database, add them.
    if not db_user:
        db_user=User({"user_id":author.id,"user_name":author.name,"roles":",".join(author.roles)})
        db.add_user(db_user)
    # Create DB Message object
    message=Message({"user_id":db_user.user_id_,"channel_id":message.channel.id,"content":message.content,"reactions":None,"mentions":",".join(message.mentions)})
    db.add_message(message)
    return message


async def parse_youtube_message(message):
    if config.MUSIC_ROLE in [y.name.lower() for y in message.author.roles]:
        match=youtube_re.search(message.content)
        if match:
            success=utils.get_vid_info(match[0])
            if success:
                vidid,title,result=success
                if result['duration'] <= 420 and 'Music' in result['categories']:
                    # Must be less than 7 minutes.
                    # Can test other things with: view_count, like_count, average_rating, etc.
                    utils.download_vid(match[0])
                else:
                    await client.send_message(message.channel,"MEMORY FULL!!!!! (Video has to be < 7 minutes long "+message.author.name+".)")
                    return None
                dbres=await add_to_database(message,vidid,title,message.author.name)
                if dbres:
                    response=random.sample(dj_responses, 1)[0]
                    response=response.replace("${username}",message.author.name).replace("${song}",title)
                    await client.send_message(message.channel,response)
                    return response
                else:
                    await client.send_message(message.channel,"Really?! :CockeyRage: (try a different YouTube link, this one couldn't download)")
                    return None
    return None

async def add_to_database(message,vidid,title,added_by):
    try:
        conn=sql.connect(config.DB_LOCATION)
        cur=conn.cursor()
        cur.execute('''SELECT * FROM playlists WHERE (playlist_name=?)''',(config.DB_PLAYLIST_ID,))
        entry = cur.fetchone()
        rid=-1
        if entry is None:
            cur.execute('''INSERT INTO playlists(playlist_name,user_added) VALUES(?,?)''',(config.DB_PLAYLIST_ID,"cockeyedgaming"))
            rid=cur.lastrowid
            conn.commit()
        else:
            rid=entry[0]
        cur.execute('''INSERT INTO tracks(playlist_id,youtube_id,title,file_location,user_added,date_added,num_plays) VALUES(?,?,?,?,?,?,?)''',(rid,vidid,title,config.MUSIC_DL_LOCATION+vidid+".mp3",added_by,time.strftime("%Y-%m-%d"),0))
        conn.commit()
        conn.close()
        return True
    except:
        print("Unexpected error:", sys.exc_info()[0], sys.exc_info()[1])
        await client.send_message(message.channel,"Ay, you broke me! :frowning: <:cockeyBlameCrunk:429210836041596928>")
        return False

client.run(config.DISCORD_TOKEN)

