from flask import Flask, request, jsonify

app = Flask(__name__)

# Almacenamos los datos de posición de los agentes
agent_positions = {}
traffic_light_states = {}

@app.route('/update_car_positions', methods=['POST'])
def update_car_positions():
    data = request.json
    agent_positions.update(data)
    return jsonify({"status": "success"})

@app.route('/get_car_positions', methods=['GET'])
def get_car_positions():
    # Convertirmos el diccionario en una lista de objetos para que Unity pueda procesarlo
    positions_list = [{"id": key, "position": value} for key, value in agent_positions.items()]
    return jsonify(positions_list)

@app.route('/get_traffic_light_states', methods=['GET'])
def get_traffic_light_states():
    states_list = [{"id": key, "state": value["state"]} for key, value in traffic_light_states.items()]
    return jsonify(states_list)

@app.route('/get_traffic_light_positions', methods=['GET'])
def get_traffic_light_positions():
    positions_list = [{"id": key, "position": value["position"]} for key, value in traffic_light_states.items()]
    return jsonify(positions_list)

@app.route('/update_traffic_light_states', methods=['POST'])
def update_traffic_light_states():
    states = request.json
    for key, data in states.items():
        if key in traffic_light_states:
            traffic_light_states[key]["state"] = data["state"]
    return jsonify({"status": "states updated"})

@app.route('/set_traffic_light_positions', methods=['POST'])
def set_traffic_light_positions():
    positions = request.json
    for key, position in positions.items():
        traffic_light_states[key] = {"position": position, "state": "red"}  # Estado inicial
    return jsonify({"status": "positions set"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
