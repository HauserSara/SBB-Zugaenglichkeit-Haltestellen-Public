import pandas as pd
from functions import get_stop_places, get_routes_ojp, get_coordinates, transform_coordinates, get_height_profile_ojp, calculate_height_meters, weight_routes
from pyproj import Transformer
import json
import datetime
import requests
import xml.etree.ElementTree as ET
import folium
import time
import statistics
import math
import os

data = pd.read_csv('data/Start_Ziel.csv')

# starting coordinates
lon1 = data['X'][0]
lat1 = data['Y'][0]

# destination coordinates
lon2 = data['X'][1]
lat2 = data['Y'][1]

# OJP request
routes = get_routes_ojp(lon1, lat1, lon2, lat2)

# parse the xml response
result_leg_ids = {}
for trip_result in routes.iter('{http://www.vdv.de/ojp}TripResult'):
    result_id = trip_result.find('{http://www.vdv.de/ojp}ResultId').text
    leg_ids = {}
    for trip_leg in trip_result.iter('{http://www.vdv.de/ojp}TripLeg'):
        leg_id = trip_leg.find('{http://www.vdv.de/ojp}LegId').text
        if trip_leg.find('{http://www.vdv.de/ojp}ContinuousLeg') is not None:
            leg_ids[leg_id] = get_coordinates(trip_leg, 'ContinuousLeg')
        elif trip_leg.find('{http://www.vdv.de/ojp}TransferLeg') is not None:
            leg_ids[leg_id] = get_coordinates(trip_leg, 'TransferLeg')
        elif trip_leg.find('{http://www.vdv.de/ojp}TimedLeg') is not None:
            leg_ids[leg_id] = get_coordinates(trip_leg, 'TimedLeg')
    result_leg_ids[result_id] = leg_ids

print(result_leg_ids)

# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

# Transform the coordinates to LV95
result_leg_ids_lv95 = transform_coordinates(result_leg_ids, transformer)
#print(result_leg_ids_lv95)

# Get the height profile for each leg
profiles = {}

for result_id, legs in result_leg_ids_lv95.items():
    for leg_id, leg_info in legs.items():
        # Ignore the leg if it's a Public Transport Leg
        if leg_info['type'] == 'TimedLeg':
            continue
        route = leg_info['coordinates']
        # Ignore the entry if coordinates are empty or route has only two points
        if len(route) > 2:
            profile = get_height_profile_ojp(result_id, leg_id, route)
            # Add the profile to the dictionary
            if result_id not in profiles:
                profiles[result_id] = {}
            profiles[result_id][leg_id] = profile

# Write the profiles to a JSON file
with open('data/profiles.json', 'w') as f:
    json.dump(profiles, f)

# Calculate the average distance and standard deviation of average distance between points
average_distances = {}
standard_deviations = {}

for result_id, legs in profiles.items():
    for leg_id, leg_infos in legs.items():
        differences = []
        for i in range(1, len(leg_infos)):
            dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
            differences.append(dist_difference)
        average_distance = sum(differences) / len(differences) if differences else 0
        standard_deviation = statistics.stdev(differences) if len(differences) > 1 else 0
        if result_id not in average_distances:
            average_distances[result_id] = {}
            standard_deviations[result_id] = {}
        average_distances[result_id][leg_id] = average_distance
        standard_deviations[result_id][leg_id] = standard_deviation

slope_factors = {}
resistances = {}
total_resistances = {}

# calculate weight (total distance multiplied with each segment resistance)
# for result_id, legs in profiles.items():
#     for leg_id, leg_infos in legs.items():
#         total_resistance = 0
#         total_distance = leg_infos[-1]['dist']  # total distance is the 'dist' of the last entry
#         for i in range(1, len(leg_infos)):
#             height_difference = abs(leg_infos[i]['alts']['DTM25'] - leg_infos[i-1]['alts']['DTM25'])
#             dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
#             slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
#             slope_factor = dist_difference * math.tan(math.radians(slope_angle))
#             if slope_angle >= 0:
#                 slope_factor += dist_difference
#             else:
#                 slope_factor -= dist_difference
#             resistance = dist_difference * slope_factor * total_distance
#             total_resistance += resistance
#             if result_id not in slope_factors:
#                 slope_factors[result_id] = {}
#                 resistances[result_id] = {}
#             if leg_id not in slope_factors[result_id]:
#                 slope_factors[result_id][leg_id] = []
#                 resistances[result_id][leg_id] = total_resistance
#             slope_factors[result_id][leg_id].append({'dist': dist_difference, 'slope_factor': slope_factor})

# for result_id, legs in resistances.items():
#     total_resistances[result_id] = sum(legs.values())

# calculate weight (total distance multiplied with total resistance)
for result_id, legs in profiles.items():
    for leg_id, leg_infos in legs.items():
        total_resistance = 0
        # get total distance of a leg (last entry in leg_infos)
        total_distance = leg_infos[-1]['dist']
        for i in range(1, len(leg_infos)):
            height_difference = abs(leg_infos[i]['alts']['DTM25'] - leg_infos[i-1]['alts']['DTM25'])
            dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
            # calculate the slope angle between two coordinates of a leg
            slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
            # calculate the slope factor between two coordinates of a leg
            slope_factor = dist_difference * math.tan(math.radians(slope_angle))
            if slope_angle >= 0:
                slope_factor += dist_difference
            else:
                slope_factor -= dist_difference
            # calculate the resistance between two coordinates of a leg
            resistance = dist_difference * slope_factor
            total_resistance += resistance
        total_resistance *= total_distance  # multiply the total resistance by the total distance
        if result_id not in slope_factors:
            slope_factors[result_id] = {}
            resistances[result_id] = {}
        if leg_id not in slope_factors[result_id]:
            slope_factors[result_id][leg_id] = []
            resistances[result_id][leg_id] = total_resistance
        slope_factors[result_id][leg_id].append({'dist': dist_difference, 'slope_factor': slope_factor})

for result_id, legs in resistances.items():
    total_resistances[result_id] = sum(legs.values())

print(resistances)
print(total_resistances)

# Find the route with the lowest total resistance
min_resistance_route = min(total_resistances.items(), key=lambda x: x[1])

# Write the corresponding entry from result_leg_ids to a new dictionary
route = {min_resistance_route[0]: result_leg_ids[min_resistance_route[0]]}
print(route)

for result_id in result_leg_ids.keys():
    print(result_id)

# ################################## Map ##################################
# Directory to save the maps
maps_dir = 'data/maps'
os.makedirs(maps_dir, exist_ok=True)

# Iterate over the trip results
for result_id, result_legs in result_leg_ids.items():
    # Get the first leg of the current trip result
    first_leg_id, first_leg_info = list(result_legs.items())[0]

    # Create a map centered at the first coordinate of the first leg
    first_coordinate = first_leg_info['coordinates'][0]
    m = folium.Map(location=[float(first_coordinate[0]), float(first_coordinate[1])], zoom_start=14)

    # Iterate over the legs of the current trip result
    for leg_id, leg_info in result_legs.items():
        # Check if coordinates is not empty and create a polyline
        if leg_info['coordinates']:
            polyline = folium.PolyLine(leg_info['coordinates'], color="red", weight=2.5, opacity=1)
            m.add_child(polyline)

    # Save the map to an HTML file
    map_file = os.path.join(maps_dir, f'map_{result_id}.html')
    m.save(map_file)