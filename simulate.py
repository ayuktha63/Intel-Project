import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
from geopy.distance import geodesic
import simpy
import folium

# Define toll zones with geospatial coordinates
toll_zones = gpd.GeoDataFrame({
    'geometry': [Polygon([(-122.5, 37.7), (-122.5, 37.8), (-122.4, 37.8), (-122.4, 37.7)])]
})

# Initialize vehicles with starting locations and destinations
vehicles = pd.DataFrame({
    'id': [1, 2, 3],
    'start': [Point(-122.6, 37.7), Point(-122.7, 37.8), Point(-122.5, 37.6)],
    'end': [Point(-122.3, 37.7), Point(-122.4, 37.9), Point(-122.2, 37.8)],
    'balance': [100.0, 150.0, 200.0]  # Ensure balance is a float
})

def check_toll_zone_crossing(vehicle_path, toll_zones):
    path_gdf = gpd.GeoDataFrame(geometry=[vehicle_path])
    for zone in toll_zones.geometry:
        if path_gdf.intersects(zone).any():
            return True
    return False

def calculate_distance(start_point, end_point):
    return geodesic((start_point.y, start_point.x), (end_point.y, end_point.x)).km

def calculate_toll(distance):
    rate_per_km = 0.2   # Example rate
    return distance * rate_per_km

def vehicle(env, vehicle_id, start, end, balance):
    current_position = start
    total_distance = 0  # Initialize total distance covered by the vehicle
    path = LineString([start, end])
    while current_position != end:
        yield env.timeout(1)
        if check_toll_zone_crossing(path, toll_zones):
            distance = calculate_distance(start, current_position)  # Calculate distance using current_position
            toll = calculate_toll(distance)
            if balance >= toll:  # Check if the balance is sufficient for the toll
                balance -= toll
                vehicles.loc[vehicles['id'] == vehicle_id, 'balance'] = balance
                print(f"Vehicle {vehicle_id} crossed a toll zone. Toll: {toll}, New Balance: {balance}")
            else:
                print(f"Vehicle {vehicle_id} does not have sufficient balance to pay toll. Balance: {balance}, Toll: {toll}")
                break  # Break the loop if balance is insufficient
            # Update current_position to end the loop
            current_position = end
        else:
            # Update current_position to move the vehicle along the path
            next_position = path.interpolate((current_position.distance(path) + 1) / path.length)
            distance = calculate_distance(current_position, next_position)  # Calculate distance between current and next position
            total_distance += distance  # Update total distance covered
            current_position = next_position  # Update current_position to next_position
            # Deduct toll based on distance traveled
            toll = calculate_toll(distance)
            if balance >= toll:  # Check if the balance is sufficient for the toll
                balance -= toll
                vehicles.loc[vehicles['id'] == vehicle_id, 'balance'] = balance
            else:
                print(f"Vehicle {vehicle_id} does not have sufficient balance to pay toll. Balance: {balance}, Toll: {toll}")
                break  # Break the loop if balance is insufficient
            # Debugging print statements
            print(f"Vehicle {vehicle_id} - Current Balance: {balance}")
            print(f"Vehicle {vehicle_id} - Total Distance Covered: {total_distance} km")

    # After reaching the end point, print the total kilometers covered
    print(f"Vehicle {vehicle_id} - Total Distance Covered: {total_distance} km")

env = simpy.Environment()
for index, row in vehicles.iterrows():
    env.process(vehicle(env, row['id'], row['start'], row['end'], row['balance']))
env.run(until=10)

# Generate reports
print("Number of vehicles that crossed the toll zone:", len(vehicles[vehicles['balance'] < 100]))
print(vehicles)

# Visualize toll zones
m = folium.Map(location=[37.75, -122.45], zoom_start=13)
for _, zone in toll_zones.iterrows():
    folium.GeoJson(zone['geometry']).add_to(m)
m.save('toll_zones.html')
