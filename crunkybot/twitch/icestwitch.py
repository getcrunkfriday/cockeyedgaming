import sqlite3
import unicodedata
from random import shuffle

#global playlist,requests,current_track
#global db,con,cur
db="/home/andrew/dbs/crunky.db"
con=sqlite3.connect(db)
cur=con.cursor()
tplaylist=[]
trequests=[]
tplaylist_id=0
tcurrent_track=""
tuser_added=""

def ices_init():
    global cur
    global con
    cur.execute('''CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS playlist_requests (id INTEGER PRIMARY KEY, playlist_id INTEGER)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS playlist (id INTEGER PRIMARY KEY, playlist_id INTEGER, youtube_id TEXT, title TEXT, file_location TEXT, user_added TEXT, date_added TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY, playlist_name TEXT, user_added TEXT)''')
    con.commit()
    cur.execute('''SELECT * FROM playlist''')
    rows=cur.fetchall()
    tplaylist=[(row[2],row[3]) for row in rows]
    shuffle(tplaylist)
    #for t in tplaylist:
    #    print t
    return 1

def ices_get_metadata():
    global tcurrent_track
    str_curr_track=None
    try:
        str_curr_track=str(tcurrent_track)
    except:
        try:
            str_curr_track=unicodedata.normalize('NFKD', tcurrent_track).encode('ascii','ignore')
        except:
            str_curr_track=None
    with open("current_track.txt","w") as f:
        f.write(str_curr_track)
    return str_curr_track

def ices_shutdown():
    #global db,con,cur
    cur.execute('''DROP TABLE requests''')
    con.commit()
    return 1

def ices_get_next():
    global tplaylist
    global trequests
    global tcurrent_track
    # Check playlist requests.
    cur.execute('''SELECT  * FROM playlist_requests''')
    row=cur.fetchone()
    if row:
        playlist_id=row[1]
        cur.execute('''DELETE FROM playlist_requests WHERE playlist_id=?''', (playlist_id,))
        con.commit()
        cur.execute('''SELECT * FROM playlist WHERE playlist_id=?''', (playlist_id,))
        pl_rows=cur.fetchall()
        tplaylist=[(row[3],row[4]) for r in pl_rows]
        shuffle(tplaylist)
        tplaylist_id=playlist_id
    # Check request table.
    cur.execute('''SELECT * FROM requests''')
    rows=cur.fetchall()
    next_track = None
    # If there are any requests:
    if rows:
        for row in rows:
            # Removes the current request from the DB.
            cur.execute('''DELETE FROM requests WHERE id=?''', (row[0],))
            new_tuple=tuple([x for x in row[1:]]+[0])
            print new_tuple
            con.commit()
            trequests.append((row[2],row[3],row[4]))
    # If I have a request, make that the next track...
    if trequests:
        track=trequests.pop(0)
        tcurrent_track=track[0]+","+track[2]
        next_track = track[1]
    # Otherwise, pick from the playlist.
    elif tplaylist:
        track=tplaylist.pop()
        tcurrent_track=track[0]+",cockeyedgaming"
        next_track = track[1]
    # If the playlist is empty and there are no requests,
    # Shuffle the playlist.
    else:
        print "Reshuffling playlist."
        cur.execute('''SELECT * FROM playlist WHERE playlist_id=?''',(tplaylist_id,))
        rows=cur.fetchall()
        tplaylist=[(row[3],row[4]) for row in rows]
        shuffle(tplaylist)
        track=tplaylist.pop()
        tcurrent_track=track[0]+",cockeyedgaming"
        next_track = track[1]
    try:
        return str(next_track)
    except:
        track=tplaylist.pop()
        tcurrent_track=track[0]+",cockeyedgaming"
        next_track=track[1]
        return str(next_track)
