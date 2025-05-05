import logging
class SpatialEtl:
    """
    Super class that initializes the config_dict. The super class contains the functions for extract, transform, and
    load. These functions only contain logging and should be overwritten by the child classes.

    :param:
    config_dict (dictionary): A dictionary containing a remote_url key to the Google spreadsheet
    and web geocoding service
    """

    def __init__(self, config_dict):
        """
        Initializes the config dictionary
        :param config_dict: A dictionary containing a remote_url key to the Google spreadsheet
        and web geocoding service
        """
        self.config_dict = config_dict

    def extract(self):
        """
        Extracts data from the remote url to the project directory, both found within config_dict
        :return: null
        """
        logging.info(f"Extracting data from {self.config_dict.get('remote_url')} to {self.config_dict.get('proj_dir')}")

    def transform(self):
        """
        Transforms the data using the data format from config_dict
        :return: null
        """
        logging.info(f"Transforming {self.config_dict.get('data_format')}")

    def load(self):
        """
        Loads the data into the destination from config_dict
        :return: null
        """
        logging.info(f"Loading data into {self.config_dict.get('destination')}")