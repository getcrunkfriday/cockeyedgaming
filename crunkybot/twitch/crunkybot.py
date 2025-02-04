import crunkycfg as cfg
import utils
import musicutils
import socket
import re
import time, _thread
import sys
import icescontroller
from time import sleep
from dbutils import Playlist
import time
import sys,os

insults = utils.load_insults(cfg.INSULTS)
stream_start_time=0
sr_enabled=True
base_commands = {
    # Text-based commands
    #"!streamote": lambda s,**kw : utils.chat(s,"Join us for Streamline bingo at: http://streamote.tv/cockeyedgaming"),
    #"!streamrpg": lambda s,**kw : utils.chat(s,"I'm sorry, are we boring you?! Fine, here: http://streamrpg.com/cockeyedgaming"),
    "insult"   : lambda s,u,m,**kw : utils.insult(s,u,m,insults),
    #"!opponent" : lambda s,**kw : utils.chat(s,"We are playing Yunalescka (https://twitch.tv/yunalescka) in the HotStreams Tourney! Give them a follow!"),
    #"!multi"    : lambda s,**kw : utils.chat(s,"Watch both teams... at the saaaame tiiime! https://multistre.am/cockeyedgaming/yunalescka/layout4/"),
    #"!race" : lambda s,**kw : utils.chat(s,"Watch the full race at: https://multistre.am/cockeyedgaming/ashplissken/layout3/"),
    #"!recipe"   : lambda s,**kw : utils.chat(s, "The \"Dirty Banana\" recipe can be found here: https://www.thespruce.com/dirty-banana-4133904."),
    #"!celebrate" : lambda s,**kw : utils.chat(s, "Come celebrate 200+ followers with us this Saturday! What's planned? Check http://bit.ly/2u9Ps9P !"),
    # Raffle commands
    "raffle"   : lambda s,u,**kw : utils.raffle(s,u),
    "rafflestop" : lambda s,u,**kw : utils.raffle_stop(s,u),
    "raffledraw" : lambda s,u,**kw : utils.raffle_draw(s,u),
    "rafflestart": lambda s,u,m,**kw : utils.raffle_start(s,u,m),
    # Queue commands
    #"!queue"    : lambda s,u,**kw : utils.add_to_queue(s,u),
    #"!popqueue" : lambda s,u,m,**kw : utils.pop_queue(s,u,m),
    #"!currqueue": lambda s,**kw   : utils.get_queue(s),
    # Music commands
    "sr"         : lambda s,u,m,**kw : song_request(s,u,m),
    "currentsong"   : lambda s,u,**kw   : utils.current_song_chat(s,u),
    "skip" : lambda s,u,proc,**kw : utils.skip_song(s,u,proc),
    "cp" : lambda s,u,m,proc,**kw : utils.change_playlist(s,u,m,proc),
    "playlists" : lambda s,u,m,**kw : utils.list_playlists(s,u),
    "sync": lambda s,u,**kw : sync_request(u),
    # Stream commands
    #"!startstream" : lambda s,u,**kw: start_stream(u),
    "uptime" : lambda s,**kw: utils.uptime(s),
    # "earthfall": lambda s,u,**kw: utils.chat(s, u,"Want to play Earthfall with us? Help support us as influencers by purchasing through our link! https://bit.ly/2NYsZm2"),
    "so": lambda s,u,m,**kw: utils.shoutout(s,u,m),
    "scream": lambda s,u,m,**kw: scream(s,u,m),
    "noscream": lambda s,u,m,**kw: noscream(s,u,m),
    "screams": lambda s,u,m,**kw: screams(s,u,m)
    # "addlegend": lambda s,u,m,**kw: add_legendary(s,u,m),
    # "legendaries": lambda s,u,m,**kw: get_legendaries(s,u,m),
    # "spill": lambda s,u,m,**kw: add_deaths(s,u,m),
    # "unspill": lambda s,u,m,**kw: remove_death(s,u,m),
    # "spills": lambda s,u,m,**kw: get_deaths(s,u,m)
    #"!togglesr": lambda s,u,m,**kw: toggle_sr(s,u,m)
    #"!commands": lambda s,**kw: chat_commands(s)
    }

download_queue=[]
legendaries=[]
deaths = 0
num_screams = 0
def add_legendary(s,u,m):
    global legendaries
    if utils.isOp(u) or u.lower() == cfg.TWITCH_CHAN:
        legendaries.append(m)
        utils.chat(s,u,m+" added to legendaries!")

def get_legendaries(s,u,m):
    utils.chat(s,u,"Crunk has discovered"+repr(len(legendaries))+"legendaries! ("+",".join(legendaries)+")")

