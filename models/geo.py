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
	def distance(self, fromP, toP):
		latFrom = math.radians(fromP['latitude'])
		lonFrom = math.radians(fromP['longitude'])
		latTo = math.radians(toP['latitude'])
		lonTo = math.radians(toP['longitude'])
		R = 6367.45
		dLat = latTo - latFrom
		dLon = lonTo - lonFrom
		a = math.pow(math.sin(dLat/2), 2) + math.cos(latFrom) * math.cos(latTo) * math.pow(math.sin(dLon/2), 2)
		c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
		d = '%.1f' % (R * c * 1000)
		return d
		
class Geocode:
	def __init__(self, address):
		self.address = address
		self.latitude = None
		self.longitude = None
		self._loadKML()
	
	def _loadKML(self):
		baseURL = 'http://maps.google.ch'
		data = urlencode({'q':self.address.encode('utf-8'), 'output':'kml'})
		requestURL = baseURL + '?' + data
		h = httplib2.Http(".cache")
		resp, content = h.request(requestURL, "GET")
		self._parseKML(content)
	
	def _parseKML(self, content):
		tree = etree.parse(StringIO(content))
		try:
			self.latitude = tree.xpath("//*[local-name()='latitude']/text()")[0]
			self.longitude = tree.xpath("//*[local-name()='longitude']/text()")[0]
		except IndexError:
			return
					
class Geostation:
	def __init__(self, latitude, longitude):
		self.stations = None
		self._loadStations(latitude, longitude)
	
	def _loadStations(self, latitude, longitude):
		query = 'SELECT *, 6367.45 * 2 * ASIN(SQRT(  POWER(SIN(($latitude - dest.station_lat) * pi()/180 / 2), 2) + COS($latitude * pi()/180) *  COS(dest.station_lat * pi()/180) * POWER(SIN(($longitude - dest.station_lon) * pi()/180 / 2), 2)  )) as distance \
				FROM zvv_station dest ORDER BY distance LIMIT 6'
		res = db.query(query, {'latitude':latitude, 'longitude':longitude})
		if (len(res)):
			self.stations = [row['station_name'] for row in res]
			return
		else:
			self.stations = None
			return
	
	def getStations(self):
		return self.stations
			
		
		
		