#
#  schedule.py
#  zvvapi
#
#  Created by Marc Ammann on 2/11/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#

from datetime import datetime, tzinfo, timedelta
from urllib import unquote

from models import schedule

class GMT1(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=1)
	def dst(self, dt):
		return timedelta(0)
	def tzname(self,dt):
		return "Europe/Zurich"


from google.appengine.ext import webapp

class Schedule(webapp.RequestHandler):
	def get(self, fromType, fromURL, toType, toURL, timeType, timeURL):
		""" Sanitize From/To/Types """
		typeD = lambda t: t is '' and 'stat' or t.split('%3A')[0]
		fromType = typeD(fromType)
		toType = typeD(toType)
		
		build = lambda v, t: {'value':v, 'type':t}
		toP = build(unquote(toURL), toType)
		fromP = build(unquote(fromURL), fromType)
		
		""" Sanitize Date/Time """
		timeTypeD = lambda t: t is '' and 'dep' or t.split('%3A')[0]
		timeType = timeTypeD(timeType)
		
		timeURL = unquote(timeURL)
		try:
			timeV = datetime.strptime(timeURL, '%H:%M')
		except ValueError:
			try:
				timeV = datetime.strptime(timeURL, '%d.%m.%Y %H:%M')
			except ValueError:
				try:
					timeV = datetime.strptime(timeURL, '%Y-%m-%d %H:%M')
				except ValueError:
					timeV = datetime.now(tz=GMT1())
		
		time = build(timeV, timeType)
		
		filters = {'changetime': self.request.get('changetime', 0),\
					'changes': self.request.get('changes', None),\
					'suppresslong': self.request.get('suppresslong', False),\
					'groups': self.request.get('groups', False),\
					'bicycles': self.request.get('bicycles', False),\
					'flat': self.request.get('flat', False),\
					'apikey': self.request.get('apikey', None)}
		
		s = schedule.Schedule()
		
		self.response.headers['Content-Type'] = 'text/xml'
		xml = s.loadXML(fromP, toP, time, filters)
		
		self.response.out.write('<?xml version="1.0"?>' + xml)