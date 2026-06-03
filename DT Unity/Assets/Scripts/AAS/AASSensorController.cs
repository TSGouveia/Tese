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
        public bool activeLow = false; // Added for Active Low support
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
                    bool activeLow = false;

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
                                if (p["idShort"]?.ToString() == "ActiveLow") activeLow = p["value"]?.ToString().ToLower() == "true";
                            }
                        }
                    }

                    if (!string.IsNullOrEmpty(compName))
                    {
                        GameObject target = null;
                        foreach (var kvp in componentMap)
                        {
                            if (kvp.Key == compName) { target = kvp.Value; break; }
                            
                            // Search children if it's a sub-mesh (like TriggerZone inside Conveyor.glb)
                            Transform child = kvp.Value.transform.Find(compName);
                            if (child == null) {
                                // Deep search
                                var allTransforms = kvp.Value.GetComponentsInChildren<Transform>(true);
                                foreach(var t in allTransforms) {
                                    if(t.name == compName) { child = t; break; }
                                }
                            }
                            if (child != null) { target = child.gameObject; break; }
                        }

                        if (target != null && (type == "TriggerZone" || type == "ContactSensor"))
                        {
                            var binding = new SensorBinding {
                                pinId = pinId,
                                componentName = compName,
                                type = type,
                                targetFilter = filter,
                                activeLow = activeLow
                            };
                            componentToSensor[compName] = binding;
                            
                            // Setup Unity Physics Proxy
                            var proxy = target.AddComponent<SensorPhysicsProxy>();
                            proxy.binding = binding;
                            proxy.onStateChange += (state) => StartCoroutine(UpdateAASPin(binding.pinId, state));

                            // Ensure collider is set correctly and hide the mesh for TriggerZones
                            var colliders = target.GetComponentsInChildren<Collider>();
                            if (colliders.Length == 0) {
                                // If it's just an empty mesh node, add a box collider
                                var box = target.AddComponent<BoxCollider>();
                                box.isTrigger = (type == "TriggerZone");
                            }

                            foreach (var c in target.GetComponentsInChildren<Collider>())
                            {
                                if (type == "TriggerZone") 
                                {
                                    c.isTrigger = true;
                                    
                                    // Auto-hide the trigger zone mesh
                                    var renderer = c.GetComponent<Renderer>();
                                    if (renderer != null) renderer.enabled = false;
                                }
                            }

                            Debug.Log($"[Sensor] 👁️ Configured {pinId} on {compName} (Filter: {filter})");
                        }
                        else if (target == null)
                        {
                            Debug.LogWarning($"[Sensor] ⚠️ Could not find component '{compName}' in the model to attach sensor '{pinId}'.");
                        }
                    }
                }
            }
        }
    }

    IEnumerator UpdateAASPin(string pinId, bool state)
    {
        // BaSyx 2.0 requires dot notation for nested elements inside collections
        string url = $"{pinsUrl}.{pinId}";
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
        public HashSet<Collider> touching = new HashSet<Collider>();

        void Start() {
            // Force initial state sync (especially important for activeLow sensors which start as 'true' when nothing is touching)
            CheckState(true);
        }

        private void OnTriggerEnter(Collider other)
        {
            if (binding.type != "TriggerZone") return;
            if (MatchesFilter(other))
            {
                touching.Add(other);
                CheckState();
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (binding.type != "TriggerZone") return;
            if (MatchesFilter(other))
            {
                touching.Remove(other);
                CheckState();
            }
        }

        private void OnCollisionEnter(Collision collision)
        {
            if (binding.type != "ContactSensor") return;
            if (MatchesFilter(collision.collider))
            {
                touching.Add(collision.collider);
                CheckState();
            }
        }

        private void OnCollisionExit(Collision collision)
        {
            if (binding.type != "ContactSensor") return;
            if (MatchesFilter(collision.collider))
            {
                touching.Remove(collision.collider);
                CheckState();
            }
        }

        private bool MatchesFilter(Collider other)
        {
            if (string.IsNullOrEmpty(binding.targetFilter)) return true;
            
            // Exclusively check if the name contains the filter word (case-insensitive)
            if (other.name.IndexOf(binding.targetFilter, StringComparison.OrdinalIgnoreCase) >= 0) {
                return true;
            }
            
            return false;
        }

        private void CheckState(bool force = false)
        {
            // Remove any colliders that might have been destroyed while inside the trigger
            touching.RemoveWhere(c => c == null);

            bool isOverlapping = touching.Count > 0;
            bool newState = binding.activeLow ? !isOverlapping : isOverlapping;
            
            if (force || newState != binding.lastState)
            {
                binding.lastState = newState;
                onStateChange?.Invoke(newState);
            }
        }
    }

    string Base64Url(string i) => Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');
}