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

from models import schedule

class GMT1(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=1)
	def dst(self, dt):
		return timedelta(0)
	def tzname(self,dt):
		return "Europe/Zurich"


class Schedule:
	def GET(self, fromType, fromURL, toType, toURL, timeType, timeURL):
		""" Sanitize From/To/Types """
		typeD = lambda t: t is u'' and 'stat' or t.split(':')[0]
		fromType = typeD(fromType)
		toType = typeD(toType)
		
		build = lambda v, t: {'value':v, 'type':t}
		toP = build(unquote(toURL), toType)
		fromP = build(unquote(fromURL), fromType)
		
		""" Sanitize Date/Time """
		timeTypeD = lambda t: t is u'' and 'dep' or t.split(':')[0]
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
		
		filters = web.input(changetime=0, changes=None, suppresslong=False,\
							groups=False, bicycles=False, flat=False, apikey=None)
							
		s = schedule.Schedule()
		xml = s.loadXML(fromP, toP, time, filters)
		
		web.header('Content-Type', 'text/xml')
		return '<?xml version="1.0"?><schedules>' + xml + '</schedules>'