import os
from turtle import config_dict

import arcpy
import re
import yaml
import arcgisscripting
from etl.GSheetsEtl import GSheetsEtl

def etl():
    """
    Start the ETL process which gets the addresses to opt out
    :return: null
    """
    print("Start ETL process...")
    etl_instance = GSheetsEtl(config_dict)
    etl_instance.process()

def setup():
    """
    Sets up the work space for Arcpy to use
    :return: null
    """

    print("Setting up workspace")
    with open('config/wnvoutbreak.yaml') as f:
        config_dict = yaml.load(f, Loader=yaml.FullLoader)
    print("CAUTION: all layers that are generated in this script may be overwritten or removed.")
    # Geodatabase workplace location
    arcpy.env.workspace = f"{config_dict.get('arcpy_workspace')}"
    # allow for overwriting
    arcpy.env.overwriteOutput = f"{config_dict.get('arcpy_overwrite')}"
    print("Setup complete")
    return config_dict


def buffer(layer_name: str):
    """
    Buffer the incoming layer by a selected buffer distance
    assumes the layer is preloaded in the ArcGIS project
    :param layer_name: the layer name that will be buffered
    :return output_buffer_layer_name: the layer name that was created for the buffer analysis
    """

    # create buffer layer name
    output_buffer_layer_name = f"buff_{layer_name}"

    # get distance from user
    prompt = f"Enter a distance for layer '{output_buffer_layer_name}' "
    buff_num = get_number(prompt=prompt, num_type=float, default=1000)
    print(f"You selected: {buff_num}")

    # get unit from user
    unit = get_units_for_buffer()
    print(f"You selected: {unit}")

    # combine the distance and units as a string for buffer analysis
    buff_dist = str(buff_num) + " " + unit

    # check if the layer exists, delete it if it does
    delete_existing_layer(output_buffer_layer_name)

    # perform the buffer analysis
    print(f"Buffering '{layer_name}' to generate '{output_buffer_layer_name}' at {buff_dist}")
    print("Please wait...")
    in_features = os.path.join(f"{config_dict.get('arcpy_gdb')}", layer_name)
    out_features = os.path.join(f"{config_dict.get('arcpy_gdb')}", output_buffer_layer_name)
    arcpy.analysis.Buffer(in_features=in_features,
                          out_feature_class=out_features,
                          buffer_distance_or_field=buff_dist,
                          line_side="FULL",
                          line_end_type="ROUND",
                          dissolve_option="ALL")
    print(f"Buffer '{output_buffer_layer_name}' complete")
    return output_buffer_layer_name


def intersect(buffer_list: list[str], default_layer_name: str="intersect_layer"):
    """
    Uses the intersect analysis on the incoming layers
    :param buffer_list: a list of layer names that will be used for the intersect
    :return intersect_layer: the layer name generated for the intersect analysis
    """

    print(f"Starting the intersect analysis")

    # get buffer name from user
    intersect_layer = get_valid_layer_name(default_layer_name)

    # check if the layer exists, delete it if it does
    delete_existing_layer(intersect_layer)

    # perform the intersect analysis
    print(f"Using {buffer_list} to create '{intersect_layer}'")
    print("Please wait...")

    in_features = []
    for feature in buffer_list:
        in_features.append(os.path.join(config_dict.get('arcpy_gdb'), feature))

    out_feature = os.path.join(f"{config_dict.get('arcpy_gdb')}", intersect_layer)

    arcpy.analysis.Intersect(in_features=in_features,
                             out_feature_class=out_feature)
    print(f"Intersect '{intersect_layer}' complete")
    return intersect_layer


