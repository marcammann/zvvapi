#
#  main.py
#  zvvapi
#
#  Created by Marc Ammann on 2/11/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#
import wsgiref.handlers

import schedule

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api.urlfetch import fetch

application = webapp.WSGIApplication(
									[(r'/schedule/(stat%3A|addr%3A|wgs%3A|)([\w\d\s+%]+)/(stat%3A|addr%3A|wgs%3A|)([\w\d\s+%]+)/(dep%3A|arr%3A|)([\d\.+A%-]+)/', schedule.Schedule)],
									debug=True)


def main():
	run_wsgi_app(application)


if __name__ == '__main__':
	main()
