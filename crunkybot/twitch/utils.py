# utils.py

import crunkycfg as cfg
import urllib2, json
import time, thread
import random
import re
import os
import subprocess
import musicutils
import sqlite3 as sql
import time
import requests
import json
import datetime
from collections import deque
from time import sleep
from dbutils import *

CURR_RAFFLE=[]
raffle_live=False
raffle_title=""
youtube_dl="youtube-dl -x --audio-format mp3 --prefer-ffmpeg"
#https://m.youtube.com/watch?v=dJ7bquKFC4E
youtube_re_str="(http(s)?://www\.youtube\.com/watch\?v=([-A-Za-z0-9_])+)|(http(s)?://www\.youtube\.com/watch/([-A-Za-z0-9_])+)|(http(s)?://youtu\.be/([-A-Za-z0-9_])+)|(http(s)://m\.youtube\.com/watch\?v=([-A-Za-z0-9_])+)"
youtube_re=re.compile(youtube_re_str)
dl_location=cfg.MUSIC_DOWNLOAD_DIR
db_location=cfg.DB_PATH
viewer_queue=deque([])

command_db=CommandDB(db_location)

def execute_command(sock,username,message,command):
    action_str=command["action"]
    num_args=int(command["num_args"])
    argument_defs=command["arguments"].split(",")
    #Split message into arguments
    message_split=message.split()
    arg_idx=0
    args={}
    for i in range(num_args):
        args[argument_defs[i]]="'"+message_split[i]+"'"
    if num_args > 0:
        args[argument_defs[i]]="'"+" ".join(message_split[i:len(message_split)])+"'"
    args["s"]="sock"
    args["u"]="username"
    # Match arguments with action.
    action_regex_str=r"[^%]*%(?P<argname>[-A-Za-z0-9_]+)"
    action_re=re.compile(action_regex_str)
    matches=action_re.findall(action_str)
    match_res=[]
    for m in matches:
        if m in args:
            action_str=re.sub("%"+m,args[m],action_str,1)
    ret = {}
    if ((command["permission"]=="MODERATOR" and isOp(username)) or
        (command["permission"]=="OWNER" and username.lower() == "cockeyedgaming") or
        (command["permission"]=="ALL")):
        print "Trying to evaluate..."
        ret=eval(action_str)
    else:
        print username,"does not have permission to execute",command["action"]
    return ret

def remove_chatcomm(sock,command):
    if command[0] == "!":
        command=command[1:]
    command_obj=command_db.get_command(command)
    if command_obj:
        command_db.remove_command(command_obj)
        chat(sock,command+" successfully removed!")
        return {"command":("REMOVE",command_obj)}
    return {}

def add_chatcomm(sock,command,text):
    if command[0] == "!":
        command=command[1:]
    text=text.replace("'",r"\'")
    command_obj=Command([command,"CHAT","ALL",0,"","chat(%s,'"+text+"')"])
    command_db.add_command(command_obj)
    chat(sock,command+" successfully added!")
    return {"command":("ADD",command_obj)}

def remove_shoutout(sock,so_user):
    if so_user[0] == "@":
        so_user=so_user[1:]
    shoutout_obj=command_db.get_shoutout(so_user)
    command_obj=command_db.get_command(shoutout_obj["command"])
    if shoutout_obj and command_obj:
        command_db.remove_command(command_obj)
        command_db.remove_shoutout(shoutout_obj)
        chat(sock,"Shoutout for "+so_user+" successfully removed!")
        return {"command":("REMOVE",command_obj),"shoutout":("REMOVE",shoutout_obj)}
    return {}

def add_shoutout(sock,command_name,so_user,twitch_clip,chat_text):
    chat_text=chat_text.replace("'",r"\'")
    if command_name[0] == "!":
        command_name=command_name[1:]
    shoutout_obj=Shoutout([command_name,so_user,twitch_clip,chat_text])
    shoutout_obj,command_obj=command_db.add_shoutout(shoutout_obj)
    chat(sock,"Shoutout for "+so_user+" successfully added!")
    return {"command":("ADD",command_obj),"shoutout":("ADD",shoutout_obj)}

def add_command(sock,username,command_name,action_function):
    return False

