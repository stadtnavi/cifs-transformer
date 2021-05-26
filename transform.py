from cifs_transformer.csv2cifs import Csv2Cifs
from cifs_transformer.datexII2cifs import DatexII2CifsTransformer
import argparse
import datetime
import json
import os

def main(config_file, outfile):
	with open(config_file) as input_file:
		config = json.load(input_file)

	incidents = []
	for source in config['sources']:
		if source['type'] == 'DATEXII':
			source_incidents = DatexII2CifsTransformer(source['reference']).transform(source['url'])
		else:
			source_incidents = Csv2Cifs().transform(source['url'])

		incidents.extend(source_incidents['incidents'])

	result = { 
		"incidents": incidents,
		"timestamp": datetime.datetime.now().isoformat()
	}

	json.dump(result, outfile)
	
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config', default=os.environ.get('CIFS_CONFIG', 'config.json'))
    parser.add_argument('-o', dest='outfile', required=False, default='-', nargs='?', type=argparse.FileType('w', encoding='utf-8'))
    args = parser.parse_args()
    main(args.config, args.outfile)	
