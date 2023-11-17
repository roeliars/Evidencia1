from flask import Flask, request, jsonify

app = Flask(__name__)

# Almacenamos los datos de posición de los agentes
agent_positions = {}

@app.route('/update_car_positions', methods=['POST'])
def update_positions():
    data = request.json
    agent_positions.update(data)
    return jsonify({"status": "success"})

@app.route('/get_car_positions', methods=['GET'])
def get_positions():
    # Convertirmos el diccionario en una lista de objetos para que Unity pueda procesarlo
    positions_list = [{"id": key, "position": value} for key, value in agent_positions.items()]
    return jsonify(positions_list)

@app.route('/update_agents_positions', methods=['POST'])
def update_static_positions():
    data = request.json
    agent_positions.update(data)
    return jsonify({"status": "success"})

@app.route('/get_agents_positions', methods=['GET'])
def get_static_positions():
    # Filtramos solo los agentes que no sean Car
    static_positions = {key: value for key, value in agent_positions.items() if not key.startswith('car_')}
    positions_list = [{"id": key, "position": value} for key, value in static_positions.items()]
    return jsonify(positions_list)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
