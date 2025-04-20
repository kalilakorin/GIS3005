import arcpy
import requests
import csv

def extract():
    """
    Pulls the information from a Google sheets web form which contains address
    :return: null
    """
    print("Calling extract function...")
    r = requests.get("https://docs.google.com/spreadsheets/d/e/2PACX-1vTDjitOlmILea7koCORJkq6QrUcwBJM7K3vy4guXB0mU_nWR6wsPn136bpH6ykoUxyYMW7wTwkzE37l/pub?output=csv")
    r.encoding = "utf-8"
    data = r.text
    with open(r"D:\jilli\Documents\ACC-RRCC\Spring_2025\GIS3005_GIS_Apps\programs\data\asgn7\addresses.csv", "w") as output_file:
        output_file.write(data)
    print("Extract data file complete.")

def transform():
    """
    Calls the API for the U.S. Census geocoder to return coordinates of the provided address.
    A new address file is created for the X Y coordinates
    :return: null
    """
    print("Calling transform function...")
    transformed_file = open(r"D:\jilli\Documents\ACC-RRCC\Spring_2025\GIS3005_GIS_Apps\programs\data\asgn7\new_addresses.csv", "w")
    transformed_file.write("X,Y,Type\n")
    with open(r"D:\jilli\Documents\ACC-RRCC\Spring_2025\GIS3005_GIS_Apps\programs\data\asgn7\addresses.csv", "r") as partial_file:
        csv_dict = csv.DictReader(partial_file, delimiter=',')
        for row in csv_dict:
            address = row["Street Address"] + " Boulder CO"
            print(address)
            geocode_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=" + address + \
                           "&benchmark=2020&format=json"
            # print(geocode_url)
            r = requests.get(geocode_url)
            resp_dict = r.json()
            x = resp_dict['result']['addressMatches'][0]['coordinates']['x']
            y = resp_dict['result']['addressMatches'][0]['coordinates']['y']
            transformed_file.write(f"{x},{y},Residential\n")
    transformed_file.close()
    print("Transform data file complete.")

def load():
    """
    Creates a point feature class from the input table of geocoded addresses
    :return: null
    """
    print("Calling load function...")
    # set environment settings
    arcpy.env.workspace = r"D:\jilli\Documents\ACC-RRCC\Spring_2025\GIS3005_GIS_Apps\labs\lab1\WestNileOutbreak\WestNileOutbreak.gdb\\"
    arcpy.env.overwriteOutput = True

    # set the local variables
    in_table = r"D:\jilli\Documents\ACC-RRCC\Spring_2025\GIS3005_GIS_Apps\programs\data\asgn7\new_addresses.csv"
    out_feature_class = "avoid_points"
    x_coords = "X"
    y_coords = "Y"

    # make the XY event layer
    arcpy.management.XYTableToPoint(in_table=in_table, out_feature_class=out_feature_class, x_field=x_coords, y_field=y_coords)

    # print the total rows
    print(f"Total rows for feature class: {arcpy.GetCount_management(out_feature_class)}")

def main():
    extract()
    transform()
    load()

if __name__ == "__main__":
    main()