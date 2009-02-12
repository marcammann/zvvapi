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
from google.appengine.api import memcache
import html5lib
from html5lib import treebuilders

import urllib

class Schedule:
	def loadXML(self, fromP, toP, time, filters):
		cachekey = str(fromP['value']) + str(fromP['type']) + str(toP['value']) + str(toP['type'])\
					+ str(time['value']) + str(time['type']) + str(filters['changetime']) + \
					str(filters['suppresslong']) + str(filters['groups']) + \
					str(filters['bicycles']) + str(filters['flat']) + str(filters['changes'])
		data = memcache.get(cachekey)
		stats = memcache.get_stats()
		
		if data is not None:
			return self._loadScheduleRemote(fromP, toP, time, filters)
			return data
		else:
			root = Element('schedule')
			""" Create Request Node """
			requestNode = SubElement(root, 'request')
			requestTimeNode = SubElement(requestNode, 'time')
			requestValueNode = SubElement(requestNode, 'query')
			requestCacheKeyNode = SubElement(requestNode, 'cachekey')
			requestCacheKeyNode.text = cachekey;
			"""requestCacheNode = SubElement(requestNode, 'cachehits') """
			"""requestCacheNode.text = "%s" % stats['hits'] """
			
			""" Link Node """
			linkNode = SubElement(root, 'link')
			linkNode.text = str(filters)
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
			
			
			file = StringIO()
			tree = ElementTree(root)
			tree.write(file)
			
			memcache.add(cachekey, file.getvalue())
			
			return file.getvalue()
			
	def _loadScheduleRemote(self, fromP, toP, time, filters):
		baseurl = 'http://fahrplan2.fahrplan.zvv.ch/bin/zvv/query.exe/dn?L=no_title'
		""" Gone params:
			'start_search':'yes','start':1,'protocol':'http:','mylanguage':'d','servername':'fahrplan.zvv.ch','fromIsZSG':'no','toIsZSG':'no',
											'wDazExt0':'Mo|Di|Mi|Do|Fr|Sa|So',
			"""
		data = urllib.urlencode({'usr':'www.zvv.ch','frames':'no','start.x':79,'start.y':9,'lg':'d','queryPageDisplayed':'yes',\
								'gis1':'Haltestelle','REQ0JourneyStopsS0A':1, 'REQ0JourneyStopsS0G':'zurich hb',\
								'gis2':'Haltestelle', 'REQ0JourneyStopsZ0A':1, 'REQ0JourneyStopsZ0G':'Bern',\
								'REQ0JourneyDate':'Do, 12.02.09', 'REQ0JourneyTime':'03:30',\
								'REQ0HafasSearchForw':1})
		f = urllib.urlopen(baseurl, data)
		all = f.readlines()
		htmlDoc = StringIO(''.join(all[1:]))
		parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))

		tree = ElementTree().parse(parser.parse(htmlDoc).toxml('UTF-8'))
		file = StringIO()
		tree.write(file)
		
		return file.getvalue()
		
		
		