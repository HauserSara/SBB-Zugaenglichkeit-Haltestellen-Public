from functions import get_stop_places, get_route_jm, get_routes_ojp, get_coordinates, transform_coordinates, get_height_profile_jm, get_height_profile_ojp, calculate_resistance, weight_routes, get_pt_routes_ojp
from pyproj import Transformer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import pandas as pd
import folium
import os
import itertools

app = FastAPI()

origins = [
    "http://localhost:4200",
    "http://localhost:51349"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Coordinates(BaseModel):
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    time: str

# define transformer to convert coordinates from WGS84 to LV95
transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

@app.post("/route_journeymaps/")
async def create_route_jm(coordinates: Coordinates):
    print(coordinates)
    start_request = time.time()
    # get stop places within a certain distance of the given coordinates
    start_time = time.time()
    try:
        stop_places_start = get_stop_places(coordinates.lon1, coordinates.lat1)
        stop_places_dest = get_stop_places(coordinates.lon2, coordinates.lat2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    print(f"Time taken for get_stop_places: {time.time() - start_time} seconds")
    # add index to the stop places for identification
    indexed_stop_places_start = [(index, stop_place) for index, stop_place in enumerate(stop_places_start)]
    indexed_stop_places_dest = [(index, stop_place) for index, stop_place in enumerate(stop_places_dest)]
    # get the didok-numbers of the stop places
    start_time = time.time()
    didok_number_start = [(index, entry['number']) for index, entry in indexed_stop_places_start]
    didok_number_dest = [(index, entry['number']) for index, entry in indexed_stop_places_dest]
    #teststart_name = stop_places_start[start_route_weights[0]]['designationofficial']
    #testdest_name = [(index, name['designationofficial'], entry['number']) for index, name, entry in indexed_stop_places_dest]
    #print(testdest_name)
    print(f"Time taken for getting didok numbers: {time.time() - start_time} seconds")

    # TESTZWECKE
    # print("STOPPLACES")
    # print(len(didok_number_start))
    # print(didok_number_start)
    # print('----------------------------------------')
    # print(len(didok_number_dest))
    # print(didok_number_dest)
    # print("========================================")

    # get the routes between the coordinates and the stop places
    # start_time = time.time()
    # routes_start = [get_route_jm(coordinates.lat1, coordinates.lon1, entry, 'start') for entry in didok_number_start]
    # print(f"Time taken for get_route start: {time.time() - start_time} seconds")
    # start_time = time.time()
    # routes_dest = [get_route_jm(coordinates.lat2, coordinates.lon2, entry, 'dest') for entry in didok_number_dest]
    # print(f"Time taken for get_route dest: {time.time() - start_time} seconds")

    start_time = time.time()
    routes_start = []
    for index, entry in didok_number_start:
        routes_start.append((index, get_route_jm(coordinates.lat1, coordinates.lon1, entry, 'start')))
    print(f"Time taken for get_route start: {time.time() - start_time} seconds")
    #print(routes_start)

    start_time = time.time()
    routes_dest = []
    for index, entry in didok_number_dest:
        routes_dest.append((index, get_route_jm(coordinates.lat2, coordinates.lon2, entry, 'dest')))
    print(f"Time taken for get_route dest: {time.time() - start_time} seconds")

        # try:
        #     routes_dest.append(get_route_jm(coordinates.lat2, coordinates.lon2, entry, 'dest'))
        #     print(f"Time taken for get_route dest: {time.time() - start_time} seconds")
        # except requests.exceptions.RequestException:
        #     print(f"Failed to get route for dest entry: {entry}. Skipping...")
        #     continue
    # TESTZWECKE
    # print("ROUTES")
    # print(len(routes_start))
    # print(routes_start)
    # print('----------------------------------------')
    # print(len(routes_dest))
    # print(routes_dest[0])
    # print("========================================")

    # define lists for the coordinates of the routes
    coords_routes_start = []
    coords_routes_dest = []

    # get the coordinates of the routes
    start_time = time.time()
    for index, feature in routes_start:
        route = feature['features'][0]['geometry']['coordinates']
        if 'distanceInMeter' not in feature['features'][1]['properties']:
            print(f"Index_start: {index}, Properties: {feature['features'][1]['properties']}")
        else:
            distance = feature['features'][1]['properties']['distanceInMeter']
        #print(route)
        #print('----- TEST ------')
            coords_routes_start.append((index, route, distance))
    #print(coords_routes_start[0][0])
    # TESTZWECKE
    # print("COORDS")
    # print(len(coords_routes_start))
    # print(coords_routes_start)
    # print('----------------------------------------')

    for index, feature in routes_dest:
        route = feature['features'][0]['geometry']['coordinates']
        #print(len(route))
        if 'distanceInMeter' not in feature['features'][1]['properties']:
            print(f"Index_dest: {index}, Properties: {feature['features'][1]['properties']}")
        else:
            distance = feature['features'][1]['properties']['distanceInMeter']
            coords_routes_dest.append((index, route, distance))
    #print(coords_routes_dest[0])
    print(f"Time taken for getting coordinates: {time.time() - start_time} seconds")

    ######################## MAP ########################
    # Define a list of colors
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
            'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
            'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
            'gray', 'black', 'lightgray']

    color_cycle = itertools.cycle(colors)  # Create an infinite iterator of colors

    # Create a map centered at the first coordinate of the first route
    first_coordinate = coords_routes_start[0][1][0]
    m = folium.Map(location=[float(first_coordinate[1]), float(first_coordinate[0])], zoom_start=14)

    # Iterate over the start routes
    for index, route, distance in coords_routes_start:
        # Get a new color for the current route
        color = next(color_cycle)

        # Create a feature group for this route
        feature_group = folium.FeatureGroup(name=f'Start Route {index}')

        # Create a polyline for the route
        polyline = folium.PolyLine([(float(coord[1]), float(coord[0])) for coord in route], color=color, weight=2.5, opacity=1)
        feature_group.add_child(polyline)
        m.add_child(feature_group)

    # Reset the color cycle for the destination routes
    color_cycle = itertools.cycle(colors)

    # Iterate over the destination routes
    for index, route, distance in coords_routes_dest:
        # Get a new color for the current route
        color = next(color_cycle)

        # Create a feature group for this route
        feature_group = folium.FeatureGroup(name=f'Dest Route {index}')

        # Create a polyline for the route
        polyline = folium.PolyLine([(float(coord[1]), float(coord[0])) for coord in route], color=color, weight=2.5, opacity=1)
        feature_group.add_child(polyline)
        m.add_child(feature_group)

    # Add layer control to the map
    folium.LayerControl().add_to(m)

    # Save the map to an HTML file
    maps_dir = 'data/maps'
    os.makedirs(maps_dir, exist_ok=True)
    map_file = os.path.join(maps_dir, 'map_all_routes.html')
    m.save(map_file)

    ##########################################################

    # TESTZWECKE
    # print(len(coords_routes_dest))
    # print(coords_routes_dest[0])
    # print("========================================")

    # define lists for the coordinates of the routes in LV95
    routes_start_lv95 = []
    routes_dest_lv95 = []

    # convert the coordinates of the routes to LV95
    start_time = time.time()
    for index, route, distance in coords_routes_start:
        route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
        routes_start_lv95.append((index, route_lv95, distance))

    for index, route, distance in coords_routes_dest:
        route_lv95 = [(transformer.transform(latitude, longitude)) for longitude, latitude in route]
        #print(len(route_lv95))
        routes_dest_lv95.append((index, route_lv95, distance))
    print(f"Time taken for transforming coordinates: {time.time() - start_time} seconds")

    #print(routes_dest_lv95[0])
    # define lists for the height profiles of the routes
    routes_start_heights = []
    routes_dest_heights = []
    # get the height profiles of the routes
    start_time = time.time()
    for index, route, distance in routes_start_lv95:
        profile = get_height_profile_jm(index, route, distance)
        routes_start_heights.append((index, profile, distance))
    # TESTZWECKE
    # print("PROFILES")
    # print(len(routes_start_heights))
    # for index, profile in routes_start_heights[:2]:
    #     print(index, profile[:2])
    # print('----------------------------------------')
        
    for index, route, distance in routes_dest_lv95:
        profile = get_height_profile_jm(index, route, distance)
        routes_dest_heights.append((index, profile, distance))
        #print(profile)
    print(f"Time taken for get_height_profile: {time.time() - start_time} seconds")
    #print(routes_dest_heights[0])
    # TESTZWECKE
    # print(len(routes_dest_heights))
    # for index, profile in routes_dest_heights[:2]:
    #     print(index, profile[:2])
    # print("========================================")

    # Calculate the heightmeters of the routes
    # start_time = time.time()
    # start_height_meters = calculate_height_meters(routes_start_heights)
    # dest_height_meters = calculate_height_meters(routes_dest_heights)
    # print(f"Time taken for calculate_height_meters: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print("HEIGHTS")
    # print(start_height_meters)
    # print(dest_height_meters)
    # print("========================================")

    # Weight the start and destination routes
    start_time = time.time()
    start_route_weights = weight_routes(routes_start_heights)
    dest_route_weights = weight_routes(routes_dest_heights)
    print(f"Time taken for weight_routes: {time.time() - start_time} seconds")
    #print(start_route_weights)
    #print(dest_route_weights)
    # TESTZWECKE
    # print("WEIGHTS")
    # print(start_route_weights)
    # print(dest_route_weights)
    # print("========================================")

    # Choose the route with the lowest weight (route coordinates in WGS84)
    start_time = time.time()
    print(f'weight: {start_route_weights}')
    route_start = routes_start[start_route_weights[0]][1]
    route_dest = routes_dest[dest_route_weights[0]][1]
    print(f"Time taken for choosing the route: {time.time() - start_time} seconds")
    # TESTZWECKE
    # print(route_start)
    # print(route_dest)

    print(f"Time taken to return routes Journey-Maps: {time.time() - start_request} seconds")

    # Call the get_journey function with the provided time and the calculated numbers
    didok_start = didok_number_start[start_route_weights[0]]
    didok_dest = didok_number_dest[dest_route_weights[0]]
    start_name = stop_places_start[start_route_weights[0]]['designationofficial']
    dest_name = stop_places_dest[dest_route_weights[0]]['designationofficial']
    print(f'{didok_start[1]}, {start_name}, {didok_dest[1]}, {dest_name}')
    journey = get_pt_routes_ojp(didok_start[1], start_name, didok_dest[1], dest_name)

  
    return route_start, route_dest

@app.post("/route_ojp/")
async def create_route_ojp(coordinates: Coordinates):
    print(coordinates)
    start_request = time.time()

    start_time = time.time()
    # get the routes between the coordinates
    try:
        routes = get_routes_ojp(coordinates.lon1, coordinates.lat1, coordinates.lon2, coordinates.lat2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    print(f"Time taken for get_routes_ojp: {time.time() - start_time} seconds")

    # parse the xml response
    start_time = time.time()
    result_leg_ids = {}
    for trip_result in routes.iter('{http://www.vdv.de/ojp}TripResult'):
        # get the result ids
        result_id = trip_result.find('{http://www.vdv.de/ojp}ResultId').text
        leg_ids = {}
        for trip_leg in trip_result.iter('{http://www.vdv.de/ojp}TripLeg'):
            # get the leg ids
            leg_id = trip_leg.find('{http://www.vdv.de/ojp}LegId').text
            # get the leg type and coordinates of the legs
            if trip_leg.find('{http://www.vdv.de/ojp}ContinuousLeg') is not None:
                leg_ids[leg_id] = get_coordinates(trip_leg, 'ContinuousLeg')
            elif trip_leg.find('{http://www.vdv.de/ojp}TransferLeg') is not None:
                leg_ids[leg_id] = get_coordinates(trip_leg, 'TransferLeg')
            elif trip_leg.find('{http://www.vdv.de/ojp}TimedLeg') is not None:
                leg_ids[leg_id] = get_coordinates(trip_leg, 'TimedLeg')
        result_leg_ids[result_id] = leg_ids
    print(f"Time taken for parsing the xml response: {time.time() - start_time} seconds")

    # define transformer to convert coordinates from WGS84 to LV95
    transformer = Transformer.from_crs('epsg:4326', 'epsg:2056')

    start_time = time.time()
    # Transform the coordinates of the footpaths to LV95
    result_leg_ids_lv95 = transform_coordinates(result_leg_ids, transformer)
    print(f"Time taken for transforming coordinates: {time.time() - start_time} seconds")

    start_time = time.time()
    # Get the height profile for each leg
    profiles = {}
    #print(result_leg_ids_lv95)
    for result_id, legs in result_leg_ids_lv95.items():
        for leg_id, leg_info in legs.items():
            #print(f"Length of coordinates for route {result_id}, leg {leg_id}: {len(leg_info['coordinates'])}")
            route = leg_info['coordinates']
            #print(len(route))
            # Ignore the entry if coordinates are empty or route has only two points
            if len(route) > 2:
                # get the height profiles for the legs
                profile = get_height_profile_ojp(result_id, leg_id, route)
                # Add the profile to the dictionary
                if result_id not in profiles:
                    profiles[result_id] = {}
                profiles[result_id][leg_id] = profile
                #print(len(profile))
    print(f"Time taken for getting height profiles: {time.time() - start_time} seconds")
    # # Write the profiles to a JSON file
    # with open('data/profiles.json', 'w') as f:
    #     json.dump(profiles, f)

    # Calculate the average distance and standard deviation of average distance between points
    # average_distances = {}
    # standard_deviations = {}

    # for result_id, legs in profiles.items():
    #     for leg_id, leg_infos in legs.items():
    #         differences = []
    #         for i in range(1, len(leg_infos)):
    #             dist_difference = abs(leg_infos[i]['dist'] - leg_infos[i-1]['dist'])
    #             differences.append(dist_difference)
    #         average_distance = sum(differences) / len(differences) if differences else 0
    #         standard_deviation = statistics.stdev(differences) if len(differences) > 1 else 0
    #         if result_id not in average_distances:
    #             average_distances[result_id] = {}
    #             standard_deviations[result_id] = {}
    #         average_distances[result_id][leg_id] = average_distance
    #         standard_deviations[result_id][leg_id] = standard_deviation

    start_time = time.time()
    #slope_factors = {}
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

    # calculate weight for each leg (total distance multiplied with total resistance)
    for result_id, legs in profiles.items():
        for leg_id, leg_infos in legs.items():
            calculated_resistance = calculate_resistance(leg_infos)
            total_resistance = calculated_resistance[0]
            print(f'mean_slope: {calculated_resistance[1]}')
            print(f'max_slope: {calculated_resistance[2]}')
            print(f'total_resistance: {total_resistance}')
            #print(f'leg_infos: {leg_infos}')
            # total_resistance = 0
            # #get total distance of a leg (last entry in leg_infos)
            # total_distance = leg_infos[-1]['dist']
            # for i in range(1, len(leg_infos)):
            #     # calculate the height difference between two coordinates of a leg
            #     height_difference = leg_infos[i]['alts']['DTM25'] - leg_infos[i-1]['alts']['DTM25']
            #     # calculate the distance between two coordinates of a leg
            #     dist_difference = leg_infos[i]['dist'] - leg_infos[i-1]['dist']
            #     # calculate the slope angle between two coordinates of a leg
            #     slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
            #     # calculate the slope factor between two coordinates of a leg
            #     slope_factor = dist_difference * math.tan(1.1*slope_angle)
            #     # calculate the resistance between two coordinates of a leg
            #     resistance = abs(dist_difference * slope_factor)
            #     # sum up the resistance
            #     total_resistance += resistance
            # multiply the total resistance by the total distance
            #total_resistance *= total_distance 
            # add the resistance values of the legs to the dictionary
            if result_id not in resistances:
                #slope_factors[result_id] = {}
                resistances[result_id] = {}
            if leg_id not in resistances[result_id]:
                #slope_factors[result_id][leg_id] = []
                resistances[result_id][leg_id] = total_resistance
            #slope_factors[result_id][leg_id].append({'dist': dist_difference, 'slope_factor': slope_factor})
    print(f'resistance values of legs: {resistances}')
    # calculate the total resistance for each route
    for result_id, legs in resistances.items():
        total_resistances[result_id] = sum(legs.values())

    print('Time taken for calculating resistance: ', time.time() - start_time)
    print(f'total_resistances: {total_resistances}')

    start_time = time.time()
    # Find the route with the lowest total resistance
    min_resistance_route = min(total_resistances.items(), key=lambda x: x[1])

    # Write the corresponding entry from result_leg_ids to a new dictionary
    route = {min_resistance_route[0]: result_leg_ids[min_resistance_route[0]]}
    print(f"Time taken for finding the route with the lowest resistance: {time.time() - start_time} seconds")
    # print(route)

    for result_id in result_leg_ids.keys():
        print(f'result_id: {result_id}')

    # ################################## Map ##################################
    # Directory to save the maps
    maps_dir = 'data/maps'
    os.makedirs(maps_dir, exist_ok=True)

    # Define a list of colors
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
            'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
            'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
            'gray', 'black', 'lightgray']

    color_cycle = itertools.cycle(colors)  # Create an infinite iterator of colors

    # Create a map centered at the first coordinate of the first leg of the first trip result
    first_result_id, first_result_legs = list(result_leg_ids.items())[0]
    first_leg_id, first_leg_info = list(first_result_legs.items())[0]
    first_coordinate = first_leg_info['coordinates'][0]
    m = folium.Map(location=[float(first_coordinate[0]), float(first_coordinate[1])], zoom_start=14)

    # Iterate over the trip results
    for result_id, result_legs in result_leg_ids.items():
        # Get a new color for the current trip result
        color = next(color_cycle)

        # Create a feature group for this trip result
        feature_group = folium.FeatureGroup(name=result_id)

        # Iterate over the legs of the current trip result
        for leg_id, leg_info in result_legs.items():
            # Check if coordinates is not empty and create a polyline
            if leg_info['coordinates']:
                polyline = folium.PolyLine(leg_info['coordinates'], color=color, weight=2.5, opacity=1)
                feature_group.add_child(polyline)

        m.add_child(feature_group)

    # Add layer control to the map
    folium.LayerControl().add_to(m)

    # Save the map to an HTML file
    map_file = os.path.join(maps_dir, 'map_all_routes.html')
    m.save(map_file)

    print(f"Time taken to return routes OJP: {time.time() - start_request} seconds")
    return route

df = pd.read_csv('./prm_connections.csv', sep=';', encoding='utf-8')

@app.get("/check-sloid/{sloid}")
async def check_sloid(sloid: str):
    matched_rows = df[(df['EL_SLOID'] == sloid) | (df['RP_SLOID'] == sloid)]
    if not matched_rows.empty:
        all_el_sloids = matched_rows['EL_SLOID'].tolist()
        all_rp_sloids = matched_rows['RP_SLOID'].tolist()
        combined_sloids = list(set(all_el_sloids + all_rp_sloids))

        connections = []
        access_translation = {0: "Zu vervollständigen", 1: "Ja", 2: "Nein", 3: "Nich anwendbar",
                            4: "Teilweise", 5: "Ja mit Lift", 6: "Ja mit Rampe", 7: "Mit Fernbedienung"}

        # Erstelle Verbindungsinformationen
        for _, row in matched_rows.iterrows():
            info = f"Stufenfreier Zugang: {access_translation[row['STEP_FREE_ACCESS']]}, " \
                f"Taktil-visuelle Markierungen: {access_translation[row['TACT_VISUAL_MARKS']]}, " \
                f"Kontrastreiche Markierungen: {access_translation[row['CONTRASTING_AREAS']]}"

            connection = {
                "start": row['EL_SLOID'],
                "end": row['RP_SLOID'],
                "info": info
            }
            connections.append(connection)

        return {"sloids": combined_sloids, "connections": connections}
    else:
        raise HTTPException(status_code=404, detail=f"SLOID '{sloid}' not found")
