# Importing necessary libraries from Mesa
import mesa
import requests
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import random
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
import heapq

# Defining the agents
class Building(Agent):
  def __init__(self, unique_id, model):
      super().__init__(unique_id, model)

class Parking(Agent):
  def __init__(self, unique_id, model):
      super().__init__(unique_id, model)
      self.occupied = False

class Roundabout(Agent):
  def __init__(self, unique_id, model):
      super().__init__(unique_id, model)

class TrafficLightAgent(Agent):
 """ An agent representing a traffic light. """
 def __init__(self, unique_id, model, position, initial_state='green'):
     super().__init__(unique_id, model)
     self.pos = position
     self.state = initial_state

 def change_state(self):
     # Alternar entre rojo y verde
     self.state = 'green' if self.state == 'red' else 'red'


 def step(self):
     """ Acciones a realizar en cada paso de la simulación. """
     # Cambiar el estado del semáforo cada n pasos
     if self.model.schedule.steps % 5 == 0:  # Ajusta este valor si es necesario
         self.change_state()

class Car(Agent):
    def __init__(self, unique_id, model, start_parking):
        super().__init__(unique_id, model)
        self.pos = start_parking.pos
        self.start_parking = start_parking
        self.destination_parking = self.find_unique_parking()
        self.path = []
        self.has_arrived = False
        
        if self.destination_parking:
            self.path = self.calculate_path(self.pos, self.destination_parking.pos)
        
        print(f"Car {self.unique_id} initialized at {self.pos}. Destination: {self.destination_parking.pos if self.destination_parking else 'None'}")

    def calculate_path(self, start, goal):
        print(f"Calculating path from {start} to {goal}")
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == goal:
                break

            for next in self.model.allowed_connections.get(current, []):
                new_cost = cost_so_far[current] + 1
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristic(goal, next)
                    heapq.heappush(frontier, (priority, next))
                    came_from[next] = current

        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()

        if len(path) == 1:  # Solo contiene la posición inicial
            print(f"No path found from {start} to {goal}")
            return []

        return path[1:]  # Excluir la celda inicial, ya que el coche ya está allí


    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


    def find_unique_parking(self):
        # Filtrar solo los estacionamientos que no están ocupados
        available_parkings = [p for p in self.model.parking_agents if not p.occupied and p not in self.model.assigned_parkings and p != self.start_parking]
        if available_parkings:
            chosen_parking = self.random.choice(available_parkings)
            self.model.assigned_parkings.add(chosen_parking)
            return chosen_parking
        else:
            return None

    def move(self):
        if self.path:
            next_step = self.path[0]
            
            # Comprobar si hay un coche en el siguiente paso
            next_cell_contents = self.model.grid.get_cell_list_contents(next_step)
            car_in_next_step = any(isinstance(obj, Car) for obj in next_cell_contents)

            # Si hay un coche en el siguiente paso, no moverse y esperar
            if car_in_next_step:
                print(f"Car {self.unique_id} waiting for the path to clear at {next_step}")
                return

            # Esperar si hay un semáforo en rojo en el siguiente paso
            if self.model.is_red_light(next_step):
                print(f"Car {self.unique_id} waiting at red light at {next_step}")
                return  # No mover el coche, continuar en el siguiente turno

            # Mover el coche a la siguiente celda
            self.model.grid.move_agent(self, next_step)
            self.path.pop(0)

            # Comprobar si el coche ha llegado a su destino
            if self.pos == self.destination_parking.pos:
                self.has_arrived = True
                self.destination_parking.occupied = True
                print(f"Car {self.unique_id} has arrived at destination {self.pos}")
        else:
            print(f"Car {self.unique_id} at {self.pos} has no path to follow")
            
    def step(self):
            # Si el coche ya ha llegado a su destino o no tiene un destino, no necesita moverse
            if self.has_arrived or not self.destination_parking:
                print(f"Car {self.unique_id} at {self.pos} has already arrived or has no destination.")
                return

            # Si el coche tiene un destino pero aún no ha calculado una ruta, intenta calcularla
            if not self.path:
                print(f"Car {self.unique_id} at {self.pos} recalculating path to {self.destination_parking.pos}.")
                self.path = self.calculate_path(self.pos, self.destination_parking.pos)

                # Si aún no hay un camino disponible, intenta encontrar un nuevo destino
                if not self.path:
                    print(f"Car {self.unique_id} at {self.pos} cannot find a path. Looking for a new destination.")
                    self.destination_parking = self.find_unique_parking()
                    if self.destination_parking:
                        self.path = self.calculate_path(self.pos, self.destination_parking.pos)
                    return

            # Intenta mover el coche siguiendo su camino (la lógica de semáforos está en 'move')
            self.move()

