#
#  __init__.py
#  zvvapi
#
#  Created by Marc Ammann on 2/12/09.
#  Copyright (c) 2009 Codesofa. All rights reserved.
#
import re
from lxml import etree

def vehicle_from_img(input):
	try:
		return re.search('/img/(.*)_pic.gif', input).group(1).upper().strip()
	except Exception:
		return None
		
def lineuri_from_url(input):
	try:
		res = re.search(r'traininfo\.exe/[\w]{2}/(.*)/L', input).group(1).strip()
		return res
	except Exception:
		return None
		
def normalize_line(input):
	try:
		res = re.sub(r'[\s]+', r' ', input)
		return res
	except Exception:
		return input
		
def stationid_from_url(input):
	try:
		res = re.search(r'&input=([\d]+)&', input)
		if res is not None:
			return res.group(1).strip()
		
		res = re.search(r'hstNr=([\d]+)', input)
		if res is not None:
			return res.group(1).strip()
	
		return None
	except Exception:
		raise
		return None

def station_to_node(station, elementname=u'station'):
	try:
		root = etree.Element(elementname)
		n = etree.SubElement(root, 'name')
		n.text = station['name']
		n = etree.SubElement(root, 'id')
		n.text = str(station['id'])
		n = etree.SubElement(root, 'sbbid')
		n.text = str(station['sbbid'])
	except Exception:
		return None
	
	try:
		lnode = etree.SubElement(root, 'location')
		n = etree.SubElement(lnode, 'latitude')
		n.text = '%.6f' % station['location']['latitude']
		n = etree.SubElement(lnode, 'longitude')
		n.text = '%.6f' % station['location']['longitude']
		n = etree.SubElement(lnode, 'distance')
		try:	
			n.text = '%.2f' % station['location']['distance']
		except Exception:
			n.text = '0.00'
	except Exception:
		pass
		
	try:
		n = etree.SubElement(root, 'datetime')
		n.text = station['datetime'].strftime('%Y-%m-%d %H:%M')
		n = etree.SubElement(root, 'track')
		n.text = station['track']
	except Exception:
		pass
		
	return root