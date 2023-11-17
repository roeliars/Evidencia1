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
public class StaticAgentPosition
{
    public string id;
    public float[] position;
}

[System.Serializable]
public class StaticAgentPositionList
{
    public StaticAgentPosition[] positions;
}

public class AgentPositionUpdater : MonoBehaviour
{
    // Creamos un diccionario para almacenar los GameObjects de los agentes Car
    private Dictionary<string, GameObject> carObjects = new Dictionary<string, GameObject>();
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
        StartCoroutine(GetAgentPositions());
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
                        print("Car ID: " + carPos.id + " Position: " + carObject.transform.position);

                    }
                }
            }
            yield return new WaitForSeconds(0.001f); // Tiempo de delay
        }
    }
}
