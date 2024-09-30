import requests
import http.client
import urllib.parse
import json
from fastapi import HTTPException
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime

# ======================================= Function API request stop places ======================================= # 
# get stop places within a certain distance of the given coordinates
def get_stop_places(lon, lat, distance=1000):
    params = {
        'where': f"within_distance(geopos_haltestelle, geom'Point({lon} {lat})',{distance}m)",
    }

    # encode the parameters as a URL string
    params_str = urllib.parse.urlencode(params)

    # make the API request
    conn = http.client.HTTPSConnection('data.sbb.ch', 443)
    conn.request('GET', '/api/explore/v2.1/catalog/datasets/haltestelle-haltekante/records?' + params_str)

    response = conn.getresponse()

    if response.status == 200:
        stop_places = json.loads(response.read())
        valid_stop_places = [stop_place for stop_place in stop_places['results'] if stop_place['meansoftransport'] is not None]

        if not valid_stop_places:
            raise Exception(f"No valid stop places found within {distance} m of coordinates {lon}, {lat}")

        return valid_stop_places
    
    else:
        print(f'Error: Failed to retrieve stop places for coordinates {lat}, {lon}')
        return None

# ======================================= Function Journey Maps API request routing ============================== #
# get the route between a coordinate and a stop place
session = requests.Session()

def get_route_jm(lat, lon, stop_place, type):
    params = {
        'client': 'webshop',
        'clientVersion': 'latest',
        'lang': 'de',
        'accessible': 'true',
        # 'api_key': 'API Key von Journey Maps (https://developer.sbb.ch/apis/journey-maps/information)'
    }

    # set parameters based on whether the coordinate is the starting point or the destination
    if type == 'start':
        params['fromLatLng'] = f'{lat},{lon}'
        params['toStationID'] = stop_place
    elif type == 'dest':
        params['fromStationID'] = stop_place
        params['toLatLng'] = f'{lat},{lon}'
    else:
        print(f"Error: Invalid type {type}. Expected 'start' or 'dest'")
        return None

    url = 'https://journey-maps.api.sbb.ch/v1/transfer'
    response = session.get(url, params=params)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    route = response.json()
    coords = route['features'][0]['geometry']['coordinates']
    if not isinstance(coords[0], list):
        message = f"No route found between coordinates {lat}, {lon} and stop place {stop_place}."
        raise HTTPException(status_code=400, detail=str(message))
    return route

