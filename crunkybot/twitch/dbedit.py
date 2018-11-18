import sqlite3
import os
import os.path
import sys
import crunkycfg as cfg
from dbutils import *
conn=sqlite3.connect(cfg.MUSIC_DB)
cur=conn.cursor()

def adjust_commands():
    # u"chat(%s,'Check us out on Twitter for stream updates.')")
    command_db = CommandDB(cfg.DB_PATH)
    commands=command_db.load_commands()
    for k,c in commands.iteritems():
        if c['action'][:4] == "chat":
            new_command=Command([c['command'],c['command_type'],c['permission'],c['num_args'],c['arguments'],c['action']])
            new_command.set_id(c['rid'])
            insert_pos=new_command['action'].find("%s")+3
            print insert_pos
            new_action=new_command['action'][:insert_pos]+"%u,"+new_command['action'][insert_pos:]
            command_db.open()
            cur=command_db.connection_.cursor()
            cur.execute('''UPDATE commands SET action=? WHERE command=?''', (new_action,c['command']))
    command_db.connection_.commit()
    command_db.close()

def cleanse_db():
    rows=cur.execute('''SELECT * FROM tracks''')
    rows_to_remove=[]
    for row in rows:
        if row[4] != "NULL":
            print row
            title=row[3]
            filename=row[4]
            print "Keep",title,"(",filename,")? (added by",row[5],")"
            response=raw_input(">>> (y/n/x)?")
            if response == "n":
                rows_to_remove.append([x for x in row])
            elif response == "x":
                break
    for row in rows_to_remove:
        print "Removing",row[2],row[3]
        cur.execute('''DELETE FROM tracks WHERE id=?''', (row[0],))
        conn.commit()
        if os.path.isfile(row[3]):
            os.remove(row[3])
                
def cleanse_dir(dl_location):
    for filename in os.listdir(dl_location):
        if filename.endswith(".mp3"):
            file_location=os.path.join(dl_location,filename)
            cur.execute('''SELECT * FROM tracks WHERE file_location=?''',(file_location,))
            rows=cur.fetchall()
            if rows:
                print rows[0][3],"(",rows[0][4],file_location,")"
            if not rows:
                print file_location,"not found in db. Removing."
                os.remove(file_location)
            
if __name__=="__main__":
    if sys.argv[1] == "cleanse":
        cleanse_db()
    elif sys.argv[1] == "cleanfiles":
        cleanse_dir(cfg.MUSIC_DOWNLOAD_DIR)
    else:
        print "Incorrect arguments."
            
        
