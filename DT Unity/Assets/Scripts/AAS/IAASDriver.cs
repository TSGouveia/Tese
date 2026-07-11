using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Networking;

public interface IAASDriver
{
    void WriteActuator(string pinId, bool value);
    bool ReadSensor(string pinId);
}

public class AASHttpDriver : IAASDriver
{
    private AASSensorController sensorController;
    private AASActuatorController actuatorController;
    private string baseRepoUrl;
    private string virtualPinsSubmodelId;

    public AASHttpDriver(
        AASSensorController sensorController,
        AASActuatorController actuatorController,
        string baseRepoUrl,
        string virtualPinsSubmodelId)
    {
        this.sensorController = sensorController;
        this.actuatorController = actuatorController;
        this.baseRepoUrl = baseRepoUrl;
        this.virtualPinsSubmodelId = virtualPinsSubmodelId;
    }

    public void WriteActuator(string pinId, bool value)
    {
        if (actuatorController != null && actuatorController.bindings != null)
        {
            var binding = actuatorController.bindings.Find(b => b.pinId == pinId);
            if (binding != null)
            {
                binding.currentState = value;
            }
            else
            {
                Debug.LogWarning($"[AASHttpDriver] Actuator with pinId '{pinId}' not found in bindings.");
            }
        }
        else
        {
            Debug.LogWarning("[AASHttpDriver] ActuatorController or its bindings list is null.");
        }

        // Send asynchronous HTTP PUT request
        StaticCoroutineRunner.Start(UpdateActuatorAAS(pinId, value));
    }

    public bool ReadSensor(string pinId)
    {
        // 1. Try to find it in the sensorController via reflection (private componentToSensor dictionary)
        if (sensorController != null)
        {
            try
            {
                var field = typeof(AASSensorController).GetField("componentToSensor", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (field != null)
                {
                    var dict = field.GetValue(sensorController) as Dictionary<string, AASSensorController.SensorBinding>;
                    if (dict != null)
                    {
                        foreach (var kvp in dict.Values)
                        {
                            if (kvp != null && kvp.pinId == pinId)
                            {
                                return kvp.lastState;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[AASHttpDriver] Reflection failed: {ex.Message}");
            }
        }

        // 2. Fallback: Search the scene for SensorPhysicsProxy with matching pinId
        var proxies = UnityEngine.Object.FindObjectsByType<AASSensorController.SensorPhysicsProxy>(FindObjectsSortMode.None);
        foreach (var proxy in proxies)
        {
            if (proxy != null && proxy.binding != null && proxy.binding.pinId == pinId)
            {
                return proxy.binding.lastState;
            }
        }

        Debug.LogWarning($"[AASHttpDriver] Sensor with pinId '{pinId}' not found!");
        return false;
    }

    private IEnumerator UpdateActuatorAAS(string pinId, bool value)
    {
        string base64SubmodelId = Base64Url(virtualPinsSubmodelId);
        string url = $"{baseRepoUrl}/submodels/{base64SubmodelId}/submodel-elements/Inputs.{pinId}";
        string json = $"{{\"idShort\":\"{pinId}\",\"modelType\":\"Property\",\"valueType\":\"xs:boolean\",\"value\":\"{value.ToString().ToLower()}\"}}";

        using (UnityWebRequest req = new UnityWebRequest(url, "PUT"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            req.timeout = 2;

            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning($"[AASHttpDriver] ❌ Failed to write actuator {pinId}: {req.error} (URL: {url})");
            }
        }
    }

    private string Base64Url(string i)
    {
        if (string.IsNullOrEmpty(i)) return "";
        return Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(i))
            .Replace("+", "-")
            .Replace("/", "_")
            .TrimEnd('=');
    }
}

public class StaticCoroutineRunner : MonoBehaviour
{
    private static StaticCoroutineRunner instance;

    public static StaticCoroutineRunner Instance
    {
        get
        {
            if (instance == null)
            {
                GameObject go = new GameObject("StaticCoroutineRunner");
                instance = go.AddComponent<StaticCoroutineRunner>();
                DontDestroyOnLoad(go);
            }
            return instance;
        }
    }

    public static Coroutine Start(IEnumerator routine)
    {
        return Instance.StartCoroutine(routine);
    }
}
