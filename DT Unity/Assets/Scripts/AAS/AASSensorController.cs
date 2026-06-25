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
        public bool visible = true;
        
        public string snapTarget;
        public Vector3 snapPosition;
        public bool hasSnap;
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

        // Pass 1: Global cleanup - Hide ALL meshes named "TriggerZone" across all instantiated models
        // This ensures duplicated static meshes are always hidden regardless of active sensor bindings.
        foreach (var kvp in componentMap)
        {
            var allTransforms = kvp.Value.GetComponentsInChildren<Transform>(true);
            foreach (var t in allTransforms)
            {
                if (t.name.Contains("TriggerZone"))
                {
                    var renderer = t.GetComponent<Renderer>();
                    if (renderer != null) renderer.enabled = false;
                }
            }
        }

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
                    bool? visibleParam = null;
                    string snapTarget = null;
                    Vector3 snapPos = Vector3.zero;
                    bool hasSnap = false;

                    foreach (var val in values)
                    {
                        string id = val["idShort"]?.ToString();
                        if (id == "PinID") pinId = val["value"]?.ToString();
                        if (id == "Component") compName = val["value"]?.ToString();
                        if (id == "Type") type = val["value"]?.ToString();
                        if (id == "Parameters" && val["value"] != null)
                        {
                            foreach (var p in val["value"])
                            {
                                string pid = p["idShort"]?.ToString();
                                if (pid == "TargetFilter") filter = p["value"]?.ToString();
                                if (pid == "ActiveLow") activeLow = p["value"]?.ToString().ToLower() == "true";
                                if (pid == "Visible") visibleParam = p["value"]?.ToString().ToLower() == "true";
                                if (pid == "SnapTarget") { snapTarget = p["value"]?.ToString(); hasSnap = true; }
                                
                                float fv = 0f;
                                if (p["value"] != null) float.TryParse(p["value"].ToString().Replace(',', '.'), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out fv);
                                if (pid == "SnapPosX") snapPos.x = fv;
                                if (pid == "SnapPosY") snapPos.y = fv;
                                if (pid == "SnapPosZ") snapPos.z = fv;
                            }
                        }
                    }

                    bool visible = visibleParam.HasValue ? visibleParam.Value : (type != "TriggerZone");

                    if (!string.IsNullOrEmpty(compName))
                    {
                        GameObject target = null;
                        
                        // First, check if there's an exact match in the component map
                        if (DirectTargetMatch(componentMap, compName, out target)) {
                            // target found
                        } else {
                            // If not, search across ALL imported components for this child (e.g., "TriggerZone")
                            foreach (var rootObj in componentMap.Values)
                            {
                                var allTransforms = rootObj.GetComponentsInChildren<Transform>(true);
                                foreach(var t in allTransforms) {
                                    if(t.name == compName) {
                                        target = t.gameObject;
                                        break;
                                    }
                                }
                                if (target != null) break;
                            }
                        }

                        if (target != null && (type == "TriggerZone" || type == "ContactSensor"))
                        {
                            var binding = new SensorBinding {
                                pinId = pinId,
                                componentName = compName,
                                type = type,
                                targetFilter = filter,
                                activeLow = activeLow,
                                visible = visible,
                                snapTarget = snapTarget,
                                snapPosition = snapPos,
                                hasSnap = hasSnap
                            };
                            componentToSensor[compName] = binding;
                            
                            // Setup Unity Physics Proxy
                            var proxy = target.AddComponent<SensorPhysicsProxy>();
                            proxy.binding = binding;
                            proxy.onStateChange += (state) => StartCoroutine(UpdateAASPin(binding, state));

                            // IMPORTANT: Sensors need a Rigidbody (Kinematic) to guarantee trigger events
                            if (target.GetComponent<Rigidbody>() == null) {
                                var rb = target.AddComponent<Rigidbody>();
                                rb.isKinematic = true;
                                rb.useGravity = false;
                            }

                            // Ensure collider is set correctly
                            var colliders = target.GetComponentsInChildren<Collider>();
                            if (colliders.Length == 0) {
                                var box = target.AddComponent<BoxCollider>();
                                box.isTrigger = (type == "TriggerZone");
                            }

                            foreach (var c in target.GetComponentsInChildren<Collider>())
                            {
                                if (type == "TriggerZone") 
                                {
                                    c.isTrigger = true;
                                }
                            }

                            // Auto-hide or show the sensor mesh based on visibility
                            foreach (var renderer in target.GetComponentsInChildren<Renderer>())
                            {
                                renderer.enabled = binding.visible;
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

    private bool DirectTargetMatch(Dictionary<string, GameObject> map, string name, out GameObject target) {
        if (map.TryGetValue(name, out target)) return true;
        foreach (var kvp in map) {
            Transform child = kvp.Value.transform.Find(name);
            if (child != null) { target = child.gameObject; return true; }
        }
        return false;
    }

    IEnumerator UpdateAASPin(SensorBinding binding, bool state)
    {
        string pinId = binding.pinId;
        Debug.Log($"[Sensor] 📡 Updating {pinId} to {state}");

        // --- SNAP / TELEPORT LOGIC ---
        // If the sensor real signal becomes TRUE and has a Snap configuration,
        // we force the target object to the specified position.
        if (state && binding.hasSnap && !string.IsNullOrEmpty(binding.snapTarget))
        {
            GameObject product = GameObject.Find(binding.snapTarget);
            if (product != null)
            {
                // Mapping SnapPosition (Z-up) to Unity (Y-up)
                Vector3 unityPos = new Vector3(binding.snapPosition.x, binding.snapPosition.z, binding.snapPosition.y);
                product.transform.localPosition = unityPos;
                
                // Reset velocity to avoid physical "bouncing" after teleport
                var rb = product.GetComponent<Rigidbody>();
                if (rb != null) {
                    rb.linearVelocity = Vector3.zero;
                    rb.angularVelocity = Vector3.zero;
                }
                
                Debug.Log($"[Sensor] ⚡ SNAP! Teleported {binding.snapTarget} to {unityPos} via {pinId}");
            }
        }

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
                Debug.LogWarning($"[Sensor] ❌ Failed to update {pinId}: {req.error} (URL: {url})");
        }
    }

    // Helper class to be attached to each sensor component
    public class SensorPhysicsProxy : MonoBehaviour
    {
        public SensorBinding binding;
        public Action<bool> onStateChange;
        public HashSet<Collider> touching = new HashSet<Collider>();

        void Start() {
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
            
            string n = other.gameObject.name;
            string t = other.gameObject.tag;
            string filter = binding.targetFilter;

            bool nameMatch = n.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0;
            bool tagMatch = t.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0;
            
            bool parentMatch = false;
            Transform p = other.transform.parent;
            while(p != null) {
                if(p.name.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0) {
                    parentMatch = true;
                    break;
                }
                p = p.parent;
            }

            return nameMatch || tagMatch || parentMatch;
        }

        private void CheckState(bool force = false)
        {
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