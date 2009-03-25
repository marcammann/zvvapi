#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  schedule.py
#  zvvapi
#
#  Created by Marc Ammann on 2/11/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#
import web

from datetime import datetime, tzinfo, timedelta
from urllib import unquote

from models import schedule,geo,station

import logging
LOG_FILENAME = '/tmp/logging_example.out'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)

import cProfile

class GMT1(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=1)
	def dst(self, dt):
		return timedelta(0)
	def tzname(self,dt):
		return "Europe/Zurich"

type = lambda t: t is u'' and 'stat' or t.split(':')[0]
toarray = lambda v, t: {'value':v, 'type':unicode(t)}
timetype = lambda t: t is u'' and 'dep' or t.split(':')[0]
def requesttime(time):
	try:
		res = datetime.strptime(datetime.now(tz=GMT1()).strftime("%Y-%m-%d") + time, '%Y-%m-%d %H:%M')
	except ValueError:
		try:
			res = datetime.strptime(time, '%d.%m.%Y %H:%M')
		except ValueError:
			try:
				res = datetime.strptime(time, '%Y-%m-%d %H:%M')
			except ValueError:
				res = datetime.now(tz=GMT1())
	return res

def profile():
	# A really slow request:
	time_type = 'dep'
	time_value = requesttime('2009-04-01 09:14')
	#source_type = 'addr'
	#source_value = u'Badenerstrasse 363, 8003, Zrich'
	#destination_type = 'addr'
	#destination_value = u'Schweighofstrasse 418, 8055 Zrich'
	source_type = 'addr'
	source_value = u'Zürich, Schaufelbergerstrasse'
	destination_type = 'stat'
	destination_value = u'Zürich, Thurgauerstrasse 4'	
	filters = {'changetime':0, 'changes':None, 'suppresslong':False, 'groups':False, 'bicycles':False, 'flat':False, 'apikey':None}
	source = toarray(source_value, source_type)
	destination = toarray(destination_value, destination_type)
	time = toarray(time_value, time_type)
	
	s = schedule.Schedule()
	xml = s.load_XML(source, destination, time, filters)	
	web.debug(xml)

class Schedule:
	def GET(self, source_type, source_value, destination_type, destination_value, time_type, time_value):
		# Sanitize From/To/Types
		source_type = type(source_type)
		destination_type = type(destination_type)
		
		try:
			dest = destination_value.encode('iso-8859-1')
			destination_value = unicode(dest, 'utf-8')
			src = source_value.encode('iso-8859-1')
			source_value = unicode(src, 'utf-8')
		except UnicodeDecodeError:
			pass

		source = toarray(unicode(unquote(source_value)), source_type)
		destination = toarray(unicode(unquote(destination_value)), destination_type)
		
		# Sanitize Date/Time
		time_type = timetype(time_type)
		time_value = requesttime(unquote(time_value))
		time = toarray(time_value, time_type)
		
		filters = web.input(changetime=0, changes=None, suppresslong=False,\
							groups=False, bicycles=False, flat=False, apikey=None)
						
		s = schedule.Schedule()
		xml = s.load_XML(source, destination, time, filters)
		
		web.header('Content-Type', 'text/xml')
		return '<?xml version="1.0"?><schedules>' + xml + '</schedules>'

class Station:
	def GET(self, pos_type, pos_value, time_value):
		# Sanitize From/Time
		pos_type = type(pos_type)
		
		try:
			pos_value = unicode(pos_value.encode('iso-8859-1'), 'utf-8')
		except UnicodeDecodeError:
			pass
			
		pos = toarray(unquote(pos_value), pos_type)
		
		time_value = requesttime(unquote(time_value))
		filters = web.input(apikey=None)
		
		s = station.Station(pos, time_value, filters)
		xml = u''
		if s.error:
			xml = s.xmlerror
		else:
			xml = s.xml
		
		web.header('Content-Type', 'text/xml')
		return '<?xml version="1.0"?><station>'+ s.xmlinfo + xml + '</station>'
		
