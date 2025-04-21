class SpatialEtl:

    def __init__(self, config_dict):
        self.config_dict = config_dict

    def extract(self):
        print(f"Extracting data from {self.config_dict.get('remote_url')} to {self.config_dict.get('proj_dir')}")

    def transform(self):
        print(f"Transforming {self.config_dict.get('data_format')}")

    def load(self):
        print(f"Loading data into {self.config_dict.get('destination')}")