using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json.Linq;

public class AASActuatorController : MonoBehaviour
{
    private string pinsUrl;
    private string behaviorUrl;
    private float pollInterval = 0.05f; // 20Hz

    [Serializable]
    public class ActuatorBinding
    {
        public string pinId;
        public GameObject target;
        public string type;
        public Vector3 axis;
        public float speed;
        public float limitMin;
        public float limitMax;
        public bool currentState;
        
        // Internal state for interpolation/fixed movement
        public Vector3 initialPosition;
        public Quaternion initialRotation;
        public Vector2 currentOffset; // For texture animation
    }

    private List<ActuatorBinding> bindings = new List<ActuatorBinding>();
    private bool isInitialized = false;

    // --- NEW: Physics for Conveyors ---
    public class ConveyorSurface : MonoBehaviour {
        public HashSet<Rigidbody> touching = new HashSet<Rigidbody>();

        void OnCollisionEnter(Collision c) { 
            if(c.rigidbody != null && !c.rigidbody.isKinematic) touching.Add(c.rigidbody);
        }
        void OnCollisionStay(Collision c) { 
            if(c.rigidbody != null && !c.rigidbody.isKinematic) touching.Add(c.rigidbody); 
        }
        void OnCollisionExit(Collision c) { 
            if(c.rigidbody != null && !c.rigidbody.isKinematic) touching.Remove(c.rigidbody);
        }

        void OnTriggerEnter(Collider other) {
            if (other.attachedRigidbody != null && !other.attachedRigidbody.isKinematic) touching.Add(other.attachedRigidbody);
        }

        void OnTriggerExit(Collider other) {
            if (other.attachedRigidbody != null && !other.attachedRigidbody.isKinematic) touching.Remove(other.attachedRigidbody);
        }
    }

    public void Init(string serverUrl, string pinsSubmodelId, string behaviorSubmodelId, Dictionary<string, GameObject> componentMap)
    {
        this.pinsUrl = $"{serverUrl}/submodels/{Base64Url(pinsSubmodelId)}/submodel-elements/Inputs";
        this.behaviorUrl = $"{serverUrl}/submodels/{Base64Url(behaviorSubmodelId)}/submodel-elements";
        Debug.Log($"[Actuator] 🌐 Init with PinsURL: {pinsUrl}");
        
        StartCoroutine(LoadBindingsRoutine(componentMap));
    }

