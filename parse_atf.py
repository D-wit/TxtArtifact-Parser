import os
import sys
import csv
import json
import datetime
import filetime
import sqlite3

conn = sqlite3.connect('parsed_atf.db')
c = conn.cursor()

index = [1, 1, 1, 1] #app,app_fc,setupapi,mru

#parse INSTALL_*_*.txt
def appcompat(file_path):
    log_line = None
    parsed_line = [0,0,0,0,'','','']
    with open(file_path, 'r', encoding='ISO-8859-1') as log_file:
        log_line = None
        line_count = 0
        while True:
            log_line = log_file.readline()
            log_line = log_line.replace('\x00','').replace('\x0d\x0a','').replace('\n','')
            line_count += 1

            log_line = log_line.split('=')

            if log_line[0] == '':
                log_line = log_file.readline()
                log_line = log_line.replace('\x00','').replace('\x0d\x0a','').replace('\n','')
                line_count += 1
                log_line = log_line.split('=')
                if log_line[0] == '': break
                else: pass
                
            parsed_line[0] = index[0]

            if log_line[0] == 'StartTime':
                log_time = log_line[1]
                section_stime = (log_time.split(' '))
                stime_date = section_stime[0].split('/')
                stime_time = section_stime[1].split(':')
                dt = datetime.datetime(int(stime_date[2]), int(stime_date[0]), int(stime_date[1]), int(stime_time[0]), int(stime_time[1]), int(stime_time[2]))
                parsed_line[2] = dt.timestamp() + 32400

            if log_line[0] == 'Name':
                parsed_line[3] = log_line[1]

            if log_line[0] == 'Path':
                parsed_line[4] = log_line[1]

            if log_line[0] == 'Id':
                parsed_line[1] = log_line[1]
            
            if log_line[0] == 'CompanyName':
                parsed_line[5] = log_line[1]
            
            if log_line[0] == 'FileCreate':
                fc_tuple = (index[1], parsed_line[1],log_line[1])
                c.execute("INSERT INTO app_filecreate VALUES(?,?,?)",fc_tuple)
                index[1] += 1

            else:
                if log_line[0] == 'MsiDetected':
                    parsed_line[6] = log_line[1]
                    c.execute("INSERT INTO appcompat VALUES(?,?,?,?,?,?,?)",tuple(parsed_line))
                    index[0] += 1
 

#parse setupapi.dev.log and setupapi.dev.*.log
def setupapi(file_path):
    is_usbstor = 0
    log_line = None
    parsed_line = [0,0,0,'','','']
    with open(file_path, 'r') as log_file:
        log_line = None
        while log_line != '':
            log_line = log_file.readline()
            if '>>>' in log_line and 'USBSTOR' in log_line:
                is_usbstor = 1
                parsed_line[0] = index[2]
                log_line = log_line[6:-2]
                log_line = log_line.split('-')
                parsed_line[2] = log_line[0]
                split_line = log_line[1].split('&')
                parsed_line[3] = split_line[1]
                parsed_line[4] = split_line[2]
                
                log_line = log_file.readline()

                section_stime = (log_line.split())[3:]
                stime_date = section_stime[0].split('/')
                stime_time = section_stime[1].split(':')
                stime_ms = stime_time[2].split('.')
                dt = datetime.datetime(int(stime_date[0]), int(stime_date[1]), int(stime_date[2]), int(stime_time[0]), int(stime_time[1]), int(stime_ms[0]))#, int(stime_ms[1]))
                parsed_line[1] = dt.timestamp() + 32400

            if is_usbstor == 1 and 'GUID' in log_line:
                log_line = log_line.split()
                parsed_line[5] = (log_line[-1])[1:-2]
            
            if  is_usbstor == 1 and 'Exit status' in log_line:
                c.execute("INSERT INTO setupapi VALUES(?,?,?,?,?,?)",tuple(parsed_line))
                index[2] += 1
                is_usbstor = 0
            
#parse Search MRU
def mru(file_path):
    with open(file_path, 'r', encoding='utf-8') as appcache:
        parsed_line = [0,0,'','','',0,'','']
        log_data = json.load(appcache)
        json_index = 0
        while json_index < len(log_data):
            parsed_line[0] = index[3]

            parsed_filetime = int(log_data[json_index]['System.DateAccessed']['Value'])
            if parsed_filetime == 0: parsed_line[1] = 0
            else:
                parsed_epochtime = filetime.to_datetime(parsed_filetime).timestamp()
                parsed_line[1] = int(parsed_epochtime)

            parsed_line[2] = log_data[json_index]['System.ItemNameDisplay']['Value']
            parsed_line[3] = log_data[json_index]['System.FileExtension']['Value']
            parsed_line[4] = log_data[json_index]['System.Software.ProductVersion']['Value']
            parsed_line[5] = log_data[json_index]['System.Software.TimesUsed']['Value']
            parsed_line[6] = log_data[json_index]['System.ItemType']['Value']
            parsed_line[7] = log_data[json_index]['System.Tile.EncodedTargetPath']['Value']

            c.execute("INSERT INTO mru VALUES(?,?,?,?,?,?,?,?)",tuple(parsed_line))
            index[3] += 1
            json_index += 1


with open(sys.argv[1], 'r', newline='') as atf_list:
    atf_info = csv.reader(atf_list, delimiter = ',')
    c.execute("DELETE FROM appcompat")
    c.execute("DELETE FROM setupapi")
    c.execute("DELETE FROM mru")
    c.execute("DELETE FROM app_filecreate")
    for line in atf_info:
        if "\\" in line[1]:
            if 'appcompat' in line[1]:
                appcompat("D:\\[kapedest]\\C"+(line[1])[2:])
            elif 'setupapi' in line[1]:
                setupapi("D:\\[kapedest]\\C"+(line[1])[2:])
            elif 'Search' in line[1]:
                mru("D:\\[kapedest]\\C"+(line[1])[2:])
            else:
                print("임마는 뭐고\n")
                print('appcompat' in line[1])

conn.commit()