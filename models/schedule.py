#
#  schedule.py
#  zvvapi
#
#  Created by Marc Ammann on 2/12/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#

from lxml import etree
from StringIO import StringIO
import html5lib
from html5lib import treebuilders
import httplib2
from urllib import urlencode, quote, unquote
import web
from datetime import datetime, tzinfo, timedelta
from threading import Thread, enumerate
from time import sleep
from geo import Geocode
import sys

UPDATE_INTERVAL = 0.01

class Schedule:
	def loadXML(self, fromP, toP, time, filters):
		cachekey = str(fromP['value']) + str(fromP['type']) + str(toP['value']) + str(toP['type'])\
					+ str(time['value']) + str(time['type']) + str(filters['changetime']) + \
					str(filters['suppresslong']) + str(filters['groups']) + \
					str(filters['bicycles']) + str(filters['flat']) + str(filters['changes'])
					
		"""data = memcache.get(cachekey)"""
		data = None
		if data is not None:
			return data
		else:
			if fromP['type'] == 'addr':
				geo = Geocode('schweighofstrasse 418, 8055 zurich')

			requests = self._getMulti(['zurich'], ['bern'], time, filters)
			nodes = [xml for fromStation, toStation, timeStation, filterStation, response, data, xml in requests]
			root = etree.Element('schedules')
			requestNode = etree.SubElement(root, 'request')
			requestTimeNode = etree.SubElement(requestNode, 'querytime')
			requestTimeNode.text = datetime.today().strftime("%Y-%m-%d %H:%M:%S%z")
			requestValueNode = etree.SubElement(requestNode, 'queryvalue')
			requestValueNode.text = web.url()
			requestCacheKeyNode = etree.SubElement(requestNode, 'cachekey')
			requestCacheKeyNode.text = cachekey;
			
			node = etree.SubElement(requestNode, 'time')
			node.text = time['value'].strftime("%Y-%m-%d %H:%M")
			conc = lambda x: x['type'] + ':' + x['value']
			node = etree.SubElement(requestNode, 'from')
			node.text = conc(fromP)
			node = etree.SubElement(requestNode, 'to')
			node.text = conc(toP)
			node = etree.SubElement(requestNode, 'filters')
			node.text = str(filters)
			
			for node in nodes:
				if node:
					elementNode = root.append(node)
			
			return etree.tostring(root, method='xml', encoding="UTF-8")
			"""memcache.add(cachekey, file.getvalue())"""
	
	def _getMulti(self, fromStations, toStations, time, filters):
		timeout = 10.0
		def alive_count(lst):
			alive = map(lambda x:1 if x.isAlive() else 0, lst)
			return reduce(lambda x,y: x+y, alive)
			
		threads = [StationURLThread(fromStation, toStation, time, filters) for fromStation in fromStations for toStation in toStations]
		map(lambda x: x.start(), threads)
		
		while alive_count(threads) > 0 and timeout > 0.0:
			timeout = timeout - UPDATE_INTERVAL
			sleep(UPDATE_INTERVAL)
			
		return [ (x.fromStation, x.toStation, x.time, x.filters, x.response, x.data, x.xml) for x in threads ]
	
	
