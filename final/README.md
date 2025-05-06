# West Nile Virus Outbreak Analysis
This project examines the potential breading grounds for mosquito larva and runs an analysis to determine which 
addresses are within those breading grounds. For the scenario, this project generates a PDF map of the area of 
Boulder, CO, showing the concern areas of mosquito breading grounds should there be a west nile virus outbreak.
It will display the areas to spray and the address locations.

This project is the final project for a GIS course - GIS3005 at Front Range Community College.

### Process
This project takes 4 shapefiles and buffers them out to the users defined amount. 
It combines those 4 buffered areas as the initial concern area for mosquito breading ground.
It then determines which address fall within the concern area.
Then the code does an API call for a Google sheets where citizens have entered their addresses in order to opt out of 
the spraying of pesticides.
The code then creates a buffer area around the opt-out addresses, using the user provided amount. The code then
removes any addresses that fall within the opt-out area so they will not be included for spraying of pesticides.
A final map product shows the areas of concern, the addresses to be sprayed, and local Boulder shapefile layers.

## Requirements
- A license to ArcGIS Pro
- Python 3.x
- A python IDE (such as PyCharm) - or a way to run Python
- The datasets downloaded and saved from Boulder, CO
  - Lakes_and_Reservoirs
  - Wetlands
  - Mosquito_Larval_Sites
  - OSMP_Properties
  - Boulder_addresses
- A project created within ArcGIS Pro and a layout created
  - A text called "Date"
  - A text called "Title"
  - A map frame
  - A legend
  - A north arrow
  - A scale bar

## How to run this code
- Update the config file with desired configurations
- Open a terminal that has access to Python and ArcPy (such as within PyCharm)
  - Navigate to where the codebase is saved if needed
- Run the main program ```python final_main.py``` 
- Follow the prompts in the terminal
- A PDF will be saved and the path of the location will be provided
- Open the map PDF to review