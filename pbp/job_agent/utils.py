import yaml
import json

def yaml_to_json(file_path):
    """
    Converts a YAML file to JSON.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: JSON representation of the YAML data.
    """
    try:
        with open(file_path, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        return json.loads(json.dumps(yaml_data, indent=4))
    except Exception as e:
        return {"error": str(e)}
