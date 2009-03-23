#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import csv
import sys

filename = sys.argv[1]
creator = sys.argv[2]

convlon = lambda xx, yy: (2.6779094 + 4.728982 * yy + 0.791484 * xx * yy + 0.1306 * yy * (xx * xx) - 0.0436 * (yy * yy * yy)) * 100 / 36
convlat = lambda xx, yy: (16.9023892 + 3.238272 * xx - 0.270978 * (yy * yy) - 0.002528 * (xx * xx) - 0.0447 * (yy * yy) * xx - 0.0140 * (xx * xx * xx)) * 100 / 36

if (creator == 'sbb'):
	f = open(filename)
	reader =  csv.reader(f, delimiter=',', quotechar='"')

	out = open('./geodata-sbb.sql', 'w')

	for line in reader:
		id = line[0]
		y = float(line[1])
		x = float(line[2])
		name = line[3]
		yy = (y-600000)/1000000
		xx = (x-200000)/1000000
	
		lon = convlon(xx, yy)
		lat = convlat(xx, yy)

		lat = '%.6f' % lat
		lon = '%.6f' % lon

		out.write('INSERT INTO zvv_station (station_sbbid, station_lat, station_lon, station_name) VALUES (' + id + ', ' + lat + ', ' + lon + ', "' + name + '");\n')

	out.close()
elif (creator == 'zvv'):
	f = open(filename)
	reader =  csv.reader(f, delimiter=',', quotechar='"')

	out = open('./geodata-zvv.sql', 'w')

	for line in reader:
		try:
			zvvid = line[0]
			sbbid = line[2]
			y = float(line[3])
			x = float(line[4])
		except ValueError:
			continue
			
		if sbbid == 0:
			continue
			
		name = line[1]
		yy = (y-600000)/1000000
		xx = (x-200000)/1000000
	
		lon = convlon(xx, yy)
		lat = convlat(xx, yy)

		lat = '%.6f' % lat
		lon = '%.6f' % lon

		out.write('INSERT INTO zvv_station (station_zvvid, station_sbbid, station_lat, station_lon, station_name) VALUES (' + zvvid + ',' + sbbid + ', ' + lat + ', ' + lon + ', "' + name + '");\n')

	out.close()