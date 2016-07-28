import sqlite3 as lite


def start(database):
    con = lite.connect(database)
    cur = con.cursor()
    currentVersion = "3.2.1"
    try:
        cur.execute('SELECT b FROM info WHERE a="version"')
        version = cur.fetchall()[0][0]
    except:
        cur.execute(
            'CREATE TABLE IF NOT EXISTS info(a,b)'
        )
        cur.execute('INSERT INTO info(a,b) VALUES ("version", "1.0.0")')
        con.commit()
        version = "1.0.0"
    if version == "1.0.0":
        print "Database needs to be updated"
        cur.execute('SELECT * FROM feeds')
        feeds = cur.fetchall()
        cur.execute("CREATE TABLE IF NOT EXISTS hold(name, url, tag)")
        con.commit()
        for each in feeds:
            x, name, url = each
            print name + " at " + url
            tag = raw_input("RSS tag: ")
            tag = tag.lower()
            if tag == "":
                tag = "link"
            cur.execute('INSERT INTO hold(name, url, tag) VALUES (?,?,?)',
                        (name, url, tag))
        con.commit()
        cur.execute('DROP TABLE feeds')
        cur.execute((
            'CREATE TABLE IF NOT EXISTS feeds(id INTEGER PRIMARY KEY, '
            'name TEXT, url TEXT, tag TEXT);'
        ))
        cur.execute('SELECT * FROM hold')
        hold = cur.fetchall()
        for each in hold:
            name, url, tag = each
            cur.execute(
                'INSERT INTO feeds(name, url, tag) VALUES(?,?,?)',
                (name, url, tag)
            )
        con.commit()
        cur.execute('DROP TABLE hold')
        cur.execute('UPDATE info SET b=? WHERE a="version"', (currentVersion,))
        con.commit()
    elif version == currentVersion:
        print "Database already up to date"
    else:
        cur.execute('UPDATE info SET b=? WHERE a="version"', (currentVersion,))
        con.commit()
