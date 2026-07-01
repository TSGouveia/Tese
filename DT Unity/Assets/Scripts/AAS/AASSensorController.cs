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
        public float lastSnapTime = 0f; // Cooldown timer to prevent infinite re-snaps
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
                        GameObject target = FindTargetComponent(componentMap, compName);

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
                            proxy.onStateChange += (state, isOverlapping, sensorObj) => StartCoroutine(UpdateAASPin(binding, state, isOverlapping, sensorObj));

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

                            // Auto-hide or show the sensor mesh based on visibility if explicitly defined in AAS
                            if (visibleParam.HasValue)
                            {
                                foreach (var renderer in target.GetComponentsInChildren<Renderer>())
                                {
                                    renderer.enabled = visibleParam.Value;
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

    private GameObject FindTargetComponent(Dictionary<string, GameObject> map, string compName)
    {
        if (string.IsNullOrEmpty(compName)) return null;

        // 1. First priority: Exact case-sensitive match in map
        if (map.TryGetValue(compName, out GameObject directTarget)) return directTarget;

        // Collect all GameObjects and their child transforms
        List<GameObject> allObjects = new List<GameObject>();
        foreach (var rootObj in map.Values)
        {
            if (rootObj == null) continue;
            if (!allObjects.Contains(rootObj)) allObjects.Add(rootObj);
            foreach (Transform t in rootObj.GetComponentsInChildren<Transform>(true))
            {
                if (t != null && !allObjects.Contains(t.gameObject))
                {
                    allObjects.Add(t.gameObject);
                }
            }
        }

        // 2. Second priority: Exact case-insensitive match
        foreach (var obj in allObjects)
        {
            if (string.Equals(obj.name, compName, StringComparison.OrdinalIgnoreCase))
                return obj;
        }

        // 3. Third priority: Suffix/prefix match (e.g. glTF importer appends suffixes)
        string cleanComp = CleanComponentName(compName);
        foreach (var obj in allObjects)
        {
            string cleanObj = CleanComponentName(obj.name);
            if (string.Equals(cleanObj, cleanComp, StringComparison.OrdinalIgnoreCase))
                return obj;
        }

        // 4. Fourth priority: Loose containment
        foreach (var obj in allObjects)
        {
            if (obj.name.ToLower().Contains(compName.ToLower()) || compName.ToLower().Contains(obj.name.ToLower()))
                return obj;
        }

        return null;
    }

    private string CleanComponentName(string name)
    {
        if (string.IsNullOrEmpty(name)) return "";
        string clean = name;
        string[] noise = { "_mesh", "_node", "_primitive", "_instance" };
        foreach (var n in noise)
        {
            int idx = clean.ToLower().IndexOf(n);
            if (idx > 0) clean = clean.Substring(0, idx);
        }
        int dotIdx = clean.IndexOf('.');
        if (dotIdx > 0) clean = clean.Substring(0, dotIdx);
        return clean.Trim().ToLower();
    }

    IEnumerator UpdateAASPin(SensorBinding binding, bool state, bool isOverlapping, GameObject sensorObj)
    {
        string pinId = binding.pinId;
        Debug.Log($"[Sensor] 📡 Updating {pinId} to {state}");

        // --- SNAP / TELEPORT LOGIC ---
        // If the sensor has a Snap configuration and the product is physically entering (isOverlapping is true),
        // we start a coroutine to snap it after a 0.3s delay.
        // Includes a 1.5s cooldown to prevent infinite snapping while a conveyor is running
        if (isOverlapping && binding.hasSnap && (UnityEngine.Time.time - binding.lastSnapTime > 1.5f))
        {
            binding.lastSnapTime = UnityEngine.Time.time;
            StartCoroutine(SnapWithDelayRoutine(binding, sensorObj, pinId));
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

    IEnumerator SnapWithDelayRoutine(SensorBinding binding, GameObject sensorObj, string pinId)
    {
        // Wait for 0.3 seconds to let Python turn off the conveyor and let the product settle
        yield return new WaitForSeconds(0.3f);

        GameObject product = null;
        Rigidbody rb = null;

        var rbs = FindObjectsByType<Rigidbody>(FindObjectsSortMode.None);
        foreach (var r in rbs)
        {
            if (!r.isKinematic)
            {
                rb = r;
                product = r.gameObject;
                break;
            }
        }

        if (product == null && !string.IsNullOrEmpty(binding.snapTarget))
        {
            product = GameObject.Find(binding.snapTarget);
            if (product != null)
            {
                rb = product.GetComponent<Rigidbody>();
            }
        }

        if (product != null)
        {
            Vector3 unityPos;
            if (binding.snapPosition.sqrMagnitude < 0.0001f)
            {
                unityPos = new Vector3(sensorObj.transform.position.x, product.transform.position.y, sensorObj.transform.position.z);
            }
            else
            {
                unityPos = new Vector3(binding.snapPosition.x, binding.snapPosition.y, -binding.snapPosition.z);
            }
            
            float dist = Vector3.Distance(product.transform.position, unityPos);
            float angle = Quaternion.Angle(product.transform.rotation, Quaternion.Euler(0, sensorObj.transform.eulerAngles.y, 0));
            
            if (dist > 0.02f || angle > 2f)
            {
                product.transform.position = unityPos;
                
                // Also align rotation to match the sensor's orientation (along the conveyor axis)
                product.transform.rotation = Quaternion.Euler(0, sensorObj.transform.eulerAngles.y, 0);
                
                // Reset velocity to avoid physical "bouncing" after teleport
                if (rb != null) {
                    rb.linearVelocity = Vector3.zero;
                    rb.angularVelocity = Vector3.zero;
                }
                
                Debug.Log($"[Sensor] ⚡ DELAYED SNAP! Teleported dynamic product '{product.name}' to {unityPos} via {pinId} (Dist={dist:F4}, Angle={angle:F2}º)");
            }
        }
    }

    // Helper class to be attached to each sensor component
    public class SensorPhysicsProxy : MonoBehaviour
    {
        public SensorBinding binding;
        public Action<bool, bool, GameObject> onStateChange;
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
                onStateChange?.Invoke(newState, isOverlapping, this.gameObject);
            }
        }
    }

    string Base64Url(string i) => Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');
}