def process_song_request(sock,user,message):
    print "Processing..."
    if not message:
        chat(sock, "Gotta use a YouTube search or link "+user+", you n00b!")
        return False
    vid=message.split(" ")[0]
    vid2=vid
    if "&" in vid:
        vid2=vid.split("&")[0]
    m=youtube_re.match(vid2)
    if m:
        try:
            res=musicutils.get_vid_info(vid2)
            if res:
                (vidid,title)=(res[0],res[1])
                chat(sock,title+" requested by "+user+" added to the queue!")
                return (vidid,title,vid2)
            else:
                chat(sock,"Video must be < 7 minutes long.")
                return False
        except Exception,e:
            print "Exception",e
    else:
        res=musicutils.youtube_search(message)
        try:
            res2=musicutils.get_vid_info("https://www.youtube.com/watch?v="+res)
            if res2:
                (vidid,title)=(res2[0],res2[1])
                chat(sock,title+" requested by "+user+" added to the queue!")
                return (vidid,title,"https://www.youtube.com/watch?v="+res)
            else:
                chat(sock,"Video must be < 7 minutes long.")
                return False
        except Exception,e:
            print "Exception",e
    return False
                
def download_song_request(vid):
    try:
        musicutils.download_vid(vid)
    except Exception,e:
        print "Soft failure.",e
# Function: song_request
def change_playlist(s,user,message,proc):
    if(isOp(user)):
        conn=sql.connect(db_location)
        c=conn.cursor()
        message=message.strip()
        playlist_id=-1
        playlist_name=None
        try:
            playlist_id=int(message)
        except:
            playlist_name=message
        if playlist_id >= 0:
            # playlists (id INTEGER PRIMARY KEY, playlist_name TEXT, user_added TEXT)
            c.execute('''SELECT * FROM playlists WHERE id=?''', (playlist_id,))
            rows=c.fetchall()
            if rows:
                c.execute('''INSERT INTO playlist_requests(playlist_id) VALUES(?)''',(playlist_id,))
                conn.commit()
        elif playlist_name:
            c.execute('''SELECT * FROM playlists WHERE playlist_name=?''', (playlist_name.lower(),))
            rows=c.fetchall()
            if rows:
                curr_playlist_id=rows[0]
                c.execute('''INSERT INTO playlist_requests(playlist_id) VALUES(?)''',(curr_playlist_id,))
                conn.commit()
        else:
            chat(sock,"No playlist with that name or ID.")

# Download youtube song and add to request list.
def commit_song_request(conn, user, vid, vidid, title):
    print "COMMITTING...",vid,user
    vid=vid.split(" ")[0]
    if "&" in vid:
        vid=vid.split("&")[0]
    m=youtube_re.match(vid)
    if m:
        c=conn.cursor()
        try:
            c.execute("INSERT INTO requests(youtube_id,title,file_location,user_added,date_added) VALUES(?,?,?,?,?)",(vid,title,cfg.MUSIC_DOWNLOAD_DIR+"/"+vidid+".mp3",user,time.strftime("%Y-%m-%d")))
            print 'executing'
            conn.commit()
            print 'committed'
        except Exception,e:
            print "Soft failure.",e

def current_song_chat(sock,user):
    cs=current_song(sock,user)
    if cs:
        chat(sock,"Currently playing: "+cs)
    else:
        chat(sock,"No song is currently playing.")

def current_song(sock, user):
    if os.path.exists("current_track.txt"):
        with open("current_track.txt") as f:
            current_song=f.readlines()[0].split(",")
            return current_song[0]+" (requested by: "+current_song[1]+")"
            #chat(sock,"Currently playing: "+current_song)
    else:
        return ""

def skip_song(sock,user,proc):
    if isOp(user) or user.lower() == "cockeyedgaming":
        currsong=current_song(sock,user)
        if currsong:
            chat(sock,"Skipping "+currsong+"...")
            proc.skip()
       
# Function: load_insults
# Loads insults from a text file.
def load_insults(insult_file):
    insults=[]
    with open(insult_file) as f:
        for line in f.readlines():
            insult=line.split("&")
            insults.append((insult[0],insult[1]))
    return insults

def insult(sock,user,message,insults):
    if insults:
        insult_object=message
        insult=random.choice(insults)
        if not insult_object:
            insult_object=user
        chat(sock,user+" "+insult[0]+" "+insult_object+" "+insult[1])


def shoutout(sock,user,message):
    if isOp(user) or user.lower() == "cockeyedgaming":
        streamer=message.strip()
        chat(sock,"Have you heard of our friend "+streamer+"?? Check them out over at twitch.tv/"+streamer+" !")
