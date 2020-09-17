#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import jsonschema
import traceback
import logging

from storeagent.store_exception import StoreJsonValidationException
from storeagent import store_util as util


def validate(json_data, schema_type='vol'):
    with open('%s/schema.json' % util.STORE_JSON_PATH, 'r') as f:
        conf = json.load(f)
        try:
            jsonschema.validate(json_data, conf[schema_type])
        except jsonschema.exceptions.ValidationError:
            logging.critical(traceback.format_exc())
            raise StoreJsonValidationException('json is invalid.')
        except json.decoder.JSONDecodeError:
            logging.critical(traceback.format_exc())
            raise StoreJsonValidationException('json format error.')
