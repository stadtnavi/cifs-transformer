import argparse
import json
import xml.etree.ElementTree as ET
import datetime
import requests

INCIDENT_TYPE_MAPPPING = {
	# TODO Map further types, even if not part of official standard
	"roadClosed": "ROAD_CLOSED",
	"carriagewayClosures": "ROAD_CLOSED",
	"newRoadworksLayout": "CONSTRUCTION",
	"repairWork": "CONSTRUCTION",
}

# Datex namespace
ns = {
	'd': 'http://datex2.eu/schema/2/2_0'
}

class DatexII2CifsTransformer():

	def __init__(self, reference):
		self.reference = reference	
		
	def roadworksName(self, situationRecord):
		for generalPublicComment in situationRecord.findall("d:generalPublicComment", ns):
				if 'roadworksName' in generalPublicComment.find('d:commentExtension/d:commentExtended/d:commentType2', ns).text:
					return generalPublicComment.find('d:comment/d:values/d:value', ns).text
		return None

	def roadName(self, situationRecord):
		linearElement = situationRecord.find('d:groupOfLocations//d:linearElement', ns)
		
		roadnameElement = linearElement.find('d:roadName/d:values/d:value', ns)
		roadname = roadnameElement.text if roadnameElement else ''
		roadnumber = linearElement.find('d:roadNumber', ns).text
		
		return '{} {}'.format(roadnumber, roadname).strip()

	def pairwise(self, t):
	    it = iter(t)
	    return list(map(list,map(lambda t: (t[1], t[0]), zip(it, it))))

	def incidentType(self, situationRecord):
		roadworkType = situationRecord.find('d:roadOrCarriagewayOrLaneManagementType', ns)
		if not roadworkType:
			roadworkType == situationRecord.find('d:roadMaintenanceType', ns)

		type = 'CONSTRUCTION'
		if not roadworkType == None:
			type = INCIDENT_TYPE_MAPPPING.get(roadworkType.text, 'CONSTRUCTION')

		return type

	def incidentSubType(self, situationRecord):
		return "ROAD_CLOSED_CONSTRUCTION" if self.incidentType(situationRecord) == "ROAD_CLOSED" else ""

	def parse(self, datex2file):
		if datex2file.startswith('http'):
			r = requests.get(datex2file)
			return ET.fromstring(r.text)
		else:
			return ET.parse(datex2file).getroot()

	def transform(self, datex2file, format = 'cifs'):
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

		closures = []
		features = []
		
		root = self.parse(datex2file)
		payload = root.find('d:payloadPublication', ns)
		for situation in payload.findall('d:situation', ns	):
			overallSituation = situation.find('d:situationExtension/d:situationExtended/d:overallSituation', ns)
			for situationRecord in situation.findall('d:situationRecord', ns):
				validity = situationRecord.find('d:validity/d:validityTimeSpecification', ns)
				endtime = validity.find('d:overallEndTime',ns).text
				if datetime.datetime.now().astimezone() > datetime.datetime.fromisoformat(endtime):
					continue
				
				polyline = situationRecord.find('d:groupOfLocations/d:linearExtension/d:linearExtended/d:gmlLineString/d:posList', ns)
				if polyline is None:
					# FIXME the order of lat/lon currently is wrong for the BW publication
					lat = float(situationRecord.find('d:groupOfLocations/d:locationForDisplay/d:longitude', ns).text)
					lon = float(situationRecord.find('d:groupOfLocations/d:locationForDisplay/d:latitude', ns).text)
					# FIXME the BW publication does not contain a LineString. As this is required by cifs, we add a minimal offset as workaround
					geometry = '{} {} {} {}'.format(lat, lon, lat, lon+0.00001)
					geojsonGeometry = {
						"type": "Point",
						"coordinates": [lon, lat]
					}
				else:
					geometry = polyline.text
					geojsonGeometry = {
						"type": "LineString",
						"coordinates": self.pairwise([float(i) for i in geometry.split()])
					}

				situationRecordId = situationRecord.get('id')
				if "-gegen" in situationRecordId:
					continue
				inverse_direction_id = situationRecordId.replace("-sperrung","-gegen-sperrung")
				direction = 'BOTH_DIRECTIONS' if situation.find("d:situationRecord[@id='{}']".format(inverse_direction_id), ns) else 'ONE_DIRECTION'
				closure = {
					'id': situationRecord.get('id'),
					'type': self.incidentType(situationRecord),
					'subtype': self.incidentSubType(situationRecord),
					'location': {
						'polyline': geometry,
				    	'street': self.roadName(situationRecord),
				    	'direction': direction,
					},
					'starttime': validity.find('d:overallStartTime',ns).text,	
					'endtime': endtime,
					'description': self.roadworksName(overallSituation),
					'reference': self.reference	
				}

				feature = {
					"type": "Feature",
					"geometry": geojsonGeometry,
					"properties": closure
				} 
				features.append(feature)
				closures.append(closure)

		if 'geojson' == format:
			geojson = { "type": "FeatureCollection", "features": features }
			json_result = geojson
		else:
			incidents = { 
				"incidents": closures,
				"timestamp": datetime.datetime.now().isoformat()
			}
			json_result = incidents

		return json_result
		

def main(datexfile, outfile, reference, format):
	json_result = DatexII2CifsTransformer(reference).transform(datexfile, format)
	json.dump(json_result, outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('datex2file', help='DATEX2 file')
    parser.add_argument('-f', dest='format', required=False, default='cifs', choices=['cifs', 'geojson'])
    parser.add_argument('-o', dest='outfile', required=False, default='-', nargs='?', type=argparse.FileType('w'))
    parser.add_argument('-r', dest='reference', required=False, default='SVZ-BW')
    args = parser.parse_args()
    main(args.datex2file, args.outfile, args.reference, args.format)	
