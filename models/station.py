#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree
from StringIO import StringIO
import html5lib
from html5lib import treebuilders
import httplib2
from urllib import urlencode, quote, unquote
import web
from datetime import datetime, tzinfo, timedelta, date
from threading import Thread, enumerate
from time import sleep, clock
import time as perf
from geo import Geocode, Util, StationGeoData, StationData
import sys
from models import *

db = web.database(dbn="mysql", db="zvv", user="zvv", pw="m1n3r4lw4ss3r")

class Station:
	def __init__(self, query, time, filters):
		""" Get Information about a station (Departures and Arrivals)"""
		# Setup output vars
		self.stations = None
		self.data = None
		self.xml = u''
		self.xmlinfo = u''
		self.error = None
		self.xmlerror = u''
		
		# Setup privates
		self._time = time
		self._query = query
		self._filters = filters
		self._backendtime = 0
		
		self.location = None
		self.cachekey = query['value'] + query['type'] + str(time)
		
		try:
			self._setup_xmlinfo()
		except Exception:
			self.error = {'message':u'Internal error', 'id':105}
			self._setup_xmlerror()
			return
		
		# Try to get the stations
		try:
			self._setup_stations()
		except Exception:
			raise
			self.error = {'message':u'Malformed input','id':101}
			self._setup_xmlerror()
			return
		
		
		if len(self.stations) == 0:
			self.error = {'message':u'Could not find any Stations','id':102}
			self._setup_xmlerror()
			return
		
		# Try to fetch the data via StationThread
		try:
			self._load_data()
		except Exception:
			raise
			self.error = {'message':u'Error retrieving data', 'id':103}
			self._setup_xmlerror()
			return
		
		
		# Try to setup the xml
		try:
			self._setup_xml()
		except Exception:
			self.error = {'message':u'Internal error', 'id':104}
			self._setup_xmlerror()
			return
		
		if self.xml == '':
			self.error = {'message':u'guru meditation - unexpected error occured', 'id':1099}
			self._setup_xmlerror()
			return
			
	def _setup_stations(self):
		qtype = self._query['type']
		qval = self._query['value']
		
		self.stations = []
		try:
			if qtype == u'addr':
				geo = Geocode(qval)
				self.stations = StationGeoData(geo.latitude, geo.longitude).stations
				self.location = {'latitude':geo.latitude, 'longitude':geo.longitude}
			elif qtype == u'wgs':
				geo = qval.split(',')
				self.stations = StationGeoData(geo[0], geo[1]).stations
				self.location = {'latitude':geo[0], 'longitude':geo[1]}
			elif qtype == u'stat':
				data = {'name':qval, 'id':None, 'zvvid':None}
				stat = StationData(data)
				if stat.data is not None:
					self.stations = [stat.data]
			elif qtype == u'id':
				data = {'name':None, 'id':qval, 'zvvid':qval}
				stat = StationData(data)
				if stat.data is not None:
					self.stations = [stat.data]
		except Exception:
			raise
		
	def _load_data(self):
		t = StationThread(self.stations[0], self._time, self._filters)
		t.start()
		while t.isAlive():
			sleep(0.02)
		
		self.xml = t.xml
		
	def _setup_xml(self):
		pass
		
	def _setup_xmlerror(self):
		root = etree.Element('error')
		n = etree.SubElement(root, 'id')
		n.text = unicode(self.error['id'])
		n = etree.SubElement(root, 'message')
		n.text = self.error['message']
		self.xmlerror = etree.tostring(root, method='xml', encoding='UTF-8')
		
	def _setup_xmlinfo(self):
		root = etree.Element('request')
		n = etree.SubElement(root, 'querytime')
		n.text = datetime.today().strftime("%Y-%m-%d %H:%M:%S%z")
		n = etree.SubElement(root, 'queryvalue')
		n.text = web.url()
		n = etree.SubElement(root, 'cachekey')
		n.text = self.cachekey;
		n = etree.SubElement(root, 'backendtime')
		n.text = '%.2f' % self._backendtime
		n = etree.SubElement(root, 'time')
		n.text = self._time.strftime("%Y-%m-%d %H:%M")
		conc = lambda x: x['type']+ ':' + x['value']
		n = etree.SubElement(root, 'from')
		n.text = conc(self._query)
		n = etree.SubElement(root, 'filters')
		n.text = str(self._filters)
		self.xmlinfo = etree.tostring(root, method='xml', encoding='UTF-8')
		