    IEnumerator LoadBindingsRoutine(Dictionary<string, GameObject> componentMap)
    {
        Debug.Log($"[Actuator] 📥 Loading behaviors from: {behaviorUrl}");
        UnityWebRequest req = UnityWebRequest.Get(behaviorUrl + "?level=deep");
        yield return req.SendWebRequest();

        if (req.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("[Actuator] ✅ Behaviors loaded successfully.");
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
                    Vector3 axis = Vector3.forward;
                    float speed = 1f;
                    float min = 0f, max = 0f;

                    foreach (var val in values)
                    {
                        string id = val["idShort"]?.ToString();
                        if (id == "Component") compName = val["value"]?.ToString();
                        if (id == "Type") type = val["value"]?.ToString();
                        if (id == "Parameters" && val["value"] != null)
                        {
                            Debug.Log($"[Actuator] 🔍 Parsing parameters for {pinId}. Token: {val.ToString(Newtonsoft.Json.Formatting.None)}");
                            foreach (var p in val["value"])
                            {
                                string pid = p["idShort"]?.ToString();
                                float fv = 0f;
                                if (p["value"] != null) {
                                    string strVal = p["value"].ToString().Replace(',', '.');
                                    bool parsed = float.TryParse(strVal, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out fv);
                                    Debug.Log($"[Actuator]   -> Param: {pid}, Raw: '{strVal}', Parsed: {parsed}, Value: {fv}");
                                } else {
                                    Debug.Log($"[Actuator]   -> Param: {pid} has NULL value.");
                                }
                                if (pid == "AxisX") axis.x = fv;
                                if (pid == "AxisY") axis.y = fv;
                                if (pid == "AxisZ") axis.z = fv;
                                if (pid == "Speed") speed = fv;
                                if (pid == "LimitMin") min = fv;
                                if (pid == "LimitMax") max = fv;
                            }
                        }
                    }

                    Debug.Log($"[Actuator] 🏁 Finished parsing {pinId}: Speed={speed}, Axis={axis}");

                    if (componentMap.TryGetValue(compName, out GameObject target) && !string.IsNullOrEmpty(type))
                    {
                        Vector3 unityAxis = new Vector3(-axis.y, axis.z, axis.x).normalized;
                        var binding = new ActuatorBinding {
                            pinId = pinId, target = target, type = type, axis = unityAxis,
                            speed = speed, limitMin = min, limitMax = max,
                            initialPosition = target.transform.localPosition,
                            initialRotation = target.transform.localRotation
                        };
                        bindings.Add(binding);

                        if (type == "Conveyor") {
                            // Ensure the object has a collider for the surface
                            if (target.GetComponentInChildren<Collider>() == null) {
                                var box = target.AddComponent<BoxCollider>();
                                box.isTrigger = false;
                                Debug.Log($"[Actuator] ➕ Added BoxCollider to {compName} for Conveyor physics.");
                            }
                            
                            // Attach surface to all parts of the conveyor that have colliders
                            foreach (var col in target.GetComponentsInChildren<Collider>()) {
                                // Unity requires at least one Rigidbody in a collision pair.
                                // If the conveyor part doesn't have one, add a kinematic one.
                                if (col.gameObject.GetComponent<Rigidbody>() == null) {
                                    var rb = col.gameObject.AddComponent<Rigidbody>();
                                    rb.isKinematic = true;
                                }

                                var surf = col.gameObject.GetComponent<ConveyorSurface>() ?? col.gameObject.AddComponent<ConveyorSurface>();
                            }
                            
                            Debug.Log($"[Actuator] ⚙️ Bound {pinId} to {compName} (Conveyor Physics on meshes)");
                        } else {
                            Debug.Log($"[Actuator] ⚙️ Bound {pinId} to {compName} ({type})");
                        }
                    }
                    else {
                        Debug.LogWarning($"[Actuator] ⚠️ Failed to bind {pinId}. Component found? {componentMap.ContainsKey(compName)} Type? {type}");
                    }
                }
            }
            isInitialized = true;
            Debug.Log($"[Actuator] 🚀 Polling started. Interval: {pollInterval}s");
            StartCoroutine(PollingLoop());
        }
        else {
            Debug.LogError($"[Actuator] ❌ Failed to load behaviors: {req.error}");
        }
    }

    IEnumerator PollingLoop()
    {
        while (true)
        {
            UnityWebRequest req = UnityWebRequest.Get(pinsUrl + "?level=deep");
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                JToken root = JToken.Parse(req.downloadHandler.text);
                JArray elements = null;
                
                if (root is JObject obj) {
                    if (obj["result"] != null) elements = obj["result"] as JArray;
                    else if (obj["value"] != null) elements = obj["value"] as JArray;
                    else {
                        // Single element fallback (if URL points directly to a property, though here it points to a collection)
                        elements = new JArray { root };
                    }
                } else if (root is JArray arr) {
                    elements = arr;
                }
                
                if (elements != null)
                {
                    foreach (var el in elements)
                    {
                        string pid = el["idShort"]?.ToString();
                        bool val = false;
                        if (el["value"] != null) bool.TryParse(el["value"].ToString(), out val);
                        
                        var b = bindings.Find(x => x.pinId == pid);
                        if (b != null) {
                            if (val != b.currentState) {
                                Debug.Log($"[Actuator] 🔄 Pin {pid} changed: {b.currentState} -> {val}");
                            }
                            b.currentState = val;
                        }
                    }
                }
            }
            else {
                Debug.LogWarning($"[Actuator] ⚠️ Polling failed: {req.error} at {pinsUrl}");
            }
            yield return new WaitForSeconds(pollInterval);
        }
    }

    void FixedUpdate() 
    {
        if (!isInitialized) return;

        foreach (var b in bindings)
        {
            if (b.target == null || !b.currentState) continue;

            if (b.type == "Conveyor") {
                var surfaces = b.target.GetComponentsInChildren<ConveyorSurface>();
                Vector3 worldDir = b.target.transform.TransformDirection(b.axis);
                Vector3 targetVel = worldDir * b.speed;
                
                foreach (var surf in surfaces) {
                    // Remove destroyed objects from hashset
                    surf.touching.RemoveWhere(rb => rb == null);
                    
                    foreach (var rb in surf.touching) {
                        // Apply surface velocity directly, preserving gravity (y-axis)
                        rb.linearVelocity = new Vector3(targetVel.x, rb.linearVelocity.y, targetVel.z);
                    }
                }
            }
        }
    }

    void Update()
    {
        if (!isInitialized) return;

        foreach (var b in bindings)
        {
            if (b.target == null) continue;

            switch (b.type)
            {
                case "TranslateContinuous":
                    if (b.currentState) b.target.transform.Translate(b.axis * b.speed * Time.deltaTime, Space.Self);
                    break;
                case "RotateContinuous":
                    if (b.currentState) b.target.transform.Rotate(b.axis, b.speed * Time.deltaTime * 100f, Space.Self);
                    break;
                case "TranslateFixed":
                    Vector3 targetPos = b.initialPosition + (b.axis * (b.currentState ? b.limitMax : b.limitMin));
                    b.target.transform.localPosition = Vector3.Lerp(b.target.transform.localPosition, targetPos, Time.deltaTime * b.speed * 5f);
                    break;
                case "RotateHinge":
                    float targetAngle = b.currentState ? b.limitMax : b.limitMin;
                    Quaternion targetRot = b.initialRotation * Quaternion.AngleAxis(targetAngle, b.axis);
                    b.target.transform.localRotation = Quaternion.Slerp(b.target.transform.localRotation, targetRot, Time.deltaTime * b.speed * 5f);
                    break;
            }
        }
    }

    string Base64Url(string i) => Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');
}