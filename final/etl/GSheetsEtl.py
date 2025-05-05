import requests
import csv
import arcpy
import logging
from etl.SpatialEtl import SpatialEtl

class GSheetsEtl(SpatialEtl):
    """
    GSheetsETL performs an extract, transform, and load process using a URL to a Google spreadsheet.
    The spreadsheet must contain an address and zipcode column.

    :param:
    config_dict (dictionary): A dictionary containing a remote_url key to the Google spreadsheet
    and web geocoding service
    """

    # A dictionary of configuration keys and values
    config_dict = None

    def __init__(self, config_dict):
        """
        Calls super class and initializes parameters
        :param: config_dict: A dictionary containing a remote_url key to the Google spreadsheet
        and web geocoding service
        """
        super().__init__(config_dict)

    def process(self):
        """
        Calls the three functions (extract, transform, load) in order
        :return:
        """
        self.extract()
        self.transform()
        self.load()

    def extract(self):
        """
        Pulls the information from a Google sheets web form which contains address
        :return: null
        """
        logging.info("Calling extract function...")
        r = requests.get(self.config_dict.get('remote_url'))
        r.encoding = "utf-8"
        data = r.text  # changed from .text to .content
        with open(f"{self.config_dict.get('proj_dir')}addresses.csv", "w") as output_file:
            output_file.write(data)
        logging.info("Extract data file complete.")

    def transform(self):
        """
        Calls the API for the U.S. Census geocoder to return coordinates of the provided address.
        A new address file is created for the X Y coordinates
        :return: null
        """
        logging.info("Calling transform function...")
        transformed_file = open(f"{self.config_dict.get('proj_dir')}new_addresses.csv", "w")
        transformed_file.write("X,Y,Type\n")
        with open(f"{self.config_dict.get('proj_dir')}addresses.csv", "r") as partial_file:
            csv_dict = csv.DictReader(partial_file, delimiter=',')
            for row in csv_dict:
                address = row["Street Address"] + " Boulder CO"
                logging.info(f"{address}")
                print("Please wait...")
                geocode_url = f"{self.config_dict.get('geocoder_prefix_url')}{address}{self.config_dict.get('geocoder_suffix_url')}"
                # print(geocode_url)
                r = requests.get(geocode_url)
                resp_dict = r.json()
                x = resp_dict['result']['addressMatches'][0]['coordinates']['x']
                y = resp_dict['result']['addressMatches'][0]['coordinates']['y']
                transformed_file.write(f"{x},{y},Residential\n")
        transformed_file.close()
        logging.info("Transform data file complete.")

    def load(self):
        """
        Creates a point feature class from the input table of geocoded addresses
        :return: null
        """

        logging.info("Calling load function...")
        # set environment settings
        arcpy.env.workspace = f"{self.config_dict.get('arcpy_gdb')}"
        arcpy.env.overwriteOutput = True

        # set the local variables
        in_table = f"{self.config_dict.get('proj_dir')}new_addresses.csv"
        out_feature_class = self.config_dict.get('avoid_points')
        x_coords = "X"
        y_coords = "Y"

        # make the XY event layer
        arcpy.management.XYTableToPoint(in_table=in_table,
                                        out_feature_class=out_feature_class,
                                        x_field=x_coords,
                                        y_field=y_coords)

        # print the total rows
        print(f"Total rows for feature class: {arcpy.GetCount_management(out_feature_class)}")
        logging.info(f"Total rows for feature class: {arcpy.GetCount_management(out_feature_class)}")