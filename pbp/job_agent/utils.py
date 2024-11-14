import yaml

def yaml_to_json(file_path):
    """Retrieve a value from a YAML file given a key.
    
    Args:
        file_path (str): Path to the YAML file.
        key (str): The key whose value needs to be retrieved.
        
    Returns:
        The value associated with the key, or None if the key does not exist.
    """
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except yaml.YAMLError as exc:
        print(f"Error reading YAML file: {exc}")
        return None