# ======================================= Function OJP request routing =========================================== #
# get the route between two coordinates
def get_routes_ojp(lon1, lat1, lon2, lat2):
    url = "https://api.opentransportdata.swiss/ojp2020"

    # set the headers of the request
    headers = {
        "Content-Type": "application/xml",
        "Authorization": "Bearer eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6Ijc4MDlhMzhlOWUyMzQzODM4YmJjNWIwNjQxN2Y0NTk3IiwiaCI6Im11cm11cjEyOCJ9"
    }

    # Get the current date and time
    current_datetime = datetime.now()
    # Format it as a string
    current_datetime_str = current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # set the body of the request
    body = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <OJP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.siri.org.uk/siri" version="1.0" xmlns:ojp="http://www.vdv.de/ojp" xsi:schemaLocation="http://www.siri.org.uk/siri ../ojp-xsd-v1.0/OJP.xsd">
        <OJPRequest>
            <ServiceRequest>
                <RequestTimestamp>{current_datetime_str}</RequestTimestamp>
                <RequestorRef>API-Explorer</RequestorRef>
                <ojp:OJPTripRequest>
                    <RequestTimestamp>{current_datetime_str}</RequestTimestamp>
                    <ojp:Origin>
                        <ojp:PlaceRef>
                            <ojp:GeoPosition>
                                <Longitude>{lon1}</Longitude>
                                <Latitude>{lat1}</Latitude>
                            </ojp:GeoPosition>
                            <ojp:LocationName>
                                <ojp:Text>{lon1}, {lat1}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:DepArrTime>{current_datetime_str}</ojp:DepArrTime>
                        <ojp:IndividualTransportOptions>
                            <ojp:Mode>walk</ojp:Mode>
                            <ojp:MaxDistance>1000</ojp:MaxDistance>
                        </ojp:IndividualTransportOptions>
                    </ojp:Origin>
                    <ojp:Destination>
                        <ojp:PlaceRef>
                            <ojp:GeoPosition>
                                <Longitude>{lon2}</Longitude>
                                <Latitude>{lat2}</Latitude>
                            </ojp:GeoPosition>
                            <ojp:LocationName>
                                <obj:Text>{lon2}, {lat2}</obj:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:IndividualTransportOptions>
                            <ojp:Mode>walk</ojp:Mode>
                            <ojp:MaxDistance>1000</ojp:MaxDistance>
                        </ojp:IndividualTransportOptions>
                    </ojp:Destination>
                    <ojp:Params>
                        <ojp:IncludeTrackSections>true</ojp:IncludeTrackSections>
                        <ojp:IncludeLegProjection>true</ojp:IncludeLegProjection>
                        <ojp:IncludeTurnDescription>true</ojp:IncludeTurnDescription>
                        <ojp:IncludeIntermediateStops>false</ojp:IncludeIntermediateStops>
                    </ojp:Params>
                </ojp:OJPTripRequest>
            </ServiceRequest>
        </OJPRequest>
    </OJP>
    """

    response = requests.post(url, headers=headers, data=body)

    print("Status code:", response.status_code)

    # write response to xml
    with open('output.xml', 'w') as f:
        f.write(response.text)
    # Parse the response text as XML
    root = ET.fromstring(response.text)

    return root

# ======================================= Handle Trip Leg for accessing coordinates (OJP) ========================= #
def get_coordinates(trip_leg, leg_type):
    coordinates = []
    for link_projection in trip_leg.iter('{http://www.vdv.de/ojp}LinkProjection'):
        for position in link_projection.iter('{http://www.vdv.de/ojp}Position'):
            longitude = float(position.find('{http://www.siri.org.uk/siri}Longitude').text)
            latitude = float(position.find('{http://www.siri.org.uk/siri}Latitude').text)
            coordinates.append([latitude, longitude])
    return {'type': leg_type, 'coordinates': coordinates}

# ======================================= Function OJP convert coordinates (WGS84 to LV95) ======================= #
def transform_coordinates(result_leg_ids_wgs84, transformer):
    result_leg_ids_lv95 = {}
    for result_id, legs in result_leg_ids_wgs84.items():
        leg_ids_lv95 = {}
        for leg_id, leg_info in legs.items():
            # Ignore the leg if it's a Public Transport Leg
            if leg_info['type'] == 'TimedLeg':
                continue
            # transform the coordinates of the footpath legs
            else:
                coordinates_lv95 = []
                for latitude, longitude in leg_info['coordinates']:
                    # Transform the coordinates to LV95
                    lv95_Y, lv95_X = transformer.transform(latitude, longitude)
                    coordinates_lv95.append([round(lv95_Y, 1), round(lv95_X, 1)])
            leg_ids_lv95[leg_id] = {'type': leg_info['type'], 'coordinates': coordinates_lv95}
        result_leg_ids_lv95[result_id] = leg_ids_lv95

    return result_leg_ids_lv95

# ======================================= Function API request height profile Journey Maps ==================================== #
def get_height_profile_jm(index, route, distance):
    geom = {
        'type': 'LineString',
        'coordinates': route,
    }

    # Convert the geom dictionary to a JSON string
    geom_json = json.dumps(geom)

    # Include the JSON string in the URL
    data = {'geom': geom_json, 'sr': 2056}
    response = requests.post('https://api3.geo.admin.ch/rest/services/profile.json', data=data)

    if response.status_code == 200:
        profile = response.json()
        return profile
    else:
        print(f'Error: Failed to retrieve height profile for route {index}')
        print(f'URL: {response.url}')
        print(f'Response status code: {response.status_code}')
        print(f'Response text: {response.text}')
        return None
    
# ======================================= Function API request height profile OJP ==================================== #
def get_height_profile_ojp(result_id, leg_id, route):
    geom = {
        'type': 'LineString',
        'coordinates': route,
    }

    # Convert the geom dictionary to a JSON string
    geom_json = json.dumps(geom)

    # Include the JSON string in the URL
    data = {'geom': geom_json, 'sr': 2056}
    response = requests.post('https://api3.geo.admin.ch/rest/services/profile.json', data=data)

    if response.status_code == 200:
        profile = response.json()
        return profile
    else:
        print(f'Error: Failed to retrieve height profile for route {result_id}, {leg_id}')
        print(f'URL: {response.url}')
        print(f'Response status code: {response.status_code}')
        print(f'Response text: {response.text}')
        return None
    
# ======================================= Function calculate height meters ======================================= #
def calculate_height_meters(height_profiles):
    height_meters = []

    for index, profile in height_profiles:
        if profile is None:
            height_meters.append((index, None))
            continue
        upwards = 0
        downwards = 0

        # Get the heights from the profile
        heights = [point['alts']['DTM25'] for point in profile]
        # print(len(heights))

        # Calculate the differences between consecutive points
        for i in range(1, len(heights)):
            diff = heights[i] - heights[i-1]
            if diff > 0:
                upwards += diff
            elif diff < 0:
                downwards += abs(diff)

        height_meters.append((index, (round(upwards, 1), round(downwards, 1))))

    return height_meters
# ======================================= Function calculate resistance ========================================== #
def calculate_resistance(profile):
    total_resistance = 0
    slope_parts = []
    
    for i in range(1, len(profile)):
        # calculate the height difference between two coordinates
        height_difference = profile[i]['alts']['DTM25'] - profile[i-1]['alts']['DTM25']
        # calculate the distance between two coordinates
        dist_difference = profile[i]['dist'] - profile[i-1]['dist']
        # calculate the slope in %
        slope = (height_difference / dist_difference) * 100 if dist_difference != 0 else 0
        
        # calculate the slope factor between two coordinates        
        if slope > 6 or slope < -6:
            slope_factor = dist_difference * slope * 5.0
        elif 1 < slope <= 6:
            slope_factor = dist_difference * slope * (slope/10 + 1)
        elif -6 <= slope < -1:
            slope_factor = dist_difference * slope * (slope/10 - 1)
        elif -1 <= slope <= 1:
            slope_factor = dist_difference * slope

        # calculate the resistance between two coordinates
        resistance = abs(dist_difference * slope_factor)
        # sum up the resistance
        total_resistance += resistance
        slope_parts.append((slope))
        mean_slope = statistics.median(slope_parts)
        max_slope = max(slope_parts)

    return total_resistance, mean_slope, max_slope

# ======================================= Function calculate weight ============================================== #
def weight_routes(profile):
    weighted_routes = []

    for index, profile, total_distance in profile:
        #total_resistance = 0
        if profile is None:
            total_resistance = None
        else:
            calculated_resistance = calculate_resistance(profile)
            total_resistance = calculated_resistance[0]
            print(f'mean_slope: {calculated_resistance[1]}')
            print(f'max_slope: {calculated_resistance[2]}')
            print(f'total_resistance: {total_resistance}')

            # for i in range(1, len(profile)):
            #     height_difference = profile[i]['alts']['DTM25'] - profile[i-1]['alts']['DTM25']
            #     dist_difference = profile[i]['dist'] - profile[i-1]['dist']
            #     # calculate the slope angle between two coordinates of a leg
            #     slope_angle = math.degrees(math.atan(height_difference / dist_difference)) if dist_difference != 0 else 0
            #     # calculate the slope factor between two coordinates of a leg
            #     # max. 4 grad -> dort gefälle über steigung priorisieren
            #     if slope_angle > 3.43:
            #         slope_factor = dist_difference * math.tan(math.radians(1.5*slope_angle))
            #     elif 0 < slope_angle <= 3.43:
            #         slope_factor = dist_difference * math.tan(math.radians(1.1*slope_angle))
            #     elif -3.43 <= slope_angle <= 0:
            #         slope_factor = dist_difference * math.tan(math.radians(slope_angle))
            #     elif slope_angle < -3.43:
            #         slope_factor = dist_difference * math.tan(math.radians(1.5*slope_angle))
            #     # calculate the resistance between two coordinates of a leg
            #     resistance = abs(dist_difference * slope_factor)
            #     total_resistance += resistance
            #total_resistance *= total_distance  # multiply the total resistance by the total distance
        weighted_routes.append((index, total_resistance))
    
    print(weighted_routes)
        
    # return route with minimal weight, None values are ignored
    return min(weighted_routes, key=lambda x: x[1] if x[1] is not None else float('inf'))
    
# ======================================= Function OJP request öV-Journey ======================================== #
def get_pt_routes_ojp(didok_start, name_start, didok_dest, name_dest):
    url = "https://api.opentransportdata.swiss/ojp2020"

    headers = {
        "Content-Type": "application/xml",
        "Authorization": "Bearer eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6Ijc4MDlhMzhlOWUyMzQzODM4YmJjNWIwNjQxN2Y0NTk3IiwiaCI6Im11cm11cjEyOCJ9"
    }
    body = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <OJP xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.siri.org.uk/siri" version="1.0" xmlns:ojp="http://www.vdv.de/ojp" xsi:schemaLocation="http://www.siri.org.uk/siri ../ojp-xsd-v1.0/OJP.xsd">
        <OJPRequest>
            <ServiceRequest>
                <RequestTimestamp>2024-05-25T13:00:05.035Z</RequestTimestamp>
                <RequestorRef>API-Explorer</RequestorRef>
                <ojp:OJPTripRequest>
                    <RequestTimestamp>2024-05-25T13:00:05.035Z</RequestTimestamp>
                    <ojp:Origin>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{didok_start}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{name_start}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                        <ojp:DepArrTime>2024-05-25T14:59:39</ojp:DepArrTime>
                    </ojp:Origin>
                    <ojp:Destination>
                        <ojp:PlaceRef>
                            <ojp:StopPlaceRef>{didok_dest}</ojp:StopPlaceRef>
                            <ojp:LocationName>
                                <ojp:Text>{name_dest}</ojp:Text>
                            </ojp:LocationName>
                        </ojp:PlaceRef>
                    </ojp:Destination>
                    <ojp:Params>
                        <ojp:IncludeTrackSections>true</ojp:IncludeTrackSections>
                        <ojp:IncludeLegProjection>true</ojp:IncludeLegProjection>
                        <ojp:IncludeTurnDescription>true</ojp:IncludeTurnDescription>
                        <ojp:IncludeIntermediateStops>false</ojp:IncludeIntermediateStops>
                    </ojp:Params>
                </ojp:OJPTripRequest>
            </ServiceRequest>
        </OJPRequest>
    </OJP>
    """

    response = requests.post(url, headers=headers, data=body)

    # ADD ERROR HANDLING
    # ...

    print("Status code:", response.status_code)

    # # write response to xml
    # with open('output.xml', 'w') as f:
    #     f.write(response.text)
    # Parse the response text as XML
    root = ET.fromstring(response.text)

    return response.text