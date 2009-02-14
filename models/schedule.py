#
#  schedule.py
#  zvvapi
#
#  Created by Marc Ammann on 2/12/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#

try:
  from xml.etree.cElementTree import *
  from xml.etree import cElementTree
except ImportError:
  try:
    from xml.etree.ElementTree import *
  except ImportError:
    from elementtree.ElementTree import *
from StringIO import StringIO
import html5lib
from html5lib import treebuilders
import httplib2
from urllib import urlencode
import web
from datetime import datetime, tzinfo, timedelta
from threading import Thread, enumerate
from time import sleep
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
			requests = self._getMulti(['zurich','st.gallen'], ['bern','genf'], time, filters)
			nodes = [xml for fromStation, toStation, timeStation, filterStation, response, data, xml in requests]
			root = Element('schedules')
			requestNode = SubElement(root, 'request')
			requestTimeNode = SubElement(requestNode, 'time')
			requestTimeNode.text = datetime.today().strftime("%Y-%m-%d %H:%M:%S%z")
			requestValueNode = SubElement(requestNode, 'query')
			requestValueNode.text = web.url()
			requestCacheKeyNode = SubElement(requestNode, 'cachekey')
			requestCacheKeyNode.text = cachekey;
			
			file = reduce(lambda a,b: a+b, nodes)
			return file
			"""memcache.add(cachekey, file.getvalue())"""
	
	def _getMulti(self, fromStations, toStations, time, filters):
		timeout = 2.0
		def alive_count(lst):
			alive = map(lambda x :1 if x.isAlive() else 0, lst)
			return reduce(lambda x,y: x+y, alive)
			
		threads = [URLThread(fromStation, toStation, time, filters) for fromStation in fromStations for toStation in toStations]
		map(lambda x: x.start(), threads)
		
		while alive_count(threads) > 0 and timeout > 0.0:
			timeout = timeout - UPDATE_INTERVAL
			sleep(UPDATE_INTERVAL)
			
		return [ (x.fromStation, x.toStation, x.time, x.filters, x.response, x.data, x.xml) for x in threads ]
	
	
class URLThread(Thread):
	def __init__(self, fromStation, toStation, time, filters):
		super(URLThread, self).__init__()
		self.response = None
		self.fromStation = fromStation
		self.toStation = toStation
		self.time = time
		self.filters = filters
		
		
	def run(self):
		self._loadRawFromURL()
		self._parseRaw()
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
		htmlDoc = StringIO(self.responses)
		all = htmlDoc.readlines()
		htmlDoc = StringIO(''.join(all[1:]))
		
		parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("etree", cElementTree))
		
		root = parser.parse(htmlDoc)
		tree = ElementTree(root)
		file = StringIO()
		tree.write(file)
		
		for target in root.findall("*/link"):
			value = target.attrib.get("href")
		
		self.data = {'v':value}
		
	def _setupXML(self):
		""" Loads parsed data into an XML """
		
		web.debug(fromStation)
		web.debug(toStation)
		web.debug(filters)
		root = Element('schedule')
		
		""" Link Node """
		linkNode = SubElement(root, 'link')
		fromNode = SubElement(linkNode, 'from')
		toNode = SubElement(linkNode, 'to')
		durationNode = SubElement(linkNode, 'duration')
		partsNode = SubElement(linkNode, 'parts')
		""" From Node """
		fromIdNode = SubElement(fromNode, 'id')
		departureNode = SubElement(fromNode, 'time')
		fromNameNode = SubElement(fromNode, 'name')
		fromLocationNode = SubElement(fromNode, 'location')
		fromLatNode = SubElement(fromLocationNode, 'lat')
		fromLonNode = SubElement(fromLocationNode, 'lon')
		fromDistanceNode = SubElement(fromLocationNode, 'distance')
		""" To Node """
		toIdNode = SubElement(toNode, 'id')
		arrivalNode = SubElement(toNode, 'time')
		toNameNode = SubElement(toNode, 'name')
		toLocationNode = SubElement(toNode, 'location')
		toLatNode = SubElement(toLocationNode, 'lat')
		toLonNode = SubElement(toLocationNode, 'lon')
		toDistanceNode = SubElement(toLocationNode, 'distance')
		
		""" Part Node """
		fromPartNode = SubElement(partsNode, 'from')
		toPartNode = SubElement(partsNode, 'to')
		lineNode = SubElement(partsNode, 'line')
		""" From Part Node """
		fromPartIdNode = SubElement(fromPartNode, 'id')
		departurePartNode = SubElement(fromPartNode, 'time')
		fromPartNameNode = SubElement(fromPartNode, 'name')
		fromPartTrackNode = SubElement(fromPartNode, 'track')
		fromPartLocationNode = SubElement(fromPartNode, 'location')
		fromPartLatNode = SubElement(fromPartLocationNode, 'lat')
		fromPartLonNode = SubElement(fromPartLocationNode, 'lon')
		fromPartDistanceNode = SubElement(fromPartLocationNode, 'distance')
		""" To Part Node """
		toPartIdNode = SubElement(toPartNode, 'id')
		arrivalPartNode = SubElement(toPartNode, 'time')
		toPartNameNode = SubElement(toPartNode, 'name')
		toPartTrackNode = SubElement(toPartNode, 'track')
		toPartLocationNode = SubElement(toPartNode, 'location')
		toPartLatNode = SubElement(toPartLocationNode, 'lat')
		toPartLonNode = SubElement(toPartLocationNode, 'lon')
		toPartDistanceNode = SubElement(toPartLocationNode, 'distance')		

		self.xml = root
		