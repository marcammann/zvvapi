#!/usr/bin/python
# -*- coding: utf-8 -*-

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
from datetime import datetime, tzinfo, timedelta, date
from threading import Thread, enumerate
from time import sleep
from geo import Geocode, Util, Geostation
import sys
import re

UPDATE_INTERVAL = 0.01
MAX_THREADS = 16

db = web.database(dbn="mysql", db="zvv", user="zvv", pw="m1n3r4lw4ss3r")

class Schedule:
	def __init__(self):
		self.threads = None
		self.currentThread = None
		self.blackslist = []

	def loadXML(self, fromP, toP, time, filters):
		cachekey = fromP['value'] + str(fromP['type']) + toP['value'] + str(toP['type'])\
					+ str(time['value']) + str(time['type']) + str(filters['changetime']) + \
					str(filters['suppresslong']) + str(filters['groups']) + \
					str(filters['bicycles']) + str(filters['flat']) + str(filters['changes'])
		
		"""data = memcache.get(cachekey)"""
		data = None
		if data is not None:
			return data
		else:
			if fromP['type'] == 'addr':
				geo = Geocode(fromP['value'])
				fromS = Geostation(geo.latitude, geo.longitude).getStations()
				fromPos = (geo.latitude, geo.longitude)
			elif fromP['type'] == 'wgs':
				s = Geostation(fromP['value'].split(',')[0], fromP['value'].split(',')[1])
				fromS = s.getStations()
				fromPos = (fromP['value'].split(',')[0], fromP['value'].split(',')[1])
			else:
				fromS = [fromP['value']]
				fromPos = None
				
			if toP['type'] == 'addr':
				geo = Geocode(toP['value'])
				toS = Geostation(geo.latitude, geo.longitude).getStations()
				toPos = (geo.latitude, geo.longitude)
			elif toP['type'] == 'wgs':
				s = Geostation(toP['value'].split(',')[0], toP['value'].split(',')[1])
				toS = s.getStations()
				toPos = (toP['value'].split(',')[0], toP['value'].split(',')[1])
			else:
				toS = [toP['value']]
				toPos = None
			
			try:
				fromPos = {'latitude':float(fromPos[0]), 'longitude':float(fromPos[1])}
				toPos = {'latitude':float(toPos[0]), 'longitude':float(toPos[1])}
			except TypeError:
				fromPos = None
				toPost = None
			
			if len(toS) > 2 and len(fromS) > 2:
				toS = toS[:4]
				fromS = fromS[:4]
				
			web.debug(fromS)
			web.debug(toS)
			
			refpos = toPos and fromPos or toPos
			#web.debug(refpos)
			requests = self._getMulti(fromS, toS, time, filters, refpos)
			dups = 0
			nodes = []
			passed = []
			self.blacklist = [] #stations who change their name and produce dups
			for fromStation, toStation, timeStation, filterStation, response, data, xml, parsedFrom, parsedTo in requests:
				try:
					i = passed.index((parsedFrom, parsedTo))
					if parsedFrom != fromStation:
						self.blacklist.append(fromStation)
					if parsedTo != toStation:
						self.blacklist.append(toStation)
					dups += 1
				except ValueError:
					passed.append((parsedFrom, parsedTo))
					nodes.append(xml)
			
			# For later use
			"""if dups is not 0:
				i = 0
				while i < dups:
					request = self._getNext()
					if request:
						fromStation, toStation, timeStation, filterStation, response, data, xml, parsedFrom, parsedTo = request
						web.debug(self.blacklist)
						web.debug(passed)
						web.debug(parsedFrom)
						web.debug(parsedTo)
						try:
							k = passed.index((parsedFrom, parsedTo))
						except ValueError:
							i += 1
							passed.append((parsedFrom, parsedTo))
							nodes.append(xml)
					else:
						break"""
			
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
			conc = lambda x: x['type']+ ':' + x['value']
			node = etree.SubElement(requestNode, 'from')
			node.text = conc(fromP)
			node = etree.SubElement(requestNode, 'to')
			node.text = conc(toP)
			node = etree.SubElement(requestNode, 'filters')
			node.text = str(filters)
			
			for node in nodes:
				if node is not None:
					elementNode = root.append(node)
			
			return etree.tostring(root, method='xml', encoding="UTF-8")
			
			"""memcache.add(cachekey, file.getvalue())"""
	
	def _getMulti(self, fromStations, toStations, time, filters, refpos = None):
		timeout = 15.0
		def alive_count(lst):
			alive = map(lambda x:1 if x.isAlive() else 0, lst)
			return reduce(lambda x,y: x+y, alive)
			
		self.threads = [StationURLThread(fromStation, toStation, time, filters, refpos) for toStation in toStations for fromStation in fromStations]
		threads = self.threads[:6]
		#web.debug([thread.toStation for thread in threads])
		map(lambda x: x.start(), threads)
		self.currentThread = MAX_THREADS
		
		while alive_count(threads) > 0 and timeout > 0.0:
			timeout = timeout - UPDATE_INTERVAL
			sleep(UPDATE_INTERVAL)
			
		return [ (x.fromStation, x.toStation, x.time, x.filters, x.response, x.data, x.xml, x.parsedFromStation, x.parsedToStation) for x in threads ]
	
	def _getNext(self):
		if len(self.threads) > self.currentThread + 1:
			timeout = 3
			thread = self.threads[self.currentThread+1]
			
			try:
				self.blacklist.index(thread.fromStation)
				self.blacklist.index(thread.toStation)
				return False
			except ValueError:
				thread.start()
				
			while thread.isAlive() and timeout > 0.0:
				timeout = timeout - UPDATE_INTERVAL
				sleep(UPDATE_INTERVAL)
			
			self.currentThread += 1
			return (thread.fromStation, thread.toStation, thread.time, thread.filters, thread.response, thread.data, thread.xml, thread.parsedFromStation, thread.parsedToStation)
		else:
			return False
	
