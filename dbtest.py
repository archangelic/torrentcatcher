import sqlite3 as lite
import tabulate

con = lite.connect('/home/cabox/workspace/data/torcatch.db')
cur = con.cursor()
test = raw_input('Enter search query: ')
cur.execute("SELECT * FROM torrents WHERE name LIKE '%{0}%'".format(test))
results = cur.fetchall()
for each in results:
	print each