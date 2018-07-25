import json
#import random
from random import randint
import re
import time
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request
app = Flask(__name__)

global db
global table
db, table = 'history.db', 'test'

@app.route('/')
def index():
	try:
		return render_template('index.html')
	except Exception as e:
		return str(e)

def to_f(c):
	return '{:.3f}'.format(c * 9/5 + 32)

# random paded int
def rpi(a, b, date=False):
	i = randint(a,b)
	if len(str(i)) == 1:
		i = '0' + str(i)
	return i

def current_temperature(testing=False, rtype='json'):
	if testing:
		rantemp = randint(1001,9999)
		raw_device_data = '56 01 4b 46 7f ff 0b 10 d0 : crc=d0 YES\n' \
						'55 01 4b 46 7f ff 0a 10 d1 t=2' + str(rantemp)
		raw_temp = re.findall(r't=\d+', raw_device_data)[0][2:]
		c = float(raw_temp[:2] + '.' + raw_temp[2:])
		month, day = rpi(1,12), rpi(1,31)
		if month == 2:
			day = rpi(1,28)
		elif month == 4 or month == 6 or month == 9 or 11:
			day = rpi(1,30)
		time = '%s-%s-%s %s:%s:%s' % (rpi(2017,2018), month, day, rpi(0,23), rpi(0,59), rpi(0,59))
	else:
		time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		return False
	if rtype == 'json':
		return json.dumps({'f':to_f(c), 'c':c, 'time':time})
	elif rtype == 'dict':
		return {'f':to_f(c), 'c':c, 'time':time}

def insert_data(c, f, time):
	conn = sqlite3.connect(db)
	cc = conn.cursor()
	sql = 'INSERT INTO %s (f, c, time) VALUES (%s, %s, "%s");' % (table, f, c, time)
	cc.execute(sql)
	conn.commit()
	conn.close()

@app.route('/api/temperature_history', methods=['GET'])
def get_temperature_history():
	conn = sqlite3.connect(db)
	cc = conn.cursor()
	try:
		time2 = request.args.get('time1')
		time1 = request.args.get('time2')
		if len(time1) < 3 or len(time2) < 3:
			raise Exception
		time1 = str(time1)[:-3]
		time2 = str(time2)[:-3]
		time1 = datetime.fromtimestamp(int(time1)).strftime('%Y-%m-%d %H:%M:%S');
		time2 = datetime.fromtimestamp(int(time2)).strftime('%Y-%m-%d %H:%M:%S');
		time1, time2 = str(time1), str(time2)
	except:
		pass
	if time1 and time2:
		sql = 'SELECT * FROM %s WHERE time BETWEEN "%s" AND "%s"' % (table, time1, time2)
	else:
		sql = 'SELECT * FROM %s;' % (table);
	cc.execute(sql)
	conn.commit()
	data = cc.fetchall()
	#return data
	conn.close()
	json_data = []
	for record in data:
		json_data.append({'f':record[0], 'c':record[1], 'time':record[2]})
	return json.dumps(json_data)

@app.route('/api/current_temperature', methods=['GET'])
def get_current_temperature():
	return current_temperature(testing=True, rtype='json')

@app.route('/api/get_high_low', methods=['GET'])
def get_high_low():
	conn = sqlite3.connect(db)
	cc = conn.cursor()
	time1 = (time.time() - (60 * 60 * 24))
	time2 = time.time()
	time1 = datetime.fromtimestamp(int(time1)).strftime('%Y-%m-%d %H:%M:%S');
	time2 = datetime.fromtimestamp(int(time2)).strftime('%Y-%m-%d %H:%M:%S');
	sql = 'SELECT * FROM %s WHERE time BETWEEN "%s" AND "%s" ORDER BY "f" ASC' % (table, time1, time2)
	cc.execute(sql)
	conn.commit()
	data = cc.fetchall()
	conn.close()

	json_data = []
	record = data[0]
	json_data.append({'f':record[0], 'c':record[1], 'time':record[2], 'type':'low'})

	record = data[len(data) - 1]
	json_data.append({'f':record[0], 'c':record[1], 'time':record[2], 'type':'high'})	
	return json.dumps(json_data);

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
	#for i in range(5000):
		#ct = current_temperature(testing=True, rtype='dict')
		#print(ct)
		#insert_data(ct['c'], ct['f'], ct['time'])