# Function: chat
# Send a chat message to the server.
#    Parameters:
#      sock -- the socket over which to send the message
#      msg  -- the message to send
def chat(sock, msg, debug=False):
    if not debug:
        sock.send("PRIVMSG #{} :{}\r\n".format(cfg.TWITCH_CHAN, msg.encode('utf-8')))
    else:
        print msg

# Function: ban
# Ban a user from the channel
#   Parameters:
#       sock -- the socket over which to send the ban command
#       user -- the user to be banned
def ban(sock, user):
    chat(sock, ".ban {}".format(user))

# Function: timeout
# Timeout a user for a set period of time
#   Parameters:
#       sock -- the socket over which to send the timeout command
#       user -- the user to be timed out
#       seconds -- the length of the timeout in seconds (default 600)
def timeout(sock, user, seconds=600):
    chat(sock, ".timeout {}".format(user, seconds))

# Function: threadFillOpList
# In a separate thread, fill up the op list
def threadFillOpList():
    while True:
        try:
            url = "http://tmi.twitch.tv/group/user/cockeyedgaming/chatters"
            req = urllib2.Request(url, headers={"accept": "*/*"})
            response = urllib2.urlopen(req).read()
            if response.find("502 Bad Gateway") == -1:
                cfg.oplist.clear()
                data = json.loads(response)
                for p in data["chatters"]["moderators"]:
                    cfg.oplist[p] = "mod"
                for p in data["chatters"]["global_mods"]:
                    cfg.oplist[p] = "global_mod"
                for p in data["chatters"]["admins"]:
                    cfg.oplist[p] = "admin"
                for p in data["chatters"]["staff"]:
                    cfg.oplist[p] = "staff"
        except:
            'do nothing'
        sleep(5)

# Function: threadFillFollowers
# IN a separate thread, fill up followers list
def threadFillFollowerList():
    while True:
        try:
            r=requests.get(cfg.TWITCH_FOLLOWS_URL+"?limit=20",headers=cfg.TWITCH_HEADERS)
            json_dict=json.loads(r.text)
            response=[x['user']['name'] for x in json_dict['follows'] if x['user']['name'] not in cfg.followerlist]
            cfg.followerlist.extend(response)
            while len(response) == 20:
                cursor=json_dict['_cursor']
                r=requests.get(cfg.TWITCH_FOLLOWS_URL+"?limit=20&cursor="+cursor,headers=cfg.TWITCH_HEADERS)
                json_dict=json.loads(r.text)
                response=[x['user']['name'] for x in json_dict['follows'] if x['user']['name'] not in cfg.followerlist]
                cfg.followerlist.extend(response)
            #Fill subs.
            r=requests.get(cfg.TWITCH_SUB_URL+"?limit=20",headers=cfg.TWITCH_SUB_HEADERS)
            json_dict=json.loads(r.text)
            response=[x['user']['name'] for x in json_dict['subscriptions'] if x['user']['name'] not in cfg.sublist]
            cfg.sublist.extend(response)
            total = json_dict['_total']
            cursor=20
            while cursor < total:
                r=requests.get(cfg.TWITCH_SUB_URL+"?limit=20&offset="+`cursor`,headers=cfg.TWITCH_SUB_HEADERS)
                json_dict=json.loads(r.text)
                response=[x['user']['name'] for x in json_dict['subscriptions'] if x['user']['name'] not in cfg.sublist]
                cfg.sublist.extend(response)
                cursor+=20
        except Exception as e:
            print e
        sleep(60)
            
# Function isOP
# Determines if user has elevated privilege (used for things like !rafflestop)
def isOp(user):
    return user in cfg.oplist or user.lower() == "cockeyedgaming"

# Function isFollower
# Determins if user is a follower.
def isFollower(user):
    return user.lower() in cfg.followerlist or user.lower() == "cockeyedgaming"

def isSubscriber(user):
    return user.lower() in cfg.sublist or user.lower() == "cockeyedgaming"

# RAFFLE FUNCTIONS
def add_to_raffle(sock,user):
    global CURR_RAFFLE
    if user not in CURR_RAFFLE:
        num_entries=1
        if isSubscriber(user):
            num_entries=3
        for i in range(num_entries):
            CURR_RAFFLE.append(user)
        chat(sock, "Thanks "+user+"! You have a "+`num_entries`+" in "+`len(CURR_RAFFLE)`+" chance of winning...")
    else:
        chat(sock, user+" is already in the raffle!")