class StationThread(Thread):
	def __init__(self, station, time, filters, refpos = None):
		super(StationThread, self).__init__()
		self._station = station
		self._time = time
		self._filters = filters
		self._refpos = refpos
		
		self._response = None
		
		self.xml = None
		self.xmldata = None
		self.data = None
		self.error = None
	
	def run(self):
		self._load()
		if self._parse() is False:
			return
			
		self._setup_xml()
		
	def _load(self):
		baseurl = 'http://fahrplan2.fahrplan.zvv.ch/bin/zvv/stboard.exe/dn?L=no_title'
		data = urlencode({'input':self._station['name'].encode('iso-8859-1'),
							'selectDate':'period',
							'dateBegin':self._time.strftime('%d.%m.%y'),
							'dateEnd':self._time.strftime('%d.%m.%y'),
							'time':self._time.strftime('%H:%M'),
							'boardType':'dep',
							'language':'e',
							'GUIREQProduct_0':'on','GUIREQProduct_1':'on','GUIREQProduct_2':'on','GUIREQProduct_3':'on',
							'GUIREQProduct_4':'on','GUIREQProduct_5':'on','GUIREQProduct_6':'on','GUIREQProduct_7':'on',
							'GUIREQProduct_9':'on',
							'start':'yes'})
		
		request = httplib2.Http(".cache")
		resp, self.response = request.request(baseurl, "POST", data)
	
	def _parse(self):
		parser = etree.HTMLParser(encoding="UTF-8")
		tree = etree.parse(StringIO(self.response), parser)
		
		rows = tree.xpath("/html/body/table[1]//table[2]//table[5]//tr[@valign='top']")
		if len(rows) == 0:
			self.error = {'id':111, 'message':'Invalid response from queryserver'}
			return False
			
		self.data = [self._get_entry(row) for row in rows]
		
	
	def _setup_xml(self):
		root = etree.Element('times')
		try:
			for element in self.data:
				tnode = etree.SubElement(root, 'entry')
				web.debug(element)
				s = station_to_node(element['station_eol'], 'station_eol')
				
				tnode.append(s)
				n = etree.SubElement(tnode, 'line')
				n.text = element['line']
				n = etree.SubElement(tnode, 'vehicle')
				n.text = element['vehicle']
				n = etree.SubElement(tnode, 'lineuri')
				n.text = element['lineuri']
		except Exception:
			pass
			
		self.xmldata = root
		self.xml = etree.tostring(self.xmldata, method='xml', encoding='UTF-8')
	
	def _get_entry(self, row):
		cols = row.xpath("td")

		data = {}
		
		# Important Information
		try:
			time = unicode(cols[0].xpath("span/text()")[0].strip())
			vehicle = unicode(vehicle_from_img(cols[2].xpath("a/img/@src")[0].strip()))
			lineuri = unicode(lineuri_from_url(cols[2].xpath("a/@href")[0].strip()))
			line = unicode(normalize_line(cols[4].xpath("span/a/text()")[0].strip()))
			tmp_station = {'name':unicode(cols[6].xpath("span[1]/a/text()")[0].strip()), 'id':unicode(stationid_from_url(cols[6].xpath("span[1]/a/@href")[0].strip()))}
			tmp_station['zvvid'] = None
			station = StationData(tmp_station).data
			
			# departure is part of the station node
			dt = datetime.strptime(self._time.strftime('%Y-%m-%d') + ' ' + time, '%Y-%m-%d %H:%M')
			station['datetime'] = dt
			
			data = {'vehicle':vehicle,
					'lineuri':lineuri,
					'line':line,
					'station_eol':station}	
		except Exception:
			return None
			
		# Stops in between - not very important
		try:
			pass
		except Exception:
			pass	
			
		
		
		# Sometimes, there is a track info available, sometimes, it is not :)
		try:
			track = unicode(cols[8].xpath("text()")[0].strip())
			data['station_eol']['track'] = track
		except Exception:
			pass
			
		return data