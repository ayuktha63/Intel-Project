import simpy
import random
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic as geopy_distance
import pandas as pd
import matplotlib.pyplot as plt
import folium

total_vehicles = 5
toll_zone_region = Polygon([(28.6139, 77.2090), (28.6139, 78.2090), (29.6139, 78.2090), (29.6139, 77.2090)])  # Example toll zone around Delhi
rate_per_km = 10  # cost per kilometer
env = simpy.Environment()
vehicle_data_list = [] 

class Vehicle:
    def __init__(self, env, vehicle_id, start_location, destination):
        self.env = env
        self.vehicle_id = vehicle_id
        self.start_location = start_location
        self.destination = destination
        self.position = start_location
        self.distance_traveled = 0
        self.toll_paid = 0
        self.path = [start_location]

    def move(self):
        while self.position != self.destination:
            next_location = self.calculate_next_location()
            yield self.env.timeout(1)  
            self.distance_traveled += geopy_distance((self.position[0], self.position[1]), (next_location[0], next_location[1])).km
            self.position = next_location
            self.path.append(next_location)
            print(f"Vehicle {self.vehicle_id} moved to {self.position}")

            if toll_zone_region.contains(Point(self.position)):
                toll_amount = self.calculate_toll()
                self.toll_paid = toll_amount
                print(f"Vehicle {self.vehicle_id} entered toll zone. Toll paid: ${toll_amount}")

    def calculate_next_location(self):
        next_latitude = self.position[0] + random.uniform(-0.01, 0.01)  
        next_longitude = self.position[1] + random.uniform(-0.01, 0.01)  
        return (next_latitude, next_longitude)

    def calculate_toll(self):
        return self.distance_traveled * rate_per_km

# Create vehicles and start simulation
vehicles = []
for i in range(total_vehicles):
    start_location = (random.uniform(28.5, 29.5), random.uniform(77.0, 78.0))  # Adjusted to a region in India
    destination = (random.uniform(28.5, 29.5), random.uniform(77.0, 78.0))  # Adjusted to a region in India
    vehicle = Vehicle(env, i + 1, start_location, destination)
    vehicles.append(vehicle)
    env.process(vehicle.move())

env.run(until=20)  

#print final data
for vehicle in vehicles:
    vehicle_data_list.append({
        'Vehicle ID': vehicle.vehicle_id, #This will be the Registration Number of the vehicle
        'Start': vehicle.start_location,
        'Destination': vehicle.destination,
        'Distance Traveled': vehicle.distance_traveled,
        'Toll Paid': vehicle.toll_paid
    })

vehicle_data = pd.DataFrame(vehicle_data_list)

print("\nSimulation Summary:\n")
print(vehicle_data)


map_center = (28.6139, 77.2090)  # Map of India (Delhi)
map_osm = folium.Map(location=map_center, zoom_start=10)

folium.Polygon(locations=[(point[0], point[1]) for point in toll_zone_region.exterior.coords],
               color='blue',
               fill=True,
               fill_color='blue',
               fill_opacity=0.4,
               popup='Toll Zone').add_to(map_osm)

for vehicle in vehicles:
    folium.PolyLine(locations=[(loc[0], loc[1]) for loc in vehicle.path],
                    color='green',
                    weight=2.5,
                    popup=f'Vehicle {vehicle.vehicle_id}').add_to(map_osm)


map_osm.save('simulation_map.html')


plt.figure(figsize=(10, 6))
plt.bar(vehicle_data['Vehicle ID'], vehicle_data['Toll Paid'], color='blue', alpha=0.7)
plt.xlabel('Vehicle ID')
plt.ylabel('Toll Paid ($)')
plt.title('Toll Paid by Each Vehicle')
plt.grid(True)
plt.tight_layout()
plt.show()