# Function raffle
# For users to enter a raffle: !raffle
def raffle(sock, user):
    global raffle_live,CURR_RAFFLE,raffle_title
    if raffle_live:
        add_to_raffle(sock,user)
    elif not raffle_live:
        chat(sock, "Umm... we're not MADE of SWAG! (...there is no live raffle)")

# Function raffle_start
# For moderators to start a raffle! Checks user to see if they are a mod, raffled item should be typed after.
# i.e. !rafflestart A copy of Streamline
def raffle_start(sock, user, raffle_info):
    global raffle_live,raffle_title
    if isOp(user) and not raffle_live:
        raffle_live=True
        raffle_title=raffle_info
        chat(sock, "Raffle has started! Type !raffle to enter for a chance to win "+raffle_title)

def raffle_draw(sock, user):
    global raffle_live,CURR_RAFFLE,raffle_title
    if isOp(user) and raffle_live and CURR_RAFFLE:
        this_raffle=[x for x in CURR_RAFFLE if isFollower(x)]
        draw=random.sample(this_raffle,1)[0]
        chat(sock, "Congrats to "+draw+"... You've won "+raffle_title+"! (Now gently brush off the haters)")
    else:
        print "Likely the opList is out of sync..."

def raffle_stop(sock,user):
    global raffle_live,CURR_RAFFLE,raffle_title
    if isOp(user) and raffle_live:
        CURR_RAFFLE=[]
        raffle_title=""
        raffle_live=False
        print "Raffle has stopped."
        
# Queue functions.
def add_to_queue(sock,user):
    global viewer_queue
    if user not in viewer_queue:
        viewer_queue.append(user)
        print viewer_queue

# !pop_queue 3 would give the next 3 users in the queue.    
def pop_queue(sock,user,n):
    global viewer_queue
    n=int(n)
    if isOp(user):
        m=min(n,len(viewer_queue))
        if m > 0:
            next_users=[viewer_queue.popleft() for x in range(m)]
            chat(sock, "Up next: "+", ".join(next_users))
        else:
            chat(sock, "Nobody wants to play?? Type !queue to join us!")
        
def get_queue(sock):
    global viewer_queue
    if viewer_queue:
        chat_string="Playing next: "
        user_list=[]
        for x in range(min(3,len(viewer_queue))):
            user_list.append(`x+1`+". "+viewer_queue[x])
        chat_string+=", ".join(user_list)
        chat(sock, chat_string)
    else:
        chat(sock, "Nobody in queue?! Type !queue to join us!")

test_uptime_data={
  "data": [
    {
      "id": "26007494656",
      "user_id": "23161357",
      "game_id": "417752",
      "community_ids": [
        "5181e78f-2280-42a6-873d-758e25a7c313",
        "848d95be-90b3-44a5-b143-6e373754c382",
        "fd0eab99-832a-4d7e-8cc0-04d73deb2e54"
      ],
      "type": "live",
      "title": "Hey Guys, It's Monday - Twitter: @Lirik",
      "viewer_count": 32575,
      "started_at": "2017-08-14T16:08:32Z",
      "language": "en",
      "thumbnail_url": "https://static-cdn.jtvnw.net/previews-ttv/live_user_lirik-{width}x{height}.jpg"
    }
  ],
  "pagination": {
    "cursor": "eyJiIjpudWxsLCJhIjp7Ik9mZnNldCI6MjB9fQ=="
  }
}
def uptime(sock):
    try:
        strT=cfg.TWITCH_V2_STREAMS_URL+"?user_id=cockeyedgaming"
        r=requests.get(cfg.TWITCH_V2_STREAMS_URL+"?user_login=CockeyedGaming",headers=cfg.TWITCH_V2_HEADERS)
        json_dict=json.loads(r.text)
        #json_dict=test_uptime_data
        #print "here"
        #print json_dict
        if json_dict['data'] and json_dict['data'][0]['type'] == 'live':
            timestamp=json_dict['data'][0]['started_at']
            dt_timestamp=datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
            now=datetime.datetime.utcnow()
            diff = now-dt_timestamp
            diff_str=str(diff).split(",")
            time_idx=0
            live_str=""
            if len(diff_str) > 1:
                live_str=diff_str[0]+", "
                time_idx=1
            hours=diff_str[time_idx].split(":")
            live_str+=hours[0]+" hours and "+`int(hours[1])`+" minutes."
            chat(sock,"Stream has been live for "+live_str)
            # "2017-08-14T15:45:17Z"
        else:
            chat(sock,"The stream isn't live :(.")
    except Exception as e:
        print "Error in ",e