def toggle_sr(s,u,m):
    global sr_enabled
    if utils.isOp(u) or u.lower() == cfg.TWITCH_CHAN:
        if sr_enabled:
            sr_enabled=False
        else:
            sr_enabled=True

def add_deaths(s,u,m):
    global deaths
    if utils.isOp(u) or u.lower() == "cockeyedgaming" or u.lower() == "firezerg_":
        deaths += 1
        utils.chat(s,u,"Ash has spilled her drink {deaths} times. What a clumsy bitch.")

def remove_death(s,u,m):
    global deaths
    if utils.isOp(u) or u.lower() == "cockeyedgaming" or u.lower() == "firezerg_":
        deaths -= 1 if deaths > 0 else 0
        utils.chat(s,u,"JK JK , she saved it. Only {deaths} spills!")

def get_deaths(s,u,m):
    utils.chat(s,u,"Ash has spilled her drink {deaths} times...")

def scream(s,u,m):
    global num_screams
    if utils.isOp(u) or u.lower() == "cockeyedgaming" or u.lower() == "getcrunkfriday":
        num_screams += 1
        utils.chat(s,u,"Ash just screamed like a little bitch. That's {num_screams} times now...")

def noscream(s,u,m):
    global num_screams
    if utils.isOp(u) or u.lower() == "cockeyedgaming" or u.lower() == "getcrunkfriday":
        num_screams -= 1
        utils.chat(s,u,"Nvm... that was just me. Ash has only screamed {num_screams} times now...")

def screams(s,u,m):
    utils.chat(s,u,"Ash has screamed {num_screams} times now... what a bitch. LUL")

def song_request(sock,username,message):
    global download_queue
    import threading
    res=utils.process_song_request(sock,username,message)
    if res:
        (vidid,title,url)=(res[0],res[1],res[2])
        download_thread=threading.Thread(target=utils.download_song_request,args=[url])
        download_thread.start()
        download_queue.append({
            'thread':download_thread,
            'request_type': 'sr',
            'user':username,
            'vid':url,
            'vidid':vidid,
            'title':title
        })

def sync_request(username="cockeyedgaming"):
    global download_queue
    import threading
    from dbutils import MusicDB
    if not utils.isOp(username):
        return
    print("Attempting to sync...")
    db_location=cfg.MUSIC_DB
    db=MusicDB(db_location)
    playlists_to_add, tracks_to_add, tracks_to_remove = musicutils.sync_playlists_to_db(db, cfg.YOUTUBE_PLAYLIST_CHANNEL)
    # Add playlists.
    for p2a in playlists_to_add:
        print("Adding playlist {p2a[0]}, {p2a[1]}")
        download_queue.append({
            'thread': None,
            'request_type': 'sync_add_playlist',
            'playlist_id': p2a[0],
            'playlist_name': p2a[1]
        })
    # Submit downloads for tracks.
    print("Adding tracks to playlist.")
    if len(tracks_to_add) > 0:
        print("Adding track to playlist2.")
        download_thread=threading.Thread(target=utils.download_song_requests,args=[["https://www.youtube.com/watch?v="+t2a.youtube_id_ for t2a in tracks_to_add]])
        download_thread.start()
        download_queue.append({
            'thread': download_thread,
            'request_type': 'sync_add_tracks',
            'tracks': tracks_to_add
        })

    if len(tracks_to_remove) > 0:
        # Remove tracks from DB
        download_queue.append({
            'thread': None,
            'request_type': 'sync_remove_tracks',
            'tracks': tracks_to_remove
        })

                                                                                                                            
def check_download_queue():
    global download_queue
    import sqlite3 as sql
    from dbutils import MusicDB
    db_location=cfg.MUSIC_DB
    conn=sql.connect(db_location)
    db = MusicDB(db_location)
    while True:
        if download_queue:
            complete_threads=[]
            for d in range(len(download_queue)):
                download=download_queue[d]
                if download['request_type'] == 'sr':
                    t=download['thread']
                    if not t.isAlive():
                        current_request_user=download['user']
                        current_request_vid =download['vid']
                        current_request_vidid=download['vidid']
                        current_request_title=download['title']
                        utils.commit_song_request(conn,current_request_user,current_request_vid,current_request_vidid,current_request_title)
                        complete_threads.append(d)
                if download['request_type'] == 'sync_add_playlist':
                    playlist=Playlist(download['playlist_name'],"cockeyedgaming",youtube_id=download['playlist_id'])
                    res,rid=db.add_playlist(playlist)
                    complete_threads.append(d)
                if download['request_type'] == 'sync_add_tracks':
                    t=download['thread']
                    if not t.isAlive():
                        for t2a in download['tracks']:
                            res,track_rid=db.add_track_to_playlist(t2a)
                        complete_threads.append(d)
                if download['request_type'] == 'sync_remove_tracks':
                    for t2r in download['tracks']:
                        playlist = db.get_playlist_by_id(t2r.playlist_id_)
                        db.remove_track_from_playlist(playlist.rid_, t2r)
                        if os.path.exists(t2r.file_location_):
                            os.remove(t2r.file_location_)
                    complete_threads.append(d)
            for t in complete_threads:
                try:
                    del download_queue[t]
                except Exception as e:
                    print(("Unexpected error: {}".format(e)))
                    continue


