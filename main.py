#
#  main.py
#  zvvapi
#
#  Created by Marc Ammann on 2/11/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#

import web
import schedule

urls = ("/schedule/(stat:|addr:|wgs:|)([\w\d\s+%]+)/(stat:|addr:|wgs:|)([\w\d\s+%]+)/(dep:|arr:|)([\d:\.+ -]+)/", "schedule.Schedule")
app = web.application(urls, globals())

web.webapi.internalerror = web.debugerror
if __name__ == "__main__":
    app.run()
