using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json.Linq;

public class AASSensorController : MonoBehaviour
{
    private string pinsUrl;
    private string behaviorUrl;

    [Serializable]
    public class SensorBinding
    {
        public string pinId;
        public string componentName;
        public string type;
        public string targetFilter;
        public bool lastState = false;
        public int overlapCount = 0; // For TriggerZone
    }

    private Dictionary<string, SensorBinding> componentToSensor = new Dictionary<string, SensorBinding>();

    public void Init(string serverUrl, string pinsSubmodelId, string behaviorSubmodelId, Dictionary<string, GameObject> componentMap)
    {
        this.pinsUrl = $"{serverUrl}/submodels/{Base64Url(pinsSubmodelId)}/submodel-elements/Outputs";
        this.behaviorUrl = $"{serverUrl}/submodels/{Base64Url(behaviorSubmodelId)}/submodel-elements";
        
        StartCoroutine(LoadBindingsRoutine(componentMap));
    }

    IEnumerator LoadBindingsRoutine(Dictionary<string, GameObject> componentMap)
    {
        UnityWebRequest req = UnityWebRequest.Get(behaviorUrl + "?level=deep");
        yield return req.SendWebRequest();

        if (req.result == UnityWebRequest.Result.Success)
        {
            JToken root = JToken.Parse(req.downloadHandler.text);
            JArray elements = (root is JObject obj && obj["result"] != null) ? obj["result"] as JArray : root as JArray;

            if (elements != null)
            {
                foreach (var el in elements)
                {
                    string pinId = el["idShort"]?.ToString();
                    JToken values = el["value"];
                    if (values == null) continue;

                    string compName = "";
                    string type = "";
                    string filter = "";

                    foreach (var val in values)
                    {
                        string id = val["idShort"]?.ToString();
                        if (id == "Component") compName = val["value"]?.ToString();
                        if (id == "Type") type = val["value"]?.ToString();
                        if (id == "Parameters" && val["value"] != null)
                        {
                            foreach (var p in val["value"])
                            {
                                if (p["idShort"]?.ToString() == "TargetFilter") filter = p["value"]?.ToString();
                            }
                        }
                    }

                    if (componentMap.TryGetValue(compName, out GameObject target) && (type == "TriggerZone" || type == "ContactSensor"))
                    {
                        var binding = new SensorBinding {
                            pinId = pinId,
                            componentName = compName,
                            type = type,
                            targetFilter = filter
                        };
                        componentToSensor[compName] = binding;
                        
                        // Setup Unity Physics Proxy
                        var proxy = target.AddComponent<SensorPhysicsProxy>();
                        proxy.binding = binding;
                        proxy.onStateChange += (state) => StartCoroutine(UpdateAASPin(binding.pinId, state));

                        // Ensure collider is set correctly
                        var colliders = target.GetComponentsInChildren<Collider>();
                        foreach (var c in colliders)
                        {
                            if (type == "TriggerZone") c.isTrigger = true;
                        }

                        Debug.Log($"[Sensor] 👁️ Configured {pinId} on {compName} (Filter: {filter})");
                    }
                }
            }
        }
    }

    IEnumerator UpdateAASPin(string pinId, bool state)
    {
        string url = $"{pinsUrl}/{pinId}";
        string json = $"{{\"idShort\":\"{pinId}\",\"modelType\":\"Property\",\"valueType\":\"xs:boolean\",\"value\":\"{state.ToString().ToLower()}\"}}";
        
        using (UnityWebRequest req = new UnityWebRequest(url, "PUT"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
            req.uploadHandler = new UploadHandlerRaw(bodyRaw);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            req.timeout = 2;

            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success)
                Debug.LogWarning($"[Sensor] ❌ Failed to update {pinId}: {req.error}");
        }
    }

    // Helper class to be attached to each sensor component
    public class SensorPhysicsProxy : MonoBehaviour
    {
        public SensorBinding binding;
        public Action<bool> onStateChange;

        private void OnTriggerEnter(Collider other)
        {
            if (binding.type != "TriggerZone") return;
            if (MatchesFilter(other))
            {
                binding.overlapCount++;
                CheckState();
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (binding.type != "TriggerZone") return;
            if (MatchesFilter(other))
            {
                binding.overlapCount = Math.Max(0, binding.overlapCount - 1);
                CheckState();
            }
        }

        private void OnCollisionEnter(Collision collision)
        {
            if (binding.type != "ContactSensor") return;
            if (MatchesFilter(collision.collider))
            {
                binding.overlapCount++;
                CheckState();
            }
        }

        private void OnCollisionExit(Collision collision)
        {
            if (binding.type != "ContactSensor") return;
            if (MatchesFilter(collision.collider))
            {
                binding.overlapCount = Math.Max(0, binding.overlapCount - 1);
                CheckState();
            }
        }

        private bool MatchesFilter(Collider other)
        {
            if (string.IsNullOrEmpty(binding.targetFilter)) return true;
            return other.name.Contains(binding.targetFilter) || other.CompareTag(binding.targetFilter);
        }

        private void CheckState()
        {
            bool newState = binding.overlapCount > 0;
            if (newState != binding.lastState)
            {
                binding.lastState = newState;
                onStateChange?.Invoke(newState);
            }
        }
    }

    string Base64Url(string i) => Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');
}