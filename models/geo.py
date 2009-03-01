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

class Geocode:
	def __init__(self, address):
		self.address = address
		self.latitude = None
		self.longitude = None
		self._loadKML()
	
	def _loadKML(self):
		baseURL = 'http://maps.google.ch'
		data = urlencode({'q':self.address, 'output':'kml'})
		requestURL = baseURL + '?' + data
		h = httplib2.Http(".cache")
		resp, content = h.request(requestURL, "GET")
		self._parseKML(content)
	
	def _parseKML(self, content):
		tree = etree.parse(StringIO(content))
		self.latitude = tree.xpath("//*[local-name()='latitude']/text()")[0]
		self.longitude = tree.xpath("//*[local-name()='longitude']/text()")[0]
					
class Geostations:
	def __init__(self, latitude, longitude):
		self.stations = None
		