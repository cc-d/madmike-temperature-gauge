GLOBAL VARIABLES
===================
All values are found at the top of run.py


db, table = '/home/pi/madmike-temperature-gauge/history.db', 'test'

db = Exact path to your sqlite3 db file


table = Name of table to use, I've already created a table called 'prod' with the correct schema, change from
'test' to 'prod' whenever you are ready to start recording ONLY real data.


sendto = 'ccarterdev@gmail.com'

sendto = The email address to warning emails to.


max\_high\_temp\_f, max\_low\_temp\_f = 50, 32

The desired temperature range, anything more or less will send emails to the sendto address.


HOW TO RUN
==============
1. Start Flask Webserver "python3 run.py"

2. Add an entry to crontab for "python3 poll.py" every x interval (suggested 15 minutes). poll.py inserts the live data into the database.
