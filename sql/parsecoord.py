#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import csv

f = open('./coord.csv')
reader =  csv.reader(f, delimiter=',', quotechar='"')

out = open('./geodata.sql', 'w')

for line in reader:
    id = line[0]
    y = float(line[1])
    x = float(line[2])
    name = line[3]
    yy = (y-600000)/1000000
    xx = (x-200000)/1000000

    lonT = (2.6779094
            + 4.728982 * yy 
            + 0.791484 * xx * yy
            + 0.1306 * yy * (xx * xx)
            - 0.0436 * (yy * yy * yy))
    lon = lonT * 100 / 36

    latT = (16.9023892
            + 3.238272 * xx
            - 0.270978 * (yy * yy)
            - 0.002528 * (xx * xx)
            - 0.0447 * (yy * yy) * xx
            - 0.0140 * (xx * xx * xx))
    lat = latT * 100 / 36    

    lat = '%.6f' % lat
    lon = '%.6f' % lon

    out.write('INSERT INTO zvv_station (station_sbbid, station_lat, station_lon, station_name) VALUES (' + id + ', ' + lat + ', ' + lon + ', "' + name + '");\n')

out.close()
    

