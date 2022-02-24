import argparse
import json
import datetime
import logging
import requests

from .util.cifsvalidator import validator


class Cifs2CifsTransformer():

	def __init__(self, reference):
		self.reference = reference	
		
	def parse(self, cifsfile):
		if cifsfile.startswith('http'):
			r = requests.get(cifsfile)
			r.encoding = 'UTF-8'
			text = r.text.replace('\r', '')
			return json.loads(text)
		else:
			with open(cifsfile) as f:
				return json.load(f)

	def transform(self, cifsfile, format = 'cifs'):
		'''
		Transforms situation records into cifs-roadworks, like e.g.:
		[{
		  "id": "101",
		  "type": "ROAD_CLOSED",
		  "subtype": "ROAD_CLOSED_CONSTRUCTION",
		  "polyline": "51.510090 -0.006902 51.509142 -0.006564 51.506291 -0.003640 51.503796 0.001051 51.499218 0.001687 51.497365 0.002020",
		  "street": "NW 12th St",
		  "starttime": "2016-04-07T09:00:00+01:00",
		  "endtime": "2016-04-07T23:00:00+01:00",
		  "description": "Closure on I-95 NB due to construction",
		  "direction": "BOTH_DIRECTIONS"
		},
		...
		]
		'''
		result = self.parse(cifsfile)
		
		# FIXME temporary fix to work around wrong directions
		for incident in result["incidents"]:
			location = incident.get("location")
			if location and location["direction"] == "BOTH_DIRECTION":
				location["direction"] = "BOTH_DIRECTIONS"
		
		result["timestamp"] = datetime.datetime.now().isoformat()
	
		if not validator.is_valid(result):
			for error in validator.iter_errors(result):
				logging.warning(error)

		return result
		

def main(datexfile, outfile, reference):
	json_result = Cifs2CifsTransformer(reference).transform(datexfile, format)
	json.dump(json_result, outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cifsfile', help='CIFS file')
    parser.add_argument('-o', dest='outfile', required=False, default='-', nargs='?', type=argparse.FileType('w'))
    parser.add_argument('-r', dest='reference', required=True)
    args = parser.parse_args()
    main(args.cifsfile, args.outfile, args.reference)	
	
