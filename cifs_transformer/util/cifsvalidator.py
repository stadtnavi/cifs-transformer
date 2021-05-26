try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources
import json
import jsonschema
from . import schema

incidents_schema = json.load(pkg_resources.open_text(schema, 'incidents_feed_schema.json'))

validator = jsonschema.Draft7Validator(
				incidents_schema, 
				format_checker=jsonschema.draft7_format_checker)
