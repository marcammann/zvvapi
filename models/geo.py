#!/usr/bin/python
# -*- coding: utf-8 -*-


#
#  geo.py
#  zvvapi
#
#  Created by Marc Ammann on 2/15/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#
from lxml import etree
from StringIO import StringIO
import httplib2
from urllib import urlencode
import web
import math

db = web.database(dbn="mysql", db="zvv", user="zvv", pw="m1n3r4lw4ss3r")

class Util:
	def distance(self, source, destination):
		try:
			source_lat = math.radians(float(source['latitude']))
			source_lon = math.radians(float(source['longitude']))
			destination_lat = math.radians(float(destination['latitude']))
			destination_lon = math.radians(float(destination['longitude']))
		except IndexError:
			return None
		
		R = 6367.45
		dLat = destination_lat - source_lat
		dLon = destination_lon - source_lon
		a = math.pow(math.sin(dLat/2), 2) + math.cos(source_lat) * math.cos(destination_lat) * math.pow(math.sin(dLon/2), 2)
		c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
		d = '%.1f' % (R * c * 1000)
		return d
		
class Geocode:
	def __init__(self, address):
		self.address = address
		self.latitude = None
		self.longitude = None
		self._load_KML()
	
	def _load_KML(self):
		base_URL = 'http://maps.google.ch'
		data = urlencode({'q':self.address.encode('utf-8'), 'output':'kml', 'ie':'UTF8', 'oe':'UTF8'})
		request_URL = base_URL + '?' + data
		h = httplib2.Http()
		resp, content = h.request(request_URL, "GET")
		self._parse_KML(content)
	
	def _parse_KML(self, content):
		tree = etree.parse(StringIO(content))
		try:
			self.latitude = tree.xpath("//*[local-name()='latitude']/text()")[0]
			self.longitude = tree.xpath("//*[local-name()='longitude']/text()")[0]
		except IndexError:
			return
					
class Geostation:
	def __init__(self, latitude, longitude):
		self.stations = None
		self._load_stations(latitude, longitude)
	
	def _load_stations(self, latitude, longitude):
		query = 'SELECT *, 6367.45 * 2 * ASIN(SQRT(  POWER(SIN(($latitude - dest.station_lat) * pi()/180 / 2), 2) + COS($latitude * pi()/180) *  COS(dest.station_lat * pi()/180) * POWER(SIN(($longitude - dest.station_lon) * pi()/180 / 2), 2)  )) as distance \
				FROM zvv_station dest ORDER BY distance LIMIT 20'
		res = db.query(query, {'latitude':latitude, 'longitude':longitude})
		if (len(res)):
			self.stations = [row['station_name'] for row in res]
			return
		else:
			self.stations = None
			return
	
	def get_stations(self):
		return self.stations
		
