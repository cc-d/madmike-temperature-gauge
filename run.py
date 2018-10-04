import json
#import random
from random import randint, choice
import re
import time
import os
import sqlite3

import smtplib
from email.mime.text import MIMEText

from datetime import datetime
from flask import Flask, render_template, request
app = Flask(__name__)

########### SCRIPT SETTINGS ###########
global db
global table
db, table = '/home/pi/madmike-temperature-gauge/history.db', 'test'
table = 'prod'

global sendto
sendto = 'mdandrea@cosbyharrison.com'
#sendto = 'centralsource@hotmail.com'
#sendto = 'ccarterdev@gmail.com'
global max_high_temp_f
global max_low_temp_f
max_high_temp_f, max_low_temp_f = 41, 32
#######################################

global real_path
real_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + '/'

@app.route('/')
def index():
        try:
                return render_template('index.html')
        except Exception as e:
                return str(e)

def to_f(c):
        return '{:.3f}'.format(c * 9/5 + 32)

# random paded int
def rpi(a=None, b=None, num=False, date=False):
        if not num and a and b:
                i = randint(a,b)
        else:
                i = int(num)
        if len(str(i)) == 1:
                i = '0' + str(i)
        return i

def semail(message='No Message'):
        global sendto

        me, you = 'localhost@localhost', sendto
        msg = MIMEText(message)
        msg['Subject'] = message
        msg['From'] = me
        msg['To'] = sendto

        s = smtplib.SMTP('localhost')
        s.sendmail(me, [you], msg.as_string())
        return True


def current_temperature(testing=False, email_alert=False, show_error=False, rtype='json'):
        if testing:
                rantemp = randint(500,5000)
                raw_device_data = '56 01 4b 46 7f ff 0b 10 d0 : crc=d0 YES\n' \
                                                '55 01 4b 46 7f ff 0a 10 d1 t=' + str(rantemp)
                month, day = rpi(1,12), rpi(1,31)
                if month == 2:
                        day = rpi(1,28)
                elif month == 4 or month == 6 or month == 9 or 11:
                        day = rpi(1,30)
                stime = '%s-%s-%s %s:%s:%s' % (2018, month, day, rpi(0,23), choice(['00',15,30,45]), '00')
        else:
                raw_device_data = os.popen('cat /sys/bus/w1/devices/28-00000a29c2c1/w1_slave').read()
                month, day = rpi(num=int(datetime.now().month)), rpi(num=int(datetime.now().day))
                now = datetime.now()
                stime = '%s-%s-%s %s:%s:%s' % (rpi(num=int(now.year)), rpi(num=int(now.month)), rpi(num=int(now.day)), 
                        rpi(num=int(now.hour)), rpi(num=int(now.minute)), rpi(num=int(now.second)))

        raw_temp = re.findall(r't=-?\d+', raw_device_data)[0][2:]
        negative = ''
        if raw_temp[0] == '-':
                negative = '-'
                raw_temp = raw_temp[1:]
        if len(raw_temp) < 5:
                raw_temp = ((5 - len(raw_temp)) * '0') + raw_temp
        c = float(negative + raw_temp[:2] + '.' + raw_temp[2:])

        error = 'None'
        if not testing:
                global sendto
                global max_high_temp_f
                global max_low_temp_f
                if float(to_f(c)) > float(max_high_temp_f) or float(to_f(c)) < float(max_low_temp_f):
                        error = 'Temperature %s is outside of range!' % to_f(c)
                        if email_alert:
                                se = semail(message=error)
                                print(se)
                        global real_path
                        print(real_path)
                        with open(real_path + 'error.log', 'a+') as e:
                                print('%s | %s\n' % (time.time(), error))
                                e.write('%s | %s\n' % (time.time(), error))

        r = {'f':to_f(c), 'c':c, 'time':stime}

        if show_error:
                r['error'] = error

        if rtype == 'json':
                return json.dumps(r)
        elif rtype == 'dict':
                return r
        return True

def poll_temp(testing=False, email_alert=True, show_error=True):
        ct = current_temperature(testing=testing, email_alert=email_alert, rtype='dict')
        print(ct)
        insert_data(ct['c'], ct['f'], ct['time'])
        return True

def insert_data(c, f, time):
        conn = sqlite3.connect(db)
        cc = conn.cursor()
        sql = 'INSERT INTO %s (f, c, time) VALUES (%s, %s, "%s");' % (table, f, c, time)
        cc.execute(sql)
        conn.commit()
        conn.close()
        return True

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
        conn.close()
        json_data = []
        for record in data:
                json_data.append({'f':record[0], 'c':record[1], 'time':record[2]})
        return json.dumps(json_data)

@app.route('/api/current_temperature', methods=['GET'])
def get_current_temperature():
        return current_temperature(testing=False, rtype='json')

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
