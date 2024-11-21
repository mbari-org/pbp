import yaml # This module is used to work with YAML data.
import json # This module is used to work with JSON data.

def yaml_to_json(file_path):
    """
    Converts a YAML file to JSON.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: JSON representation of the YAML data.
    """
    try:
        with open(file_path, 'r') as yaml_file: # Opens the YAML file in read mode.
            yaml_data = yaml.safe_load(yaml_file) # Loads the YAML data.
        return json.loads(json.dumps(yaml_data, indent=4)) # Returns the JSON representation of the YAML data.
    except Exception as e: # Catches any exception that occurs.
        return {"error": str(e)} # Returns an error message.
