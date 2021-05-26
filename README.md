# CIFS Transformer

Google Waze's CIFS format is a simple format to publish road incidents like traffic jams, hazards, or road closures or constructions.

## Transforming DATEXII Feed into CIFS format

cifs_transfomer.datexII2cifs transforms a DATEXII MDM-Arbeitsstellen-Profil 4-00-00 file into a CIFS Format.

```
python -m cifs_transformer.datexII2cifs -d 'https://data.mfdz.de/DATEXII_Arbeitsstellen_SVZ_BW/body.xml' > cifs.json
```

## Transforming CSV file into CIFS format

A CSV file with the following structure can be transformed into a cifs.json file using `csv2cifs.py`

```
id	
type	
subtype	
location/polyline	
location/street	
location/direction	
starttime	
endtime	
description	
reference	
creationtime	
updatetime
```

Call csv2cifs via e.g.

```
python -m cifs_transformer.csv2cifs 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR-xkaaS5t5c2fZ23SSUFiYy5nFzeWA7W-HS178-st8XVPwXIA8AyWJijJ2xUw4eHSUMm1on96kGH8c/pub?gid=0&single=true&output=csv' > cifs.json
```



Every row that, converted to an incident json fragment and conforming to the cifs schema will be included in the cifs.json.

## Using cifs-transformer via docker

Running cifs-transformer via a docker-container built with this poject's Dockerfile will
retrieve csv/DATEXII road works and transform them in a `cifs.json` in the mounted `out` directory:

```
$ docker build -t mfdz/cifs-transformer .

$ docker run --rm -v $(PWD)/out:/out/
```

If you want to provide a customized config file, you may supply this by mounting your proper config or defining an ENV variable `CIFS_CONFIG`:

```
$ docker run --rm -v $(PWD)/config.json:/usr/src/app/config.json -v $(PWD)/out:/out/ mfdz/cifs-transformer
```

## Issues with the CIFS spec
Implementing this transformer, we noted some inconsistencies which IOHO should be tackled by waze:

1. A minItems value of 1 would imply there always needs to be an incident in a publication. If there is none, should the file not exist and the server return 404? I'd favor to allow 0 incidents
2. Examples on page https://developers.google.com/waze/data-feed/incident-information#xml-incident don't match the XML spec:
	* reference is listed as required, though not shown in examples and in schema only required for the optional source element
	* polyline, street, direction according to spec should be nested in location property, which is not the case for every example
