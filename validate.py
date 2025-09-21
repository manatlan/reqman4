
import json
from jsonschema import validate
import sys
from src.reqman4 import common

def validate_yaml(yaml_file, schema_file):
    """Validates a YAML file against a JSON schema."""
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)

        yaml_data = common.yload( open(yaml_file,"r") )
        validate(instance=yaml_data, schema=schema)
        print(f"Validation successful for {yaml_file}")
        return True
    except Exception as e:
        print(f"Validation failed for {yaml_file}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate.py <path_to_yaml_file>")
        sys.exit(1)

    yaml_to_validate = sys.argv[1]
    schema_location = "schema.json"
    validate_yaml(yaml_to_validate, schema_location)