class StationURLThread(Thread):
	def __init__(self, fromStation, toStation, time, filters, refpos = None):
		super(StationURLThread, self).__init__()
		self.response = None
		self.fromStation = fromStation
		self.toStation = toStation
		self.parsedFromStation = None
		self.parsedToStation = None
		self.time = time
		self.filters = filters
		self.data = None
		self.xml = None
		self.refpos = refpos
		#web.debug(self.refpos)
		
	def run(self):
		self._setupXML()
	
	def _loadRawFromURL(self):
		isdep = lambda time:time['type'] == 'dep' and 1 or 0
		changetime = int(self.filters['changetime'])
		changetimeURL = (changetime < 5 and '0:1') or (changetime < 10 and '5:2') or (changetime < 15 and '10:3') or (changetime < 20 and '15:4') or (changetime < 30 and '20:5') or (changetime >= 30 and '30:6')
		bicycles = int(self.filters['bicycles'])
		bicyclesURL = bicycles and 1 or 0
		suppresslong = int(self.filters['suppresslong'])
		suppresslongURL = suppresslong and 1 or 0
		groups = int(self.filters['groups'])
		groupsURL = groups and 1 or 0
		changes = self.filters['changes'] == None and 1000 or int(self.filters['changes'])
		changesURL = (changes == None and '1000:1') or (changes == 0 and '0:2') or (changes == 1 and '1:3') or (changes == 2 and '2:4') or (changes == 3 and '3:5') or (changes == 4 and '4:5') or (changes > 4 and '1000:1')
		
		baseurl = 'http://fahrplan2.fahrplan.zvv.ch/bin/zvv/query.exe/dn?L=no_title'
		data = urlencode({'usr':'www.zvv.ch','frames':'no','start.x':79,'start.y':9,'lg':'d','queryPageDisplayed':'yes','REQ0HafasNumCons0':'5:5'.encode('iso-8859-1'),\
								'REQ0HafasChangeTime':changetimeURL.encode('iso-8859-1'), 'REQ0HafasAttrExc.1':bicyclesURL, 'REQ0HafasSkipLongChanges':suppresslongURL,\
								'REQ0HafasAttrExc.2':groupsURL, 'REQ0HafasNoOfChanges':changesURL.encode('iso-8859-1'),\
								'gis1':'Haltestelle','REQ0JourneyStopsS0A':1, 'REQ0JourneyStopsS0G':self.fromStation.encode('iso-8859-1'),\
								'gis2':'Haltestelle', 'REQ0JourneyStopsZ0A':1, 'REQ0JourneyStopsZ0G':self.toStation.encode('iso-8859-1'),\
								'REQ0JourneyDate':self.time['value'].strftime('%d.%m.%y'), 'REQ0JourneyTime':self.time['value'].strftime('%H:%M'),\
								'REQ0HafasSearchForw':isdep(self.time)})
		
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
		
		rows = self.data.xpath("/html/body//table[7]//tr[th/@class='resultdark']")
		if rows:
			links = [self._parseLink(row.xpath("following-sibling::tr[td/@class='result']")) for row in rows]	
		else:
			return None
		
		for link in links:
			fromL = link['parts'][0]['from']
			toL = link['parts'][len(link['parts'])-1]['to']
			""" Link Node """
			linkNode = etree.SubElement(root, 'link')
			fromNode = etree.SubElement(linkNode, 'from')
			toNode = etree.SubElement(linkNode, 'to')
			durationNode = etree.SubElement(linkNode, 'duration')
			if link['from']['datetime'] and link['to']['datetime']:
				durationNode.text = str(self._getDuration(link['from'], link['to']))
			partsNode = etree.SubElement(linkNode, 'parts')
			""" From Node """
			fromIdNode = etree.SubElement(fromNode, 'id')
			fromIdNode.text = str(fromL['id'])
			departureNode = etree.SubElement(fromNode, 'datetime')
			if link['from']['datetime']:
				departureNode.text = str(datetime.strftime(link['from']['datetime'], '%Y-%m-%d %H:%M%z'))
			else:
				departureNode.text = 'None'
			fromNameNode = etree.SubElement(fromNode, 'name')
			fromNameNode.text = fromL['name']
			self.parsedFromStation = fromL['name']
			if fromL['location'] is not None:
				if self.refpos is None:
					self.refpos = fromL['location']
					
				fromLocationNode = etree.SubElement(fromNode, 'location')
				fromLatNode = etree.SubElement(fromLocationNode, 'lat')
				fromLatNode.text = str(fromL['location']['latitude'])
				fromLonNode = etree.SubElement(fromLocationNode, 'lon')
				fromLonNode.text = str(fromL['location']['longitude'])
				fromDistanceNode = etree.SubElement(fromLocationNode, 'distance')
				fromDistanceNode.text = str(Util().distance(fromL['location'], toL['location']))
				if self.refpos is not None:
					fromDistanceNode.text = str(Util().distance(self.refpos, fromL['location']))
					
			""" To Node """
			toIdNode = etree.SubElement(toNode, 'id')
			toIdNode.text = str(toL['id'])
			arrivalNode = etree.SubElement(toNode, 'datetime')
			if link['to']['datetime']:
				arrivalNode.text = str(datetime.strftime(toL['datetime'], '%Y-%m-%d %H:%M%z'))
			else:
				arrivalNode.text = 'None'
			toNameNode = etree.SubElement(toNode, 'name')
			toNameNode.text = toL['name']
			self.parsedToStation = toL['name']
			if toL['location'] is not None:
				toLocationNode = etree.SubElement(toNode, 'location')
				toLatNode = etree.SubElement(toLocationNode, 'lat')
				toLatNode.text = str(toL['location']['latitude'])
				toLonNode = etree.SubElement(toLocationNode, 'lon')
				toLonNode.text = str(toL['location']['longitude'])
				toDistanceNode = etree.SubElement(toLocationNode, 'distance')
				if self.refpos is not None:
					toDistanceNode.text = str(Util().distance(self.refpos, toL['location']))
			
			if self.filters['flat'] is False:
				for part in link['parts']:
					""" Part Node """
					partNode = etree.SubElement(partsNode, 'part')
					fromPartNode = etree.SubElement(partNode, 'from')
					toPartNode = etree.SubElement(partNode, 'to')
					lineNode = etree.SubElement(partNode, 'line')
					lineNode.text = part['line']
					vehicleNode = etree.SubElement(partNode, 'vehicle')
					vehicleNode.text = part['vehicle']
					durationNode = etree.SubElement(partNode, 'duration')
					if part['to']['datetime'] and part['from']['datetime']:
						durationNode.text = str(self._getDuration(part['from'], part['to']))
					""" From Part Node """
					fromPartIdNode = etree.SubElement(fromPartNode, 'id')
					fromPartIdNode.text = str(part['from']['id'])
					departurePartNode = etree.SubElement(fromPartNode, 'datetime')
					if part['from']['datetime']:
						departurePartNode.text = str(datetime.strftime(part['from']['datetime'], '%Y-%m-%d %H:%M%z'))
					else:
						departurePartNode.text = str(None)
					fromPartNameNode = etree.SubElement(fromPartNode, 'name')
					fromPartNameNode.text = part['from']['name']
					fromPartTrackNode = etree.SubElement(fromPartNode, 'track')
					fromPartTrackNode.text = str(part['from']['track'])
					if part['from']['location'] is not None:
						fromPartLocationNode = etree.SubElement(fromPartNode, 'location')
						fromPartLatNode = etree.SubElement(fromPartLocationNode, 'lat')
						fromPartLatNode.text = str(part['from']['location']['latitude'])
						fromPartLonNode = etree.SubElement(fromPartLocationNode, 'lon')
						fromPartLonNode.text = str(part['from']['location']['longitude'])
						fromPartDistanceNode = etree.SubElement(fromPartLocationNode, 'distance')
						if self.refpos is not None:
							fromPartDistanceNode.text = str(Util().distance(self.refpos, part['from']['location']))
					""" To Part Node """
					toPartIdNode = etree.SubElement(toPartNode, 'id')
					toPartIdNode.text = str(part['to']['id'])
					arrivalPartNode = etree.SubElement(toPartNode, 'datetime')
					if part['to']['datetime']:
						arrivalPartNode.text = str(datetime.strftime(part['to']['datetime'], '%Y-%m-%d %H:%M%z'))
					else:
						arrivalPartNode.text = str(None)
					toPartNameNode = etree.SubElement(toPartNode, 'name')
					toPartNameNode.text = part['to']['name']
					toPartTrackNode = etree.SubElement(toPartNode, 'track')
					toPartTrackNode.text = str(part['to']['track'])
					if part['to']['location'] is not None:
						toPartLocationNode = etree.SubElement(toPartNode, 'location')
						toPartLatNode = etree.SubElement(toPartLocationNode, 'lat')
						toPartLatNode.text = str(part['to']['location']['latitude'])
						toPartLonNode = etree.SubElement(toPartLocationNode, 'lon')
						toPartLonNode.text = str(part['to']['location']['longitude'])
						toPartDistanceNode = etree.SubElement(toPartLocationNode, 'distance')
						if self.refpos is not None:
							toPartDistanceNode.text = str(Util().distance(self.refpos, part['to']['location']))


		self.xml = root
		
	def _parseLink(self, nodes):
		partrows = []
		parts = []
		for row in nodes:
			if row.xpath("td[@colspan=12]/table"):
				if len(parts):
					parseDate = parts[len(parts)-1]['lastDate']
				else:
					parseDate = None
				
				parts.append(self._parsePart(partrows, parseDate))
				partrows = []
			elif row.xpath("td/img"):
				break
			else:
				partrows.append(row)


		### Screw those walkings
		k = 0
		for part in parts:
			if part['vehicle'] == u'FOOT':
				if k > 0:
					part['from']['datetime'] = parts[k-1]['to']['datetime']
				if k < len(parts) - 1:
					part['to']['datetime'] = parts[k+1]['from']['datetime']
			k += 1
				
		
		
		### Get the frst and the last times of the journey
		i = 0
		while parts[i]['from']['datetime'] is None:
			i+=1
			
		j = len(parts)-1
		while parts[j]['to']['datetime'] is None:
			j-=1
		
		link = {'from':{}, 'to':{}, 'parts':[]}
		if len(parts) >= i:
			link['from']['datetime'] = parts[i]['from']['datetime']
		else:
			link['from']['datetime'] = None
		
		if j >= 0:
			link['to']['datetime'] = parts[j]['to']['datetime']
		else:
			link['to']['datetime'] = None
			
		link['parts'] = parts

		
		return link
			
	def _parsePart(self, nodes, lastDate):
		def us(e):
			try:
				return unicode(e[0]).strip()
			except IndexError:
				if len(e) is 0:
					return ''
				return unicode(e).strip()
				
	
		part = {'from':{}, 'to':{}}
		
		part['from']['name'] = us(nodes[0].xpath("td[1]/a[1]/text()"))
		part['to']['name'] = us(nodes[1].xpath("td[1]/a[1]/text()"))
		
		def _getID(node):
			la = us(node.xpath("td[1]/a[1]/@href"))
			lb = us(node.xpath("td[1]/a[2]/@href"))
			if re.search(r'input=(\d+)', la) is not None:
				return str(int(re.search(r'input=(\d+)', la).group(1)))
			else:
				return str(int(re.search(r'hst=(\d+)', lb).group(1)))
		
		part['from']['id'] = _getID(nodes[0])
		part['to']['id'] = _getID(nodes[1])
		
		def locationForStation(station):
			res = db.query('SELECT station_sbbid, station_lat, station_lon FROM zvv_station WHERE station_name = $name OR station_sbbid = $id', {'name' : station['name'], 'id' : station['id']})
			if len(res):
				row = res[0]
				location = {'latitude':row['station_lat'], 'longitude':row['station_lon']}
				return location
			else:
				return None
		
		part['from']['location'] = locationForStation(part['from'])
		part['to']['location'] = locationForStation(part['to'])
	
		def _getDate(nodeIndex):
			try:
				tDate = datetime.strptime(us(nodes[nodeIndex].xpath("td[3]/text()")), '%d.%m.%y')
			except ValueError:
				if lastDate is not None:
					tDate = lastDate
				else:
					tDate = datetime.now()
			return tDate
		
		part['from']['date'] = _getDate(0)
		lastDate = part['from']['date']
		part['to']['date'] = _getDate(1)
		lastDate = part['to']['date']
		part['lastDate'] = lastDate
	
		part['vehicle'] = re.search('/img/(.*)_pic.gif', us(nodes[0].xpath("td[10]/table/tr/td[1]/img/@src"))).group(1).upper()
		if part['vehicle'] != u'FUSS' and part['vehicle'] != u'TRANSFER':
			# distinguish between by foot or by transit
			part['line'] = us(nodes[0].xpath("td[10]/table/tr/td[2]/a/text()"))
			

			
			part['from']['datetime'] = datetime.strptime(part['from']['date'].strftime('%Y-%m-%d ') + us(nodes[0].xpath("td[6]/text()")), '%Y-%m-%d %H:%M')
			part['to']['datetime'] = datetime.strptime(part['to']['date'].strftime('%Y-%m-%d ') + us(nodes[1].xpath("td[5]/text()")), '%Y-%m-%d %H:%M')
			
			part['from']['track'] = us(nodes[0].xpath("td[8]/text()"))
			part['to']['track'] = us(nodes[1].xpath("td[6]/text()"))
		else:
			part['line'] = ''
			part['from']['datetime'] = None
			part['to']['datetime'] = None
			part['from']['track'] = ''
			part['to']['track'] = ''
			part['vehicle'] = u'FOOT'
		
		return part
		
	def _getDuration(self, fromP, toP):
		arr = toP['datetime']
		dep = fromP['datetime']
		
		timedelta = arr - dep
		return timedelta