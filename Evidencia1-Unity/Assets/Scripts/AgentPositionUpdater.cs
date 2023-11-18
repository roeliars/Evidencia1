using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class CarPosition
{
    public string id;
    public float[] position; 
}

[System.Serializable]
public class CarPositionList
{
    public CarPosition[] positions;
}


[System.Serializable]
public class TrafficLightPosition
{
    public string id;
    public float[] position; 
}

[System.Serializable]
public class TrafficLightList
{
    public TrafficLightPosition[] trafficLights;
}

[System.Serializable]
public class TrafficLightState
{
    public string id;
    public string state; // "red" o "green"
}

[System.Serializable]
public class TrafficLightStateList
{
    public TrafficLightState[] trafficLights;
}

public class AgentPositionUpdater : MonoBehaviour
{
    // Creamos un diccionario para almacenar los GameObjects de los agentes Car y TrafficLight
    private Dictionary<string, GameObject> carObjects = new Dictionary<string, GameObject>();
    private Dictionary<string, GameObject> trafficLightObjects = new Dictionary<string, GameObject>();

    public Material redMaterial; 
    public Material greenMaterial;

    void Start()
    {
        DontDestroyOnLoad(gameObject); // Asegúrate de que este GameObject persista entre escenas

        // Cargar GameObjects de coches
        for (int i = 205; i <= 222; i++)
        {
            string carId = "car_" + i;
            GameObject carObject = GameObject.Find(carId);
            if (carObject != null)
            {
                carObjects[carId] = carObject;
            }
        }
        
        for (int i = 1; i <= 25; i++)
        {
            string trafficLightId = "traffic_light_" + i;
            GameObject trafficLightObject = GameObject.Find(trafficLightId);
            if (trafficLightObject != null)
            {
                trafficLightObjects[trafficLightId] = trafficLightObject;
            }
        }
        StartCoroutine(GetAgentPositions());
        StartCoroutine(SetInitialTrafficLightPositions());
        StartCoroutine(UpdateTrafficLightStates());
    }

    IEnumerator GetAgentPositions()
    {
        while (true)
        {
            // Obtenemos y actualizamos las posiciones de coches
            UnityWebRequest www = UnityWebRequest.Get("http://127.0.0.1:5000/get_car_positions");
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(www.error);
            }
            else
            {
                string jsonString = www.downloadHandler.text;
                CarPositionList carPositions = JsonUtility.FromJson<CarPositionList>("{\"positions\":" + jsonString + "}");
                foreach (CarPosition carPos in carPositions.positions)
                {
                    if (carObjects.TryGetValue(carPos.id, out GameObject carObject) && carObject != null && carPos.position != null && carPos.position.Length == 2)
                    {
                        carObject.transform.position = new Vector3(carPos.position[0], 0, carPos.position[1]);
                    }
                }
            }
            yield return new WaitForSeconds(1); // Tiempo de delay
        }
    }
    IEnumerator SetInitialTrafficLightPositions()
    {
        UnityWebRequest www = UnityWebRequest.Get("http://127.0.0.1:5000/get_traffic_light_positions");
        yield return www.SendWebRequest();

        if (www.result != UnityWebRequest.Result.Success)
        {
            Debug.Log(www.error);
        }
        else
        {
            string jsonString = www.downloadHandler.text;
            TrafficLightList trafficLightList = JsonUtility.FromJson<TrafficLightList>("{\"trafficLights\":" + jsonString + "}");
            foreach (TrafficLightPosition trafficLightPos in trafficLightList.trafficLights)
            {
                if (trafficLightObjects.TryGetValue(trafficLightPos.id, out GameObject trafficLightObject) && trafficLightObject != null && trafficLightPos.position != null && trafficLightPos.position.Length == 2)
                {
                    trafficLightObject.transform.position = new Vector3(trafficLightPos.position[0], 0, trafficLightPos.position[1]);
                }
            }
        }
    }

    IEnumerator UpdateTrafficLightStates()
    {
        while (true)
        {
            UnityWebRequest www = UnityWebRequest.Get("http://127.0.0.1:5000/get_traffic_light_states");
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(www.error);
            }
            else
            {
                string jsonString = www.downloadHandler.text;
                TrafficLightStateList trafficLightStates = JsonUtility.FromJson<TrafficLightStateList>("{\"trafficLights\":" + jsonString + "}");
                foreach (TrafficLightState trafficLightState in trafficLightStates.trafficLights)
                {
                    if (trafficLightObjects.TryGetValue(trafficLightState.id, out GameObject trafficLightObject) && trafficLightObject != null)
                    {
                        Renderer renderer = trafficLightObject.GetComponent<Renderer>();
                        if (renderer != null)
                        {
                            Material colorMaterial = (trafficLightState.state == "red") ? redMaterial : greenMaterial;
                            renderer.material = colorMaterial;
                        }
                    }
                }
            }
            yield return new WaitForSeconds(1); // Tiempo de delay
        }
    }
}