def spatial_join(target_layer: str, join_layer: str, default_layer_name: str="spatial_join_layer"):
    """
    Uses the spatial join analysis for incoming target and join layer
    :param target_layer: the addresses to be used
    :param join_layer: the intersect layer which will be added to the target layer
    :return spatial_join_layer: the layer of the spatial join that was created
    """

    print(f"Starting the spatial join analysis")
    spatial_join_layer = get_valid_layer_name(default_layer_name)

    # check if the layer exists, delete it if it does
    delete_existing_layer(spatial_join_layer)

    # perform the spatial analysis
    print(f"Creating '{spatial_join_layer}' between '{target_layer}' and '{join_layer}'")
    print("Please wait...")

    target_feature = os.path.join(f"{config_dict.get('arcpy_gdb')}", target_layer)
    join_feature = os.path.join(f"{config_dict.get('arcpy_gdb')}", join_layer)
    out_feature = os.path.join(f"{config_dict.get('arcpy_gdb')}", spatial_join_layer)

    arcpy.analysis.SpatialJoin(target_features=target_feature,
                               join_features=join_feature,
                               out_feature_class=out_feature,
                               join_operation="JOIN_ONE_TO_ONE",
                               join_type="KEEP_COMMON",
                               match_option="WITHIN")
    print(f"Spatial join '{spatial_join_layer}' complete")

    return spatial_join_layer


def erase(in_layer: str, erase_layer: str, default_layer_name: str="erased_layer"):
    """
    Uses the addresses created from the ETL file, and erases those addresses from the concerned mosquito areas
    :param in_layer: layer name for the mosquito areas of concern - layer which has all addresses
    :param erase_layer: layer name from ETL file which has the addresses to avoid - it will be erased from in_layer
    :return: output_layer: name of the generated layer - it will contain the addresses which can be sprayed
    """

    print(f"Starting the erase analysis")

    print(f"Erasing '{erase_layer}' points from '{in_layer}' - Create a name for the new layer that will be created.")
    output_layer = get_valid_layer_name(default_layer_name)
    # check if the layer exists, delete it if it does
    delete_existing_layer(output_layer)

    # perform the erase of features
    print(f"Erasing areas to avoid spraying. Creating '{output_layer}'.")
    print("Please wait...")

    in_features = os.path.join(f"{config_dict.get('arcpy_gdb')}", in_layer)
    erase_features = os.path.join(f"{config_dict.get('arcpy_gdb')}", erase_layer)
    out_feature = os.path.join(f"{config_dict.get('arcpy_gdb')}", output_layer)

    arcpy.analysis.Erase(in_features=in_features,
                         erase_features=erase_features,
                         out_feature_class=out_feature)
    print(f"Erase layer '{output_layer}' complete.")

    return output_layer


def spatial_selection(intersect_layer: str, select_layer: str):
    """
    Does a quick check for how many features are found within a layer
    :param intersect_layer: the boulder address layer name
    :param select_layer: areas to avoid buffer layer name
    :return: the number from the select by location - the number of addresses that fall within the buffer layer, which
        are the number of addresses that should not be sprayed
    """

    in_layer = os.path.join(f"{config_dict.get('arcpy_gdb')}", intersect_layer)
    select_features = os.path.join(f"{config_dict.get('arcpy_gdb')}", select_layer)

    address_to_inform = arcpy.management.SelectLayerByLocation(in_layer=in_layer,
                                                               overlap_type="WITHIN",
                                                               select_features=select_features,
                                                               selection_type="NEW_SELECTION")
    count = int(arcpy.GetCount_management(address_to_inform)[0])
    return count


def add_layer_to_project(layer_name: str):
    """
    Function to add an incoming layer to the project and saves the project
    :param layer_name: the name of the layer to add to the project
    :return: null
    """

    print(f"Adding {layer_name} to project.")
    print("Please wait...")
    try:
        proj_path = f"{config_dict.get('arcpy_workspace')}"
        aprx = arcpy.mp.ArcGISProject(rf"{proj_path}\WestNileOutbreak.aprx")

        # get the list of maps in the project, and select the 1st one
        map_doc = aprx.listMaps()[0]

        # add the layer to the project
        map_doc.addDataFromPath(rf"{proj_path}\WestNileOutbreak.gdb\{layer_name}")

        # save the project
        aprx.save()
        print(f"'{layer_name}' added to project map.")

    except OSError as e:
        print(f"Could not add layer '{layer_name}' to project")
        print(f"Error encountered: {e}")
        print("Try closing ArcPro and try again.")


def query_by_attribute(layer_name: str, query: str, selection: str="NEW_SELECTION"):
    """
    Function to run a query by attribute
    :param layer_name: the layer to query
    :param query: the where clause of the query to use against the layer
    :param selection: the selection type to use in query, default is new selection
    :return count_result: the number that was found from the query
    """

    print(f"Querying '{layer_name}' with query '{query}' as '{selection}'")

    in_layer = os.path.join(f"{config_dict.get('arcpy_gdb')}", layer_name)

    query_result = arcpy.management.SelectLayerByAttribute(in_layer_or_view=in_layer,
                                                           selection_type=selection,
                                                           where_clause=query)
    count_result = arcpy.management.GetCount(query_result)
    return count_result


def delete_existing_layer(layer_name: str):
    """
    Function that deletes a layer if it exists
    :param layer_name: layer name to check if it exists in the geodatabase
    :return: null
    """

    layer = os.path.join(f"{config_dict.get('arcpy_gdb')}", layer_name)
    # check if the layer exists, delete it if it does
    if arcpy.Exists(layer):
        print(f"'{layer_name}' already exists - deleting existing layer")
        arcpy.Delete_management(layer)
    else:
        print(f"'{layer_name}' does not exist yet")


def get_number(prompt: str="Enter a number", num_type=float, default=None):
    """
    Function to prompt the end user to enter a number to use for buffering the layer
    :param prompt: the sentence to prompt the user with, default is 'Enter a number'
    :param num_type: the classification of number to return, default is float
    :param default: what the default number is set to, default is none
    :return user_input: the number the user inputs
    """

    # determine the full prompt to show the user
    if default == None:
        full_prompt = f"{prompt}: "
    else:
        full_prompt = f"{prompt} (Press Enter for {default}): "

    # get a number from the user until it is a valid selection
    while True:
        user_input = input(full_prompt).strip()

        # Return default if input is empty
        if user_input == "" and default is not None:
            return default

        # check the input
        try:
            # Convert input to the specified type
            return num_type(user_input)
        except ValueError:
            print(f"Invalid input. Please enter a valid {num_type.__name__}.")


def get_units_for_buffer():
    """
    Function to prompt the end user to select an option for which buffer unit to be used for the buffer layer
    :return selected_unit: a unit that is acceptable for use within the buffer analysis; default is feet
    """

    # Define a list of acceptable units
    valid_units = config_dict.get('valid_units')
    default_unit = config_dict.get('default_unit')

    # Print the list of units to the user for unit selection
    print("Select a unit for buffering:")
    for i, unit in enumerate(valid_units, 1):
        print(f"{i}. {unit}")

    # Get user input and validate, continue loop until valid selection is made
    while True:
        user_input = input(f"Enter the number for your choice (Press Enter for {default_unit}): ").strip()

        # Return default unit if input is empty
        if user_input == "":
            return default_unit

        # Validate the entered selection
        try:
            unit_choice = int(user_input)
            # check that the input number is within the list
            if 1 <= unit_choice <= len(valid_units):
                selected_unit = valid_units[unit_choice - 1]
                # return the valid unit to buffer
                return selected_unit
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def is_valid_layer_name(layer_name: str):
    """
    Function to check for invalid characters, spaces, starting number or starting hyphen
    :param layer_name: the layer name that was entered
    :return: true if it passes
    """

    # Define invalid characters pattern (special characters)
    invalid_chars = r'[!@#$%^&*()+=;:\'",.<>/\?\\|\[\]{}`~]'

    # Check if the name contains spaces
    if ' ' in layer_name:
        raise ValueError("Layer name cannot contain spaces.")

    # Check if the name contains invalid characters
    if re.search(invalid_chars, layer_name):
        raise ValueError("Layer name contains invalid characters.")

    # Check if the name starts with a hyphen
    if layer_name[0] == '-':
        raise ValueError("Layer name cannot start with a hyphen.")

    # Check if the name starts with a number
    if layer_name[0].isdigit():
        raise ValueError("Layer name cannot start with a number.")

    # Return true if everything passes successfully
    return True


def get_valid_layer_name(default_layer_name: str=None) -> str:
    """
    Function to get a valid layer name from the user. Function will loop until a valid name is provided.
    :return layer_name: the name to use for the intersect layer
    """

    if default_layer_name != None:
        print(f"Press enter to use the default layer name '{default_layer_name}'")

    while True:
        try:
            # Ask the user for a layer name
            layer_name = input("Enter a valid layer name (no spaces or special characters): ").strip()

            # Return default layer name
            if layer_name == "" and default_layer_name is not None:
                return default_layer_name

            # Check if the input is empty (no characters entered)
            if not layer_name:
                raise ValueError("Layer name cannot be empty.")

            # Check if the name is valid
            if is_valid_layer_name(layer_name):
                print(f"Valid layer name entered: {layer_name}")
                # return the layer name entered
                return layer_name
        except ValueError as e:
            # Handle the error if the name is invalid
            print(f"Invalid input: {e}")

def ask_to_continue(prompt: str="Would you like to continue?"):
    """
    Function to ask user to continue with a task
    :param prompt: question to user
    :return choice: "Yes" or "No"
    """

    # Define a list of acceptable answers
    valid_answers = config_dict.get('valid_answers_y_n')

    print(f"{prompt}")
    for i, answer in enumerate(valid_answers, 1):
        print(f"{i}. {answer}")

    # Get user input and validate, continue loop until valid selection is made
    while True:
        user_input = input(f"Enter the number for your choice: ").strip()

        # Validate the entered selection
        try:
            user_choice = int(user_input)
            # check that the input number is within the list
            if 1 <= user_choice <= len(valid_answers):
                choice = valid_answers[user_choice - 1]
                # return the valid unit to buffer
                return choice
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def main():
    global config_dict

    try:
        config_dict = setup()
        print(config_dict)
        print()

        # layers that exist in gdb which will be buffered
        layers_to_buffer = ["Lakes_and_Reservoirs", "Wetlands", "Mosquito_Larval_Sites", "OSMP_Properties"]
        # list of buffered layers that will be used for intersect function
        buffer_layer_list = []
        # buffer the layers that need to be buffered
        for layer in layers_to_buffer:
            buffered_layer = buffer(layer)
            # add the name to the list of buffered layers
            buffer_layer_list.append(buffered_layer)
            # print a new line for readability in console
            print()

        # intersect the buffered layers
        intersect_layer = intersect(buffer_layer_list)
        print()

        # do a spatial join with the addresses that overlap the intersect layer
        spatial_join_target = "Boulder_Addresses"
        spatial_layer = spatial_join(spatial_join_target, intersect_layer, default_layer_name="address_in_concern_areas")
        print()

        # inform the user the number of address that were found
        qry = "Join_Count = 1"
        qry_result = query_by_attribute(layer_name=spatial_layer, query=qry)
        print(f"There are {qry_result} addresses found which fall within concerned mosquito areas.")
        print()

        # add the spatial join layer to the arcgis project
        answer = ask_to_continue(prompt=f"Would you like to add '{spatial_layer}' to the project map?")
        if answer == "Yes":
            add_layer_to_project(spatial_layer)
        else:
            print(f"Will not add '{spatial_layer}' to the map")
        print()

        # run the etc process for which addresses to avoid based on Google opt-out form
        etl()
        print()

        # erase the areas to avoid, which will create a new layer to use
        avoid_points_layer = config_dict.get('avoid_points')
        # create a buffered area of where to avoid spraying
        areas_to_avoid = buffer(avoid_points_layer)
        print()

        address_to_spray = erase(spatial_layer, areas_to_avoid, default_layer_name="addresses_to_spray")
        print()

        # inform the user the number of addresses that will not be sprayed
        address_count = spatial_selection(spatial_join_target, address_to_spray)
        # addresses to notify
        print(f"There are {address_count} addresses that will need treatment and must be notified.")
        print()

        # Notify the end of the program
        print("Script complete. Ending program.")

    except arcgisscripting.ExecuteError as e:
        print(f"Error encountered: {e}")
        print(f"Cannot run program. Try closing ArcGIS Pro before continuing.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()