import pandas as pd
from functions import get_stop_places, get_route_jm, get_height_profile, calculate_height_meters, weight_routes
from pyproj import Transformer
import json
import datetime

data = pd.read_csv('Routing/data/Start_Ziel.csv')

# starting coordinates
X1 = data['X'][0]
Y1 = data['Y'][0]

# destination coordinates
X2 = data['X'][1]
Y2 = data['Y'][1]

# get stop places within a certain distance of the given coordinates
stop_places_start = get_stop_places(X1, Y1)
stop_places_dest = get_stop_places(X2, Y2)

# get the didok-numbers of the stop places
didok_number_start = [entry['number'] for entry in stop_places_start]
didok_number_dest = [entry['number'] for entry in stop_places_dest]

# get the routes between the coordinates and the stop places
routes_start = [get_route_jm(X1, Y1, entry, 'start') for entry in didok_number_start]
routes_dest = [get_route_jm(X2, Y2, entry, 'dest') for entry in didok_number_dest]

# define lists for the coordinates of the routes
coords_routes_start = []
coords_routes_dest = []

# get the coordinates of the routes
for index, feature in enumerate(routes_start):
    route = feature['features'][0]['geometry']['coordinates']
    coords_routes_start.append((index, route))

for index, feature in enumerate(routes_dest):
    route = feature['features'][0]['geometry']['coordinates']
    coords_routes_dest.append((index, route))

# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

# define lists for the coordinates of the routes in LV95
routes_start_lv95 = []
routes_dest_lv95 = []

# convert the coordinates of the routes to LV95
for index, route in coords_routes_start:
    route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
    routes_start_lv95.append((index, route_lv95))

for index, route in coords_routes_dest:
    route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
    routes_dest_lv95.append((index, route_lv95))

# get the height profiles of the routes
routes_start_heights = []
routes_dest_heights = []

for index, route in routes_start_lv95:
    profile = get_height_profile(index, route)
    routes_start_heights.append((index, profile))
    
for index, route in routes_dest_lv95:
    profile = get_height_profile(index, route)
    routes_dest_heights.append((index, profile))

start_height_meters = calculate_height_meters(routes_start_heights)
dest_height_meters = calculate_height_meters(routes_dest_heights)

# Weight the start and destination routes
start_route_weights = weight_routes(start_height_meters)
dest_route_weights = weight_routes(dest_height_meters)

# Choose the route with the lowest weight (route coordinates in WGS84)
route_start = routes_start[start_route_weights[0]]
route_dest = routes_dest[dest_route_weights[0]]

# Choose starting coordinates, didok number and route coordinates
coord_start = route_start['features'][1]['geometry']['coordinates']
number_start = didok_number_start[start_route_weights[0]]
coords_route_start = coords_routes_start[start_route_weights[0]]

# Choose destination coordinates, didok number and route coordinates
coord_dest = route_dest['features'][2]['geometry']['coordinates']
number_dest = didok_number_dest[dest_route_weights[0]]
coords_route_dest = coords_routes_dest[dest_route_weights[0]]

print(number_start, number_dest)

# ######################## Function API request ÖV Journey ##########################
# def get_journey(number_start, number_dest, time):
#     params = {
#         "from": number_start,
#         "to": number_dest,
#         "time": time
#     }

#     url = "http://transport.opendata.ch/v1/connections"
#     response = requests.get(url, params=params)

#     if response.status_code == 200:
#         stop_places = response.json()
#         return stop_places
#     else:
#         print(f"Error: Failed to retrieve data for numbers {number_start}, {number_dest}")
#         return None
    
# current_time = datetime.datetime.now().strftime("%H:%M")
# journey = get_journey(number_start, number_dest, current_time)
# with open('data/journey.json', 'w') as f:
#     json.dump(journey, f)