import argparse
from .util.csv2json import Csv2Json
import json
import logging
import datetime
from .util.cifsvalidator import validator, incidents_schema

class Csv2Cifs():
	def transform(self, csvfile):
		''' csv2cifs transforms a csv file of incidents into google waze's cifs format (JSON style), 
		    see https://developers.google.com/waze/data-feed/incident-information#json-incident.
		  Only valid rows (according to incidents jsonschema) will be added to the cifs publication.
		'''
		row_schema = incidents_schema["properties"]["incidents"]["items"]
		result = Csv2Json().transform(csvfile, 'incidents', row_schema)
		result["timestamp"] = datetime.datetime.now().isoformat()

		if not validator.is_valid(result):
			for error in validator.iter_errors(result):
				logging.warning(error)
		
		return result

def main(csvfile, outfile):
	result = Csv2Cifs().transform(csvfile)
	json.dump(result, outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile', help='CSV file')
    parser.add_argument('-o', dest='outfile', required=False, default='-', nargs='?', type=argparse.FileType('w'))
    args = parser.parse_args()
    main(args.csvfile, args.outfile)	