class StationURLThread(Thread):
	def __init__(self, fromStation, toStation, time, filters):
		super(StationURLThread, self).__init__()
		self.response = None
		self.fromStation = fromStation
		self.toStation = toStation
		self.time = time
		self.filters = filters
		self.data = None
		self.xml = None
		
	def run(self):
		self._setupXML()
	
	def _loadRawFromURL(self):
		baseurl = 'http://fahrplan2.fahrplan.zvv.ch/bin/zvv/query.exe/dn?L=no_title'
		data = urlencode({'usr':'www.zvv.ch','frames':'no','start.x':79,'start.y':9,'lg':'d','queryPageDisplayed':'yes',\
								'gis1':'Haltestelle','REQ0JourneyStopsS0A':1, 'REQ0JourneyStopsS0G':'zurich hb',\
								'gis2':'Haltestelle', 'REQ0JourneyStopsZ0A':1, 'REQ0JourneyStopsZ0G':'Bern',\
								'REQ0JourneyDate':'Do, 12.02.09', 'REQ0JourneyTime':'03:30',\
								'REQ0HafasSearchForw':1})
		
		self.request = httplib2.Http(".cache")
		resp, content = self.request.request(baseurl, "POST", data)

		self.response = content
		self.responseHeaders = resp
	
	def _checkQueryError(self):
		return False
	
	def _parseRaw(self):
		self._loadRawFromURL()
		
		parser = etree.HTMLParser(encoding="UTF-8")
		tree = etree.parse(StringIO(self.response), parser)
		self.data = tree
		
	def _setupXML(self):
		self._parseRaw()
		""" Loads parsed data into an XML """
		root = etree.Element('schedule')
		
		rows = self.data.xpath("//html/body//table[7]//tr[th]/following-sibling::tr")

		parts = []
		data = []
		for row in rows:
			n = etree.SubElement(root, 'link')
			if (row.xpath("./th") and data is not []):
				parts.append(self._parseLink(data))
				data = []
			else:
				data.append(row)
		parts.append(self._parseLink(data))
			
			
		""" Link Node """
		linkNode = etree.SubElement(root, 'link')
		fromNode = etree.SubElement(linkNode, 'from')
		toNode = etree.SubElement(linkNode, 'to')
		durationNode = etree.SubElement(linkNode, 'duration')
		partsNode = etree.SubElement(linkNode, 'parts')
		""" From Node """
		fromIdNode = etree.SubElement(fromNode, 'id')
		departureNode = etree.SubElement(fromNode, 'time')
		fromNameNode = etree.SubElement(fromNode, 'name')
		fromLocationNode = etree.SubElement(fromNode, 'location')
		fromLatNode = etree.SubElement(fromLocationNode, 'lat')
		fromLonNode = etree.SubElement(fromLocationNode, 'lon')
		fromDistanceNode = etree.SubElement(fromLocationNode, 'distance')
		""" To Node """
		toIdNode = etree.SubElement(toNode, 'id')
		arrivalNode = etree.SubElement(toNode, 'time')
		toNameNode = etree.SubElement(toNode, 'name')
		toLocationNode = etree.SubElement(toNode, 'location')
		toLatNode = etree.SubElement(toLocationNode, 'lat')
		toLonNode = etree.SubElement(toLocationNode, 'lon')
		toDistanceNode = etree.SubElement(toLocationNode, 'distance')
		
		for part in parts:
			""" Part Node """
			fromPartNode = etree.SubElement(partsNode, 'from')
			toPartNode = etree.SubElement(partsNode, 'to')
			lineNode = etree.SubElement(partsNode, 'line')
			lineNode.text = part['line']
			""" From Part Node """
			fromPartIdNode = etree.SubElement(fromPartNode, 'id')
			departurePartNode = etree.SubElement(fromPartNode, 'time')
			fromPartNameNode = etree.SubElement(fromPartNode, 'name')
			fromPartNameNode.text = part['fromName']
			fromPartTrackNode = etree.SubElement(fromPartNode, 'track')
			fromPartLocationNode = etree.SubElement(fromPartNode, 'location')
			fromPartLatNode = etree.SubElement(fromPartLocationNode, 'lat')
			fromPartLonNode = etree.SubElement(fromPartLocationNode, 'lon')
			fromPartDistanceNode = etree.SubElement(fromPartLocationNode, 'distance')
			""" To Part Node """
			toPartIdNode = etree.SubElement(toPartNode, 'id')
			arrivalPartNode = etree.SubElement(toPartNode, 'time')
			toPartNameNode = etree.SubElement(toPartNode, 'name')
			toPartNameNode.text = part['toName']
			toPartTrackNode = etree.SubElement(toPartNode, 'track')
			toPartLocationNode = etree.SubElement(toPartNode, 'location')
			toPartLatNode = etree.SubElement(toPartLocationNode, 'lat')
			toPartLonNode = etree.SubElement(toPartLocationNode, 'lon')
			toPartDistanceNode = etree.SubElement(toPartLocationNode, 'distance')		

		self.xml = root
		
	def _parseLink(self, nodes):
		partRows = []
		parts = []
		for node in nodes:
			if (node.xpath("./td/text()[substring(.,1,5) = 'Dauer']")):
				web.debug("end")
				return parts
			elif (False):
				""" this should be the check for the hr line """
				partRows.append(node)
			else:
				parts.append(self._parsePart(partRows))
				partRows = []
			
	def _parsePart(self, nodes):
		part['from'] = nodes[0].xpath("./td[0]/a/text()")
		part['to'] = nodes[1].xpath("./td[0]/a/text()")
		
		
			
			
			