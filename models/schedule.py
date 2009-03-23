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
		self.journeys = []
		self.refpos = None
		

	def load_XML(self, source, destination, time, filters):
		cachekey = source['value'] + str(source['type']) + destination['value'] + str(destination['type'])\
					+ str(time['value']) + str(time['type']) + str(filters['changetime']) + \
					str(filters['suppresslong']) + str(filters['groups']) + \
					str(filters['bicycles']) + str(filters['flat']) + str(filters['changes'])
		# data = memcache.get(cachekey)
		data = None
		if data is not None:
			return data
		else:
			try:
				source_container = self.get_stations(source)
				self.refpos = source_container['position']
				destination_container = self.get_stations(destination)
				source_stations = source_container['stations']
				destination_stations = destination_container['stations']
			except Exception:
				raise
				return None
			
			max_range = len(source_stations) > len(destination_stations) and len(source_stations) or len(destination_stations)
			
			web.debug(source_stations)
			web.debug(destination_stations)
			

			
			""" combinate journeys in a nice way """
			min = lambda a,b: a if a < b else b
			journeys = []
			for i in range(0, max_range):
				min_dest_range = min(i, len(destination_stations))
				min_src_range = min(i, len(source_stations)-1)
				
				if	i < len(source_stations) and min_dest_range > 0:
					for j in range(0, min_dest_range):
						journeys.append({'source': source_stations[i], 'destination': destination_stations[j]})
				if i < len(destination_stations):
					for k in range(0, min_src_range+1):
						journeys.append({'source': source_stations[k], 'destination': destination_stations[i]})
			
			timeout = 20.0
			def alive_count(lst):
				alive = map(lambda x:1 if x.isAlive() else 0, lst)
				return reduce(lambda x,y: x+y, alive)
			
			initial_thread_count = 8
			threads = [StationURLThread(j['source'], j['destination'], time, filters, self.refpos) for j in journeys]
			map(lambda x: x.start(), threads[:initial_thread_count])
			
			def is_duplicate(thread, completed_threads):
				for t in completed_threads:
					if t.parsedFromStation == thread.parsedFromStation and t.parsedToStation == thread.parsedToStation:
						web.debug(t.parsedFromStation + ':' + thread.parsedFromStation)
						return True
					else:
						continue
				return False
			
			web.debug(alive_count(threads))
			
			ct = initial_thread_count
			result_threads = []
			worker_threads = threads
			while alive_count(worker_threads) > 0 and timeout > 0:
				timeout -= UPDATE_INTERVAL
				for t in worker_threads:
					if t.isAlive() is False and t.xml is None and t.did_run is True:
						worker_threads.remove(t)
						if ct < len(threads):
							threads[ct].start()
							timeout += 10
							web.debug('spawning thread because of empty xml')
							ct += 1
					elif t.isAlive() is False and t.xml is not None and is_duplicate(t, result_threads) is True:
						worker_threads.remove(t)
						if ct < len(threads):
							threads[ct].start()
							timeout += 10
							web.debug('spawning thread because of duplicateness')
							ct += 1
					elif t.isAlive() is False and t.xml is not None and is_duplicate(t, result_threads) is False:
						worker_threads.remove(t)
						result_threads.append(t)
				sleep(UPDATE_INTERVAL)
			
			for t in threads:
				if t.isAlive() is  False and t.xml is not None and is_duplicate(t, result_threads) is False:
					result_threads.append(t)
			
			nodes = [t.xml for t in result_threads]
			
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
			node.text = conc(source)
			node = etree.SubElement(requestNode, 'to')
			node.text = conc(destination)
			node = etree.SubElement(requestNode, 'filters')
			node.text = str(filters)
			
			for node in nodes:
				if node is not None:
					elementNode = root.append(node)
			
			return etree.tostring(root, method='xml', encoding="UTF-8")
			"""memcache.add(cachekey, file.getvalue())"""
	
	def get_stations(self, pos):
		try:
			stations = None
			position = None
			if pos['type'] == u'addr':
				geo = Geocode(pos['value'])
				stations = Geostation(geo.latitude, geo.longitude).get_stations()
				position = {'latitude':geo.latitude, 'longitude':geo.longitude}
			elif pos['type'] == u'wgs':
				geo = pos['value'].split(',')
				stations = Geostation(geo[0], geo[1]).get_stations()
				position = {'latitude':geo[0], 'longitude':geo[1]}
			elif pos['type'] == u'stat':
				stations = [pos['value']]
				position = None
			else:
				raise Exception
				
			return {'stations': stations, 'position': position}
		except Exception:
			raise
	
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
		self.did_run = False
		#web.debug(self.refpos)
		web.debug(Util().distance(self.refpos, {'latitude': '47.267923', 'longitude': '8.502808'}))
		
	def run(self):
		self.did_run = True
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
		data = urlencode({'usr':'www.zvv.ch','frames':'no','start.x':79,'start.y':9,'lg':'d','language':'e','queryPageDisplayed':'yes','REQ0HafasNumCons0':'5:5'.encode('iso-8859-1'),\
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
					notesNode = etree.SubElement(partNode, 'notes')
					notesNode.text = part['notes']
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
			part['line'] = u'Walk'
			part['vehicle'] = u'FOOT'
	
		part['notes'] = us(nodes[0].xpath("td[12]/text()"))
		
	
		return part
		
	def _getDuration(self, fromP, toP):
		arr = toP['datetime']
		dep = fromP['datetime']
		
		timedelta = arr - dep
		return timedelta