# Defining the model
class City(Model):
    def __init__(self, width, height):
        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.parking_agents = []
        self.current_id = 0
        self.running = True
        self.step_count = 0
        self.assigned_parkings = set()

        # Inicializar las conexiones permitidas
        self.allowed_connections = {
           # Borde de mapa
           (0, 1): [(0, 0), (1, 1)],
           (0, 0): [(1, 0), (0, 1)],
           (1, 1): [(2, 1), (1, 0), (0, 1)],
           (2, 1): [(2, 0), (3, 1)],
           (1, 0): [(2, 0), (1, 1)],
           (2, 0): [(2, 1), (3, 0)],
           (3, 0): [(3, 1), (4, 0)],
           (3, 1): [(3, 0), (4, 1)],
           (4, 0): [(4, 1), (5, 0)],
           (4, 1): [(5, 1), (4, 0)],
           (5, 0): [(6, 0), (5, 1)],
           (5, 1): [(6, 1), (5, 0)],
           (6, 0): [(6, 1), (7, 0)],
           (6, 1): [(7, 1), (6, 0)],
           (7, 0): [(7, 1), (8, 0)],
           (7, 1): [(8, 1), (7, 0)],
           (8, 0): [(8, 1), (9, 0)],  
           (8, 1): [(8, 0), (9, 1)],
           (9, 0): [(9, 1), (10, 0)],
           (9, 1): [(9, 0), (10, 1)],
           (10, 0): [(10, 1), (11, 0)],
           (10, 1): [(10, 0), (11, 1)],
           (11, 0): [(11, 1), (12, 0)],
           (11, 1): [(11, 0), (12, 1)],
           (12, 0): [(13, 0), (12, 1)],
           (12, 1): [(12, 0), (13, 1)],
           (13, 0): [(13, 1), (14, 0)],
           (13, 1): [(13, 0), (14, 1)],
           (14, 0): [(14, 1), (15, 0)],
           (14, 1): [(14, 0), (15, 1), (14, 2)],
           (15, 0): [(15, 1), (16, 0)],
           (15, 1): [(15, 0), (16, 1), (15, 2)],
           (16, 0): [(16, 1), (17, 0)],
           (16, 1): [(16, 0), (17, 1)],
           (17, 0): [(17, 1), (18, 0)],
           (17, 1): [(17, 0), (18, 1)],
           (18, 0): [(18, 1), (19, 0)],
           (18, 1): [(18, 0), (19, 1)],
           (19, 0): [(19, 1), (20, 0)],
           (19, 1): [(19, 0), (20, 1)],
           (20, 0): [(20, 1), (21, 0)],
           (20, 1): [(20, 0), (21, 1)],
           (21, 0): [(21, 1), (22, 0)],
           (21, 1): [(21, 0), (22, 1)],
           (22, 0): [(22, 1), (23, 0)],
           (22, 1): [(22, 0), (23, 1), (22, 2)],
           (23, 0): [(22, 0), (23, 1)],
           (23, 1): [(22, 1), (23, 2)],
           (22, 2): [(23, 2), (22, 3)],
           (23, 2): [(22, 2), (23, 3)],
           (23, 3): [(22, 3), (23, 4)],
           (22, 3): [(23, 3), (22, 4)],
           (22, 4): [(23, 4), (22, 5)],
           (23, 4): [(22, 4), (23, 5)],
           (22, 5): [(23, 5), (22, 6)],
           (23, 5): [(22, 5), (23, 6)],
           (22, 6): [(23, 6), (22, 7)],
           (23, 6): [(22, 6), (23, 7)],
           (22, 7): [(23, 7), (22, 8)],
           (23, 7): [(22, 7), (23, 8)],
           (22, 8): [(23, 8), (22, 9)],
           (23, 8): [(22, 8), (23, 9)],
           (22, 9): [(23, 9), (22, 10)],
           (23, 9): [(22, 9), (23, 10)],
           (22, 10): [(23, 10), (22, 11), (21, 10)],
           (23, 10): [(22, 10), (23, 11)],
           (22, 11): [(23, 11), (22, 12), (21, 11)],
           (23, 11): [(22, 11), (23, 12)],
           (22, 12): [(23, 12), (22, 13)],
           (23, 12): [(22, 12), (23, 13)],
           (22, 13): [(23, 13), (22, 14)],
           (23, 13): [(22, 13), (23, 14)],
           (22, 14): [(23, 14), (22, 15), (21, 14)],
           (23, 14): [(22, 14), (23, 15)],
           (22, 15): [(23, 15), (22, 16)],
           (23, 15): [(22, 15), (23, 16)],
           (22, 16): [(23, 16), (22, 17)],
           (23, 16): [(22, 16), (23, 17)],
           (22, 17): [(23, 17), (22, 18)],
           (23, 17): [(22, 17), (23, 18)],
           (22, 18): [(23, 18), (22, 19)],
           (23, 18): [(22, 18), (23, 19)],
           (22, 19): [(23, 19), (22, 20)],
           (23, 19): [(22, 19), (23, 20)],
           (22, 20): [(23, 20), (22, 21)],
           (23, 20): [(22, 20), (23, 21)],
           (22, 21): [(23, 21), (22, 22)],
           (23, 21): [(22, 21), (23, 22)],
           (22, 22): [(23, 22), (22, 23), (21, 22)],
           (23, 22): [(22, 22), (23, 23)],
           (22, 23): [(21, 23), (22, 22)],
           (23, 23): [(22, 23), (23, 22)],
           (21, 23): [(21, 22), (20, 23)],
           (21, 22): [(21, 23), (20, 22)],
           (20, 23): [(20, 22), (19, 23)],
           (20, 22): [(20, 23), (19, 22)],
           (19, 23): [(19, 22), (18, 23)],
           (19, 22): [(19, 23), (18, 22), (19, 21)],
           (18, 23): [(18, 22), (17, 23)],
           (18, 22): [(18, 23), (17, 22), (18, 21)],
           (17, 23): [(17, 22), (16, 23)],
           (17, 22): [(17, 23), (16, 22)],
           (16, 23): [(16, 22), (15, 23)],
           (16, 22): [(16, 23), (15, 22)],
           (15, 23): [(15, 22), (14, 23)],
           (15, 22): [(15, 23), (14, 22)],
           (14, 23): [(14, 22), (13, 23)],
           (14, 22): [(14, 23), (13, 22)],
           (13, 23): [(13, 22), (12, 23)],
           (13, 22): [(13, 23), (12, 22), (13, 21)],
           (12, 23): [(12, 22), (11, 23)],
           (12, 22): [(12, 23), (11, 22), (12, 21)],
           (11, 23): [(11, 22), (10, 23)],
           (11, 22): [(11, 23), (10, 22)],
           (10, 23): [(10, 22), (9, 23)],
           (10, 22): [(10, 23), (9, 22)],
           (9, 23): [(9, 22), (8, 23)],
           (9, 22): [(9, 23), (8, 22), (9, 21)],
           (8, 23): [(8, 22), (7, 23)],
           (8, 22): [(8, 23), (7, 22)],
           (7, 23): [(7, 22), (6, 23)],
           (7, 22): [(7, 23), (6, 22)],
           (6, 23): [(6, 22), (5, 23)],
           (6, 22): [(6, 23), (5, 22)],
           (5, 23): [(5, 22), (4, 23)],
           (5, 22): [(5, 23), (4, 22)],
           (4, 23): [(4, 22), (3, 23)],
           (4, 22): [(4, 23), (3, 22)],
           (3, 23): [(3, 22), (2, 23)],
           (3, 22): [(3, 23), (2, 22)],
           (2, 23): [(2, 22), (1, 23)],
           (2, 22): [(2, 23), (1, 22)],
           (1, 23): [(1, 22), (0, 23)],
           (1, 22): [(0, 22), (1, 22), (1, 23)],
           (0, 23): [(0, 22), (1, 23)],
           (0, 22): [(1, 22), (0, 21)],
           (0, 21): [(1, 21), (0, 20)],
           (1, 21): [(0, 21), (1, 20)],
           (0, 20): [(1, 20), (0, 19)],
           (1, 20): [(0, 20), (1, 19), (2, 20)],
           (0, 19): [(1, 19), (0, 18)],
           (1, 19): [(0, 19), (1, 18)],
           (0, 18): [(1, 18), (0, 17)],
           (1, 18): [(0, 18), (1, 17)],
           (0, 17): [(1, 17), (0, 16)],
           (1, 17): [(0, 17), (1, 16)],
           (0, 16): [(1, 16), (0, 15)],
           (1, 16): [(0, 16), (1, 15)],
           (0, 15): [(1, 15), (0, 14)],
           (1, 15): [(0, 15), (1, 14)],
           (0, 14): [(1, 14), (0, 13)],
           (1, 14): [(0, 14), (1, 13)],
           (0, 13): [(1, 13), (0, 12)],
           (1, 13): [(0, 13), (1, 12)],
           (0, 12): [(1, 12), (0, 11)],
           (1, 12): [(0, 12), (1, 11)],
           (0, 11): [(1, 11), (0, 10)],
           (1, 11): [(0, 11), (1, 10)],
           (0, 10): [(1, 10), (0, 9)],
           (1, 10): [(0, 10), (1, 9)],
           (0, 9): [(1, 9), (0, 8)],
           (1, 9): [(0, 9), (1, 8), (2, 9)],
           (0, 8): [(1, 8), (0, 7)],
           (1, 8): [(0, 8), (1, 7), (2, 8)],
           (0, 7): [(1, 7), (0, 6)],
           (1, 7): [(0, 7), (1, 6)],
           (0, 6): [(1, 6), (0, 5)],
           (1, 6): [(0, 6), (1, 5), (2, 6)],
           (0, 5): [(1, 5), (0, 4)],
           (1, 5): [(0, 5), (1, 4)],
           (0, 4): [(1, 4), (0, 3)],
           (1, 4): [(0, 4), (1, 3)],
           (0, 3): [(1, 3), (0, 2)],
           (1, 3): [(0, 3), (1, 2)],
           (0, 2): [(1, 2), (0, 1)],
           (1, 2): [(0, 2), (1, 1)],


           # Dentro del mapa
           (6, 7): [(7, 7), (6, 6)],
           (7, 7): [(6, 7), (7, 6)],
           (6, 6): [(7, 6), (6, 5)],
           (7, 6): [(6, 6), (7, 5)],
           (6, 5): [(7, 5), (6, 4)],
           (7, 5): [(6, 5), (7, 4)],
           (6, 4): [(7, 4), (6, 3)],
           (7, 4): [(6, 4), (7, 3)],
           (6, 3): [(7, 3), (6, 2), (5, 3)],
           (7, 3): [(6, 3), (7, 2), (8, 3)],
           (6, 2): [(7, 2), (6, 1)],
           (7, 2): [(6, 2), (7, 1)],
           (2, 9): [(3, 9), (2, 8)],
           (2, 8): [(2, 9), (3, 8)],
           (3, 9): [(3, 8), (4, 9)],
           (3, 8): [(3, 9), (4, 8)],
           (4, 9): [(4, 8), (5, 9)],
           (4, 8): [(4, 9), (5, 8)],
           (5, 9): [(5, 8), (6, 9)],
           (5, 8): [(5, 9), (6, 8)],
           (6, 9): [(6, 8), (7, 9)],
           (6, 8): [(6, 9), (7, 8), (6, 7)],
           (7, 9): [(7, 8), (8, 9)],
           (7, 8): [(7, 9), (8, 8), (7, 7)],
           (8, 9): [(8, 8), (9, 9)],
           (8, 8): [(8, 9), (9, 8)],
           (9, 9): [(9, 8), (10, 9)],
           (9, 8): [(9, 9), (10, 8)],
           (10, 9): [(10, 8), (11, 9)],
           (10, 8): [(10, 9), (11, 8)],
           (11, 9): [(11, 8), (12, 9)],
           (11, 8): [(11, 9), (12, 8)],
           (12, 9): [(12, 8)],
           (12, 8): [(13, 8), (12, 7)],
           (13, 8): [(14, 8), (13, 7)],
           (14, 8): [(15, 8)],
           (15, 8): [(15, 9), (16, 8)],
           (15, 9): [(15, 10), (16, 9)],
           (15, 10): [(15, 11)],
           (15, 11): [(14, 11), (15, 12)],
           (14, 11): [(13, 11), (14, 12)],
           (13, 11): [(12, 11)],
           (12, 11): [(11, 11), (12, 10)],
           (12, 10): [(11, 10), (12, 9)],
           (12, 7): [(13, 7), (12, 6)],
           (13, 7): [(12, 7), (13, 6)],
           (12, 6): [(13, 6), (12, 5)],
           (13, 6): [(12, 6), (13, 5)],
           (12, 5): [(13, 5), (12, 4)],
           (13, 5): [(12, 5), (13, 4)],
           (12, 4): [(13, 4), (12, 3)],
           (13, 4): [(12, 4), (13, 3)],
           (12, 3): [(13, 3), (12, 2)],
           (13, 3): [(12, 3), (13, 2)],
           (12, 2): [(13, 2), (12, 1)],
           (13, 2): [(12, 2), (13, 1)],
           (14, 2): [(15, 2), (14, 3)],
           (15, 2): [(14, 2), (15, 3)],
           (14, 3): [(15, 3), (14, 4)],
           (15, 3): [(14, 3), (15, 4)],
           (14, 4): [(15, 4), (14, 5)],
           (15, 4): [(14, 4), (15, 5), (16, 4)],
           (14, 5): [(15, 5), (14, 6)],
           (15, 5): [(14, 5), (15, 6), (16, 5)],
           (14, 6): [(15, 6), (14, 7)],
           (15, 6): [(14, 6), (15, 7)],
           (14, 7): [(14, 8), (15, 7)],
           (15, 7): [(14, 7), (15, 8)],
           (16, 5): [(17, 5), (16, 4)],
           (16, 4): [(16, 5), (17, 4)],
           (17, 5): [(17, 6), (18, 5), (17, 4)],
           (17, 4): [(17, 5), (18, 4)],
           (18, 5): [(19, 5), (18, 4)],
           (18, 4): [(18, 5), (19, 4)],
           (19, 5): [(19, 6), (20, 5), (19, 4)],
           (19, 4): [(19, 5), (20, 4), (19, 3)],
           (20, 5): [(21, 5), (20, 4)],
           (20, 4): [(20, 5), (21, 4)],
           (21, 5): [(22, 5), (21, 4)],
           (21, 4): [(21, 5), (22, 4)],
           (16, 9): [(16, 8), (17, 9)],
           (16, 8): [(16, 9), (17, 8)],
           (17, 9): [(17, 8), (18, 9)],
           (17, 8): [(17, 9), (18, 8)],
           (18, 9): [(18, 8), (19, 9)],
           (18, 8): [(18, 9), (19, 8)],
           (19, 9): [(19, 8), (20, 9)],
           (19, 8): [(19, 9), (20, 8)],
           (20, 9): [(20, 8), (21, 9)],
           (20, 8): [(20, 9), (21, 8)],
           (21, 9): [(22, 9), (21, 8)],
           (21, 8): [(21, 9), (22, 8)],
           (21, 10): [(21, 11), (20, 10)],
           (21, 11): [(21, 10), (20, 11)],
           (20, 10): [(20, 11), (19, 10)],
           (20, 11): [(20, 10), (19, 11)],
           (19, 10): [(19, 11), (18, 10)],
           (19, 11): [(19, 10), (18, 11), (19, 12)],
           (18, 10): [(18, 11), (17, 10)],
           (18, 11): [(18, 10), (17, 11), (18, 12)],
           (17, 10): [(17, 11), (16, 10)],
           (17, 11): [(17, 10), (16, 11)],
           (16, 10): [(16, 11), (15, 10)],
           (16, 11): [(16, 10), (15, 11)],
           (19, 12): [(18, 12), (19, 13)],
           (18, 12): [(19, 12), (18, 13)],
           (19, 13): [(18, 13), (19, 14)],
           (18, 13): [(19, 13), (18, 14)],
           (19, 14): [(19, 15), (18, 14)],
           (18, 14): [(19, 14), (18, 15)],
           (19, 15): [(18, 15), (19, 15)],
           (18, 15): [(19, 15), (18, 16)],
           (18, 21): [(19, 21), (18, 20)],
           (19, 21): [(18, 21), (19, 20)],
           (18, 20): [(19, 20), (18, 19), (17, 20)],
           (19, 20): [(18, 20), (19, 19)],
           (18, 19): [(19, 19), (18, 18)],
           (19, 19): [(18, 19), (19, 18), (20, 19)],
           (18, 18): [(19, 18), (18, 17)],
           (19, 18): [(18, 18), (19, 17)],
           (18, 17): [(18, 16), (19, 17)],
           (19, 17): [(19, 16), (20, 17)],
           (18, 16): [(18, 17), (19, 16)],
           (19, 16): [(19, 17), (20, 16)],
           (20, 17): [(20, 16), (21, 17)],
           (20, 16): [(20, 17), (21, 16)],
           (21, 17): [(21, 16), (22, 17)],
           (21, 16): [(21, 17), (22, 16)],
           (15, 12): [(14, 12), (15, 13)],
           (14, 12): [(15, 12), (14, 13)],
           (15, 13): [(14, 13), (15, 14), (16, 13)],
           (14, 13): [(15, 13), (14, 14)],
           (15, 14): [(14, 14), (15, 15)],
           (14, 14): [(15, 14), (14, 15)],
           (15, 15): [(14, 15), (15, 16)],
           (14, 15): [(15, 15), (14, 16)],
           (15, 16): [(14, 16), (15, 17), (16, 16)],
           (14, 16): [(15, 16), (14, 17)],
           (15, 17): [(14, 17), (15, 18), (16, 17)],
           (14, 17): [(15, 17), (14, 18)],
           (15, 18): [(14, 18), (15, 19)],
           (14, 18): [(15, 18), (14, 19)],
           (15, 19): [(14, 19), (15, 20)],
           (14, 19): [(15, 19), (14, 20)],
           (15, 20): [(14, 20), (15, 21)],
           (14, 20): [(15, 20), (14, 21)],
           (15, 21): [(14, 21), (15, 22)],
           (14, 21): [(15, 21), (14, 22)],
           (16, 17): [(17, 17), (16, 16)],
           (16, 16): [(16, 17), (17, 16)],
           (17, 17): [(17, 16), (18, 17)],
           (17, 16): [(17, 17), (18, 16)],
           (12, 21): [(13, 21), (12, 20)],
           (13, 21): [(12, 21), (13, 20)],
           (12, 20): [(13, 20), (12, 19)],
           (13, 20): [(12, 20), (13, 19)],
           (12, 19): [(13, 19), (12, 18), (11, 19)],
           (13, 19): [(12, 19), (13, 18)],
           (12, 18): [(13, 18), (12, 17)],
           (13, 18): [(12, 18), (13, 17)],
           (12, 17): [(13, 17), (12, 16), (11, 17)],
           (13, 17): [(12, 17), (13, 16)],
           (12, 16): [(13, 16), (12, 15), (11, 16)],
           (13, 16): [(13, 15), (12, 16)],
           (12, 15): [(13, 15), (12, 14)],
           (13, 15): [(12, 15), (13, 14)],
           (12, 14): [(13, 14), (12, 13)],
           (13, 14): [(12, 14), (13, 13)],
           (12, 13): [(11, 13), (12, 12), (13, 13)],
           (13, 13): [(12, 13), (13, 12)],
           (12, 12): [(13, 12), (12, 11)],
           (13, 12): [(12, 12), (13, 11)],
           (11, 11): [(11, 10), (10, 11)],
           (11, 10): [(11, 11), (10, 10)],
           (10, 11): [(10, 10), (9, 11)],
           (10, 10): [(10, 11), (9, 10)],
           (9, 11): [(9, 10), (8, 11)],
           (9, 10): [(9, 11), (8, 10)],
           (8, 11): [(8, 10), (7, 11)],
           (8, 10): [(8, 11), (7, 10)],
           (7, 11): [(7, 10), (6, 11)],
           (7, 10): [(7, 11), (6, 10)],
           (6, 11): [(6, 12), (5, 11), (6, 10)],
           (6, 10): [(6, 11), (5, 10)],
           (5, 11): [(5, 12), (4, 11), (5, 10)],
           (5, 10): [(5, 11), (4, 10)],
           (4, 11): [(4, 10), (3, 11)],
           (4, 10): [(4, 11), (3, 10)],
           (3, 11): [(3, 10), (2, 11)],
           (3, 10): [(3, 11), (2, 10)],
           (2, 11): [(2, 10), (1, 11)],
           (2, 10): [(2, 11), (1, 10)],
           (6, 12): [(5, 12), (6, 13)],
           (5, 12): [(6, 12), (5, 13)],
           (6, 13): [(5, 13), (6, 14)],
           (5, 13): [(6, 13), (5, 14), (4, 13)],
           (6, 14): [(5, 14), (6, 15)],
           (5, 14): [(6, 14), (5, 15)],
           (6, 15): [(5, 15), (6, 16)],
           (5, 15): [(6, 15), (5, 16)],
           (6, 16): [(5, 16), (6, 17)],
           (5, 16): [(5, 17), (4, 16)],
           (6, 17): [(5, 17), (6, 16), (6, 18)],
           (5, 17): [(5, 16), (4, 17)],
           (4, 17): [(4, 16), (3, 17)],
           (4, 16): [(4, 17), (3, 16)],
           (3, 17): [(3, 16), (2, 17)],
           (3, 16): [(3, 17), (2, 16)],
           (2, 17): [(2, 16), (1, 17)],
           (2, 16): [(2, 17), (1, 16)],
           (11, 17): [(11, 16), (10, 17)],
           (11, 16): [(11, 17), (10, 16)],
           (10, 17): [(10, 16), (9, 17)],
           (10, 16): [(10, 17), (9, 16)],
           (9, 17): [(9, 16), (8, 17)],
           (9, 16): [(9, 17), (8, 16)],
           (8, 17): [(8, 16), (7, 17)],
           (8, 16): [(8, 17), (7, 16), (8, 15)],
           (7, 17): [(6, 17), (7, 16)],
           (7, 16): [(7, 17), (6, 16)],


           # Al final, revisar TODOS los estacionamientos y sus adyacentes
           (2, 6): [(1, 6)],
           (5, 3): [(6, 3)],
           (8, 3): [(7, 3)],
           (17, 6): [(17, 5)],
           (19, 6): [(19, 5)],
           (19, 3): [(19, 4)],
           (21, 14): [(22, 14)],
           (20, 19): [(19, 19)],
           (17, 20): [(18, 20)],
           (16, 13): [(15, 13)],
           (11, 19): [(12, 19)],
           (11, 13): [(12, 13)],
           (8, 15): [(8, 16)],
           (4, 13): [(5, 13)],
           (9, 21): [(9, 22)],
           (2, 20): [(1, 20)],
           (6, 18): [(6, 17)]
       }

        # Validar que todas las conexiones son tuplas
        for key, connections in self.allowed_connections.items():
                for connection in connections:
                    if not isinstance(connection, tuple):
                        print(f"Error en la conexión: {key} a {connection}, que no es una tupla.")


        # Crear semáforos verdes en el camino
        traffic_lights_positions = [(11, 0), (11, 1), (16, 4), (16, 5), (21, 8), (21, 9), (2, 10), (2, 11), (7, 16), (7, 17), (16, 22), (16, 23)]
        for pos in traffic_lights_positions:
            traffic_light = TrafficLightAgent(self.next_id(), self, pos, 'green')
            self.grid.place_agent(traffic_light, pos)
            self.schedule.add(traffic_light)
        
        # Crear semáforos rojos en el camino
        traffic_lights_positions = [(12, 2), (13, 2), (14, 3), (15, 3), (22, 7), (23, 7), (0, 12), (1, 12), (5, 15), (6, 15), (14, 21), (15, 21)]
        for pos in traffic_lights_positions:
            traffic_light = TrafficLightAgent(self.next_id(), self, pos, 'red')
            self.grid.place_agent(traffic_light, pos)
            self.schedule.add(traffic_light)
        
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


        self.place_parkings([(2, 6), (5, 3), (8, 3), (17, 6), (19, 6), (19, 3), (16, 13), (21, 14), (20, 19), (17, 20), (4, 13), (11, 13), (8, 15), (6,18), (2, 20), (9, 21), (11, 19)])
        
        self.place_roundabouts([(13, 9), (13, 10), (14, 9), (14, 10)])
        
        #self.send_car_positions_to_server()
        #self.send_static_agent_positions_to_server()


    # Generar un coche en cada estacionamiento al inicio de la simulación
        for parking_agent in self.parking_agents:
            car = Car(self.next_id(), self, parking_agent)
            if car.destination_parking:
                self.grid.place_agent(car, parking_agent.pos)
                self.schedule.add(car)

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
            self.parking_agents.append(parking)
    
    def place_roundabouts(self, positions):
        for x, y in positions:
            roundabout = Roundabout(self.next_id(), self)
            self.grid.place_agent(roundabout, (x, y))
            self.schedule.add(roundabout)


    def next_id(self):
        self.current_id += 1
        return self.current_id
    
    def is_red_light(self, pos):
        if isinstance(pos, tuple) and len(pos) == 2:
            cell_contents = self.grid.get_cell_list_contents([pos])
            traffic_lights = [agent for agent in cell_contents if isinstance(agent, TrafficLightAgent)]
            return any(light.state == 'red' for light in traffic_lights)
        else:
            # Manejar el caso en que pos no es una tupla de coordenadas válidas
            return False
       
    def send_car_positions_to_server(self):
            positions_data = {f"car_{car_agent.unique_id}": [car_agent.pos[0], car_agent.pos[1]] for car_agent in self.schedule.agents if isinstance(car_agent, Car)}
            requests.post("http://127.0.0.1:5000/update_car_positions", json=positions_data)
    
    def send_static_agent_positions_to_server(self):
        static_positions_data = {}
        
        for agent in self.schedule.agents:
            if isinstance(agent, (Parking, Roundabout, TrafficLightAgent, Building)):
                agent_type = type(agent).__name__.lower()
                static_positions_data[f"{agent_type}_{agent.unique_id}"] = [agent.pos[0], agent.pos[1]]

        requests.post("http://127.0.0.1:5000/update_static_agent_positions", json=static_positions_data)
        
    def step(self):
        self.schedule.step()
        self.step_count += 1  # Incrementar el contador de pasos en cada llamada a step

        # Condición de finalización: terminar después de 100 pasos
        if self.step_count >= 100:
            self.running = False
       
        self.send_car_positions_to_server()  # Añadir esta línea al final de step

# Incializamos el servidor y el modelo
city_model = City(24, 24)
while city_model.running:
  city_model.step()

def agent_portrayal(agent):
   if isinstance(agent, Car):
       portrayal = {"Shape": "circle", "Filled": "true", "Layer": 0, "Color": "pink", "r": 0.5}
   elif isinstance(agent, Parking):
       portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": "yellow", "w": 1, "h": 1}
   elif isinstance(agent, Roundabout):
       portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": "brown", "w": 1, "h": 1}
   elif isinstance(agent, TrafficLightAgent):
       portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": "red" if agent.state == 'red' else "green", "w": 1, "h": 1}
   elif isinstance(agent, Building):
       portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": "blue", "w": 1, "h": 1}
   return portrayal


grid = CanvasGrid(agent_portrayal, 24, 24, 500, 500)

server = ModularServer(City,
                     [grid], 
                     "City Simulation",
                     {"width": 24, "height": 24})  


server.port = 8521  # Puerto por defecto
server.launch()