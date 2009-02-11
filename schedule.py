#
#  schedule.py
#  zvvapi
#
#  Created by Marc Ammann on 2/11/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#

from google.appengine.ext import webapp
from StringIO import StringIO

try:
  from xml.etree.cElementTree import *
except ImportError:
  try:
    from xml.etree.ElementTree import *
  except ImportError:
    from elementtree.ElementTree import *

class Schedule(webapp.RequestHandler):
	def get(self):		
		self.response.headers['Content-Type'] = 'text/xml'
		root = Element('schedule')
		""" Create Request Node """
		requestNode = SubElement(root, 'request')
		requestTimeNode = SubElement(requestNode, 'time')
		requestValueNode = SubElement(requestNode, 'query')
		requestCacheNode = SubElement(requestNode, 'cachehits')
		
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
		
		
		file = StringIO()
		tree = ElementTree(root)
		tree.write(file)
		
		
		self.response.out.write('<?xml version="1.0"?>' + file.getvalue())