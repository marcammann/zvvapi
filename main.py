#!/usr/bin/python
# -*- coding: utf-8 -*-

#
#  main.py
#  zvvapi
#
#  Created by Marc Ammann on 2/11/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#

import web
import schedule
import sys

urls = (r"/schedule/(stat:|addr:|wgs:|)(.+)/(stat:|addr:|wgs:|)(.+)/(dep:|arr:|)([^/]+).+", "schedule.Schedule",
		r"/station/(stat:|addr:|wgs:|id:)(.+)/([^/]+).+", "schedule.Station")

app = web.application(urls, globals(), autoreload=True)

web.webapi.internalerror = web.debugerror
if __name__ == "__main__":
	app.run()
