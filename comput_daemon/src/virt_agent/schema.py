import json
import jsonschema
import traceback
import logging

from virt_agent.virt_agent_exception import VirtAgentJsonValidationException


def validate(json_data, schema_type='domain'):
    with open("/etc/vap/schema.json", 'r') as f:
        conf = json.load(f)
        try:
            jsonschema.validate(json_data, conf[schema_type])
        except jsonschema.exceptions.ValidationError:
            logging.critical(traceback.format_exc())
            raise VirtAgentJsonValidationException("json is invalid")
