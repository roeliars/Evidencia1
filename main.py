# Importing necessary libraries from Mesa
import mesa
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import random


import random

from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer

# Defining the agents
class Road(Agent):
    def __init__(self, unique_id, model, direction):
        super().__init__(unique_id, model)
        self.direction = direction

class Building(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Parking(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Roundabout(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class TrafficLight(Road):
    def __init__(self, unique_id, model, direction, initial_state):
        super().__init__(unique_id, model, direction)
        self.state = initial_state
        self.steps = 0

    def step(self):
        self.steps += 1
        if self.steps % 5 == 0:
            self.state = 'green' if self.state == 'red' else 'red'

class Car(Agent):
    def __init__(self, unique_id, model, start_parking):
        super().__init__(unique_id, model)
        self.start_parking = start_parking
        self.destination_parking = None

    def step(self):
        if not self.destination_parking:
            # Choose a random destination parking
            possible_parkings = [p for p in self.model.parking_agents if p != self.start_parking]
            self.destination_parking = self.random.choice(possible_parkings)

        # Move towards the destination parking following the road rules
        # This function needs to be defined to include the logic for the car's movement
        self.move_towards_destination()

    def move_towards_destination(self):
        # Movement logic for the car goes here
        pass

# Defining the model
class City(Model):
    def __init__(self):
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(24, 24, False)  # Assuming a 24x24 grid from the image
        self.parking_agents = []
        self.current_id = 0  # Initialize current_id
        self.running = True  # Initialize the running attribute

        # Create agents based on the image information (simplified example)
        # Each different type of agent would be added to the grid here
        for x in range(24):
            for y in range(24):
                # Assuming we have a function that determines the agent type and other properties based on x and y
                # In a real implementation, this would parse the image or some configuration to determine what to place
                agent_type, direction, initial_state = self.determine_agent(x, y)
                if agent_type == Road:
                    agent = Road(self.next_id(), self, direction)
                elif agent_type == Building:
                    agent = Building(self.next_id(), self)
                elif agent_type == Parking:
                    agent = Parking(self.next_id(), self)
                    self.parking_agents.append(agent)
                elif agent_type == Roundabout:
                    agent = Roundabout(self.next_id(), self)
                elif agent_type == TrafficLight:
                    agent = TrafficLight(self.next_id(), self, direction, initial_state)
                # Add the agent to the grid and schedule
                self.grid.place_agent(agent, (x, y))
                self.schedule.add(agent)

        # Spawn a car in each parking at the start of the simulation
        for parking_agent in self.parking_agents:
            car = Car(self.next_id(), self, parking_agent)
            self.grid.place_agent(car, parking_agent.pos)
            self.schedule.add(car)
        
        self.place_buildings(range(2, 9), [21])
        self.place_buildings(range(10, 12), [21])
        self.place_buildings(range(3, 12), [20])
        self.place_buildings(range(2, 11), [19])
        self.place_buildings(range(2, 6), [18])
        self.place_buildings(range(7, 12), [18])
        self.place_buildings(range(16, 18), [21, 19, 18])
        self.place_buildings(range(20, 22), [21, 20, 18])
        self.place_buildings(range(21, 22), [19])
        self.place_buildings(range(16, 17), [20])
        self.place_buildings(range(2, 5), [15, 14, 12])
        self.place_buildings(range(2, 4), [13])
        self.place_buildings(range(7, 12), [14, 12])
        self.place_buildings(range(7, 11), [13])
        self.place_buildings(range(7, 8), [15])
        self.place_buildings(range(9, 12), [15])
        self.place_buildings(range(16, 18), [15, 14, 12])
        self.place_buildings(range(20, 22), [15, 13, 12])
        self.place_buildings(range(20, 21), [14])
        self.place_buildings(range(17, 18), [13])
        self.place_buildings(range(2, 6), [7, 5, 4, 2])
        self.place_buildings(range(3, 6), [6])
        self.place_buildings(range(2, 5), [3])
        self.place_buildings(range(8, 12), [2, 4, 5, 6, 7])
        self.place_buildings(range(9, 12), [3])
        self.place_buildings(range(16, 22), [2, 7])
        self.place_buildings(range(16, 19), [3])
        self.place_buildings(range(20, 22), [3])
        self.place_buildings(range(16, 17), [6])
        self.place_buildings(range(18, 19), [6])
        self.place_buildings(range(20, 22), [6])


        self.place_parkings([(2, 20), (9, 21), (6, 18), (11, 19), (17, 20), (20, 19),
                     (8, 15), (4, 13), (11, 13), (21, 14), (16, 13),
                     (5, 3), (8, 3), (19, 3), (2, 6), (17, 6), (19, 6)])
        
        self.place_roundabouts([(13, 9), (13, 10), (14, 9), (14, 10)])

    def place_buildings(self, x_range, y_positions):
        for x in x_range:
            for y in y_positions:
                building = Building(self.next_id(), self)
                self.grid.place_agent(building, (x, y))
                self.schedule.add(building)

    def place_parkings(self, positions):
        for x, y in positions:
            parking = Parking(self.next_id(), self)
            self.grid.place_agent(parking, (x, y))
            self.schedule.add(parking)
    
    def place_roundabouts(self, positions):
        for x, y in positions:
            roundabout = Roundabout(self.next_id(), self)
            self.grid.place_agent(roundabout, (x, y))
            self.schedule.add(roundabout)

    def next_id(self):
        # Overrides the next_id method to increment current_id
        self.current_id += 1
        return self.current_id

    def determine_agent(self, x, y):
        # Placeholder for determining the agent type based on coordinates
        # In a real scenario, this would parse the image or a map configuration file
        return Road, None, None

    def step(self):
        self.schedule.step()
        # Check for end condition (no cars left)
        if all(not isinstance(agent, Car) for agent in self.schedule.agents):
            self.running = False

# Initialize and run the model
city_model = City()
while city_model.running:
    city_model.step()

from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer

def agent_portrayal(agent):
    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": "red", "w": 1, "h": 1}
    if isinstance(agent, Building):
        portrayal["Color"] = "blue"
    elif isinstance(agent, Parking):
        portrayal["Color"] = "yellow"
    elif isinstance(agent, Road):
        portrayal["Color"] = "white"
    elif isinstance(agent, Roundabout):
        portrayal["Color"] = "brown"
    elif isinstance(agent, TrafficLight):
        portrayal["Color"] = "red" if agent.state == 'red' else "green"
    elif isinstance(agent, Car):
        portrayal["Color"] = "red"
    return portrayal

grid = CanvasGrid(agent_portrayal, 24, 24, 500, 500)

# Define any other visualization modules, e.g., a chart
# chart = ChartModule([...])

server = ModularServer(City,
                       [grid],  # Include any other modules you've defined
                       "City Simulation",
                       {})  # Include any model parameters if necessary

server.port = 8521  # Default is 8521, but you can choose another
server.launch()
