import sqlite3
import os
import os.path
import sys
import crunkybot.twitch.config as cfg

from crunkybot.twitch.dbutils import CommandDB, Command


def adjust_commands(conn, cur):
    # u"chat(%s,'Check us out on Twitter for stream updates.')")
    command_db = CommandDB(cfg.ConfigLoader[cfg.COMMAND_DB_LOCATION])
    commands=command_db.load_commands()
    for k, c in commands.items():
        if c['action'][:4] == "chat":
            new_command = Command((c['command'],c['command_type'],c['permission'],c['num_args'],c['arguments'],c['action']))
            new_command.set_id(c['rid'])
            insert_pos = new_command['action'].find("%s")+3
            new_action = new_command['action'][:insert_pos]+"%u,"+new_command['action'][insert_pos:]
            command_db.open()
            cur = command_db.connection.cursor()
            cur.execute('''UPDATE commands SET action=? WHERE command=?''', (new_action,c['command']))
    command_db.connection.commit()
    command_db.close()


def cleanse_db(conn, cur):
    rows=cur.execute('''SELECT * FROM tracks''')
    rows_to_remove=[]
    for row in rows:
        if row[4] != "NULL":
            print(row)
            title=row[3]
            filename=row[4]
            print("Keep", title, "(", filename, ")? (added by", row[5], ")")
            response = input(">>> (y/n/x)?")
            if response == "n":
                rows_to_remove.append([x for x in row])
            elif response == "x":
                break
    for row in rows_to_remove:
        print("Removing", row[2], row[3])
        cur.execute('''DELETE FROM tracks WHERE id=?''', (row[0],))
        conn.commit()
        if os.path.isfile(row[3]):
            os.remove(row[3])


def cleanse_dir(conn, cur, dl_location):
    for filename in os.listdir(dl_location):
        if filename.endswith(".mp3"):
            file_location = os.path.join(dl_location,filename)
            cur.execute('''SELECT * FROM tracks WHERE file_location=?''',(file_location,))
            rows = cur.fetchall()
            if rows:
                print(rows[0][3], "(", rows[0][4], file_location, ")")
            if not rows:
                print(file_location, "not found in db. Removing.")
                os.remove(file_location)


if __name__ == "__main__":
    config = cfg.ConfigLoader(sys.argv[1])
    conn = sqlite3.connect(cfg.MUSIC_DB_LOCATION)
    cur = conn.cursor()
    if sys.argv[2] == "cleanse":
        cleanse_db(conn, cur)
    elif sys.argv[2] == "cleanfiles":
        cleanse_dir(conn, cur, cfg.MUSIC_DOWNLOAD_DIR)
    else:
        print("Incorrect arguments.")
