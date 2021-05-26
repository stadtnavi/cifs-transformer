import argparse
import io
import json
import csv
import datetime
import requests
import jsonschema
import logging

class Csv2Json():

	def __init__(self):
		None


	def set(self, feature, key, value):
		if not value or "" == value:
			return 

		keys = key.split('/')
		if len(keys) == 2:
			if not feature.get(keys[0]):
				feature[keys[0]] = {}
			feature[keys[0]][keys[-1]] = value
		else:
			feature[keys[-1]] = value

	def parse_features(self, reader, schema):
		schema = None
		validator = jsonschema.Draft7Validator(schema if schema else {}, 
			format_checker=jsonschema.draft7_format_checker,)

		features = []
		for row in reader:
			feature = {}
			for key in row.keys():
				self.set(feature, key, row[key])
			
			if not validator.is_valid(feature):
				for error in validator.iter_errors(feature):
					logging.warning('Skipping row {} as it does not conform to schema'.format(row))
					logging.warning(error)
			else:
				features.append(feature)
		
		return features
	
	def transform(self, csvfile, collection_property, schema):
		'''
		Transforms a csv file into a json collection
		'''
		if csvfile.startswith('http'):
			r = requests.get(csvfile)
			features = self.parse_features(csv.DictReader(io.StringIO(r.content.decode())), schema)
		else:
			with open(csvfile) as inputfile:
				features = self.parse_features(csv.DictReader(inputfile), schema)
			
		feature_collection = { collection_property: features } if collection_property else features
		
		return feature_collection

def main(csvfile, collection_property, schema):
	print(Csv2Json().transform(csvfile, collection_property, schema))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile', help='CSV file')
    parser.add_argument('-p', dest='collection_property', required=False)
    parser.add_argument('-s', dest='schema', required=False)
    args = parser.parse_args()
    main(args.csvfile, args.collection_property, args.schema)		