def main(debug, sync_yt):
    # Networking.
    s=socket.socket()
    s.connect((cfg.TWITCH_HOST, cfg.TWITCH_PORT))
    s.send("PASS {}\r\n".format(cfg.TWITCH_PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(cfg.TWITCH_NICK).encode("utf-8"))
    s.send("JOIN #{}\r\n".format(cfg.TWITCH_CHAN).encode("utf-8"))
    CHAT_MSG=re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
    # to send a chat: utils.chat(s, "Chat message")
    _thread.start_new_thread(utils.threadFillOpList,())
    _thread.start_new_thread(utils.threadFillFollowerList,())
    playlistProc=None
    if sr_enabled:
        _thread.start_new_thread(check_download_queue,())
        playlistProc=icescontroller.PlaylistProcess()
    if sync_yt:
        sync_request()
    # Loads "!" commands.
    commands= utils.command_db.load_commands()
    print(commands)
    # Loads auto-shoutouts.
    shoutouts=utils.command_db.load_shoutouts()
    print(commands)
    while True:
        try:
            response = ""
            if debug:
                response = input(">>>")
            else:
                response = s.recv(1024).decode("utf-8")
            if not debug and response == "PING :tmi.twitch.tv\r\n":
                s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            else:
                username = re.search(r"\w+", response) # Grab first word in message; will be user.
                if username is None:
                    continue
                username = username.group(0)
                message  = CHAT_MSG.sub("", response).strip()
                command = message.split()[0]
                message = " ".join(message.split()[1:])
                if command[0] == "!":
                    command=command[1:]
                    # If the command is a built-in command:
                    if command in base_commands:
                        base_commands[command](s,u=username,m=message,proc=playlistProc)
                    # If the command is DB-defined:
                    elif command in commands:
                        message=message.replace("'",r"\'")
                        print((commands[command].get_fields()))
                        cmd_obj=utils.execute_command(s,username,message,commands[command])
                        # If we're adding a new command or shoutout.
                        if cmd_obj and "command" in cmd_obj:
                            # Add to commands.
                            if cmd_obj["command"][0] == "ADD":
                                print(cmd_obj)
                                commands[cmd_obj['command'][1]['command']]=cmd_obj["command"][1]
                            elif cmd_obj["command"][0] == "REMOVE":
                                del commands[cmd_obj['command'][1]['command']]
                        if cmd_obj and "shoutout" in cmd_obj:
                            # Add to shoutouts.
                            if cmd_obj["shoutout"][0] == "ADD":
                                shoutouts[cmd_obj['shoutout'][1]['so_user'].lower()]=cmd_obj["shoutout"][1]
                            elif cmd_obj["shoutout"][0] == "REMOVE":
                                del shoutouts[cmd_obj['shoutout'][1]['so_user'].lower()]
                if username.lower() in shoutouts:
                    so=shoutouts[username.lower()]
                    if not so['was_seen']:
                        utils.chat(s,username," : ".join([so['chat_text'],so['twitch_clip']]))
                        so['was_seen']=True
        except Exception as e:
            exc_type,exc_obj,exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(("{},{},{},{}".format(e, exc_type, fname, exc_tb.tb_lineno)))
                                            
if __name__ == "__main__":
    debug=False
    sync_yt=False
    if len(sys.argv) > 1:
        if "--no-sr" in sys.argv:
            sr_enabled=False
        if "--initialize-db" in sys.argv:
            utils.command_db.init_db("commands.json")
        if "--channel" in sys.argv:
            assert len(sys.argv) >= sys.argv.index("--channel") + 2
            cfg.TWITCH_CHAN = sys.argv[sys.argv.index("--channel") + 1]
        if "--sync_yt" in sys.argv:
            sync_yt = True
    main(debug, sync_yt)
    
