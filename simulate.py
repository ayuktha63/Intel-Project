import simpy
import random
from shapely.geometry import Point, Polygon
from geopy.distance import distance
import pandas as pd
import matplotlib.pyplot as plt
import folium

# Constants and Parameters
NUM_VEHICLES = 5
TOLL_ZONE_POLYGONS = [
    Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
    Polygon([(3, 3), (3, 8), (8, 8), (8, 3)])
]
TOLL_RATE_PER_KM = 10  # Example toll rate per kilometer

# Simulation environment setup
env = simpy.Environment()
vehicle_data_list = [] # Use a list to store vehicle data

class Vehicle:
    def __init__(self, env, vehicle_id, start_location, destination):
        self.env = env
        self.vehicle_id = vehicle_id
        self.start_location = start_location
        self.destination = destination
        self.position = start_location
        self.distance_traveled = 0
        self.toll_paid = 0

    def move(self):
        while self.position != self.destination:
            # Simulate movement along a path (in a simplified manner)
            next_location = self.calculate_next_location()
            yield self.env.timeout(1)  # Simulate time passing
            self.distance_traveled += distance(self.position, next_location).km
            self.position = next_location
            print(f"Vehicle {self.vehicle_id} moved to {self.position}")

            # Check for toll zone crossing
            for zone_polygon in TOLL_ZONE_POLYGONS:
                if zone_polygon.contains(Point(self.position)):
                    toll_amount = self.calculate_toll()
                    self.toll_paid += toll_amount
                    print(f"Vehicle {self.vehicle_id} entered toll zone. Toll paid: ${toll_amount}")

    def calculate_next_location(self):
        # Simplified logic to calculate the next location
        # This can involve moving along a predefined route or randomly moving within a defined area
        # Here, we simulate random movement for demonstration purposes
        next_x = self.position[0] + random.uniform(-0.01, 0.01)
        next_y = self.position[1] + random.uniform(-0.01, 0.01)
        return (next_x, next_y)

    def calculate_toll(self):
        return self.distance_traveled * TOLL_RATE_PER_KM

# Create vehicles and start simulation
vehicles = []
for i in range(NUM_VEHICLES):
    start_location = (random.uniform(0, 10), random.uniform(0, 10))
    destination = (random.uniform(0, 10), random.uniform(0, 10))
    vehicle = Vehicle(env, i+1, start_location, destination)
    vehicles.append(vehicle)
    env.process(vehicle.move())

# Run the simulation
env.run(until=20)  # Run for a specified duration or until a condition

# Generate summary report
for vehicle in vehicles:
    vehicle_data_list.append({ # Append vehicle data to the list
        'Vehicle ID': vehicle.vehicle_id,
        'Start': vehicle.start_location,
        'Destination': vehicle.destination,
        'Distance Traveled': vehicle.distance_traveled,
        'Toll Paid': vehicle.toll_paid
    })

# Create DataFrame from the list of dictionaries
vehicle_data = pd.DataFrame(vehicle_data_list)

print("\nSimulation Summary:")
print(vehicle_data)

# Visualization using Folium
map_center = (5, 5)  # Center of the map
map_osm = folium.Map(location=map_center, zoom_start=10)

# Add toll zones to the map
for idx, zone_polygon in enumerate(TOLL_ZONE_POLYGONS):
    folium.Polygon(locations=[[(point[1], point[0]) for point in zone_polygon.exterior.coords]],
                   color='blue',
                   fill=True,
                   fill_color='blue',
                   fill_opacity=0.4,
                   popup=f'Toll Zone {idx+1}').add_to(map_osm)

# Add vehicle paths to the map
for vehicle in vehicles:
    folium.PolyLine(locations=[(vehicle.start_location[1], vehicle.start_location[0]),
                               (vehicle.destination[1], vehicle.destination[0])],
                    color='green',
                    weight=2.5,
                    popup=f'Vehicle {vehicle.vehicle_id}').add_to(map_osm)

# Save map as HTML
map_osm.save('simulation_map.html')

# Display summary statistics and map
plt.figure(figsize=(10, 6))
plt.bar(vehicle_data['Vehicle ID'], vehicle_data['Toll Paid'], color='blue', alpha=0.7)
plt.xlabel('Vehicle ID')
plt.ylabel('Toll Paid ($)')
plt.title('Toll Paid by Each Vehicle')
plt.grid(True)
plt.tight_layout()
plt.show()