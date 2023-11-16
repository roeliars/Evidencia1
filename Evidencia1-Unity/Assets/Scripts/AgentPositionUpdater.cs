using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class CarPosition
{
    public string id;
    public float[] position; // Utiliza un arreglo de float en lugar de Vector2.
}

[System.Serializable]
public class CarPositionList
{
    public CarPosition[] positions;
}

public class AgentPositionUpdater : MonoBehaviour
{
    private Dictionary<string, GameObject> carObjects = new Dictionary<string, GameObject>();

    void Start()
    {
        DontDestroyOnLoad(gameObject); // Agrega esta línea al principio del método Start
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
            UnityWebRequest www = UnityWebRequest.Get("http://127.0.0.1:5000/get_positions");
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(www.error);
            }
            else
            {
                string jsonString = www.downloadHandler.text;
                Debug.Log("Datos JSON recibidos: " + jsonString);  // Esto imprimirá el JSON crudo en la consola

                CarPositionList carPositions = JsonUtility.FromJson<CarPositionList>("{\"positions\":" + jsonString + "}");
                foreach (CarPosition carPos in carPositions.positions)
                {
                    Debug.Log("Procesando: " + carPos.id + " en posición: " + carPos.position);  // Esto imprimirá cada posición procesada

                    if (carObjects.TryGetValue(carPos.id, out GameObject carObject))
                    {
                        if (carObject == null)
                        {
                            Debug.LogError("El GameObject con ID " + carPos.id + " fue encontrado en el diccionario pero es null");
                            continue; // Salta a la próxima iteración del bucle
                        }

                        // Comprueba que haya exactamente dos elementos en el arreglo de posición.
                        if (carPos.position != null && carPos.position.Length == 2)
                        {
                            // Asigna las posiciones x y y al transform del objeto.
                            carObject.transform.position = new Vector3(carPos.position[0], 0, carPos.position[1]);
                            Debug.Log("Moviendo " + carPos.id + " a la posición: " + carObject.transform.position);
                        }
                        else
                        {
                            Debug.LogError("Array de posición incorrecto para " + carPos.id);
                        }
                    }
                    else
                    {
                        Debug.LogError("No se encontró el GameObject para " + carPos.id);
                    }
                }
            }

            yield return new WaitForSeconds(1f); // Ajusta este tiempo según sea necesario
        }
    }
}
