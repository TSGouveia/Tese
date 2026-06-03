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
        
        public Vector3 initialPosition;
        public Quaternion initialRotation;
        public Vector2 currentOffset;
    }

    public List<ActuatorBinding> bindings = new List<ActuatorBinding>();
    private bool isInitialized = false;

    private static PhysicsMaterial _noFrictionMaterial;
    private static PhysicsMaterial NoFrictionMaterial {
        get {
            if (_noFrictionMaterial == null) {
                _noFrictionMaterial = new PhysicsMaterial("NoFriction") {
                    dynamicFriction = 0f,
                    staticFriction = 0f,
                    frictionCombine = PhysicsMaterialCombine.Minimum,
                    bounceCombine = PhysicsMaterialCombine.Minimum
                };
            }
            return _noFrictionMaterial;
        }
    }

    // --- Product-Centric Movement ---
    public class ConveyorContactTracker : MonoBehaviour {
        private Rigidbody rb;
        private class ContactInfo {
            public float lastTime;
            public List<ActuatorBinding> bindings;
        }
        private Dictionary<GameObject, ContactInfo> activeContacts = new Dictionary<GameObject, ContactInfo>();

        void Awake() { rb = GetComponent<Rigidbody>(); }

        public void NotifyContact(GameObject root, List<ActuatorBinding> kitBindings) {
            if (!activeContacts.ContainsKey(root)) {
                activeContacts[root] = new ContactInfo { bindings = kitBindings };
            }
            activeContacts[root].lastTime = Time.fixedTime;
        }

        void FixedUpdate() {
            var expired = activeContacts.Where(kvp => Time.fixedTime - kvp.Value.lastTime > 0.2f).Select(kvp => kvp.Key).ToList();
            foreach (var key in expired) activeContacts.Remove(key);

            if (activeContacts.Count == 0) return;

            List<Vector3> candidateVelocities = new List<Vector3>();
            foreach (var contact in activeContacts.Values) {
                foreach (var b in contact.bindings) {
                    if (b.type == "Conveyor") {
                        Vector3 worldDir = b.target.transform.TransformDirection(b.axis);
                        Vector3 vel = b.currentState ? (worldDir * b.speed) : Vector3.zero;
                        candidateVelocities.Add(vel);
                    }
                }
            }

            Vector3 targetVel = Vector3.zero;
            var activeVels = candidateVelocities.Where(v => v.sqrMagnitude > 0.001f).ToList();

            if (activeVels.Count > 0) {
                bool opposing = false;
                for (int i = 0; i < activeVels.Count; i++) {
                    for (int j = i + 1; j < activeVels.Count; j++) {
                        if (Vector3.Dot(activeVels[i].normalized, activeVels[j].normalized) < -0.1f) {
                            opposing = true; break;
                        }
                    }
                    if (opposing) break;
                }
                if (opposing) {
                    targetVel = Vector3.zero;
                } else {
                    targetVel = activeVels[0];
                    foreach (var v in activeVels) {
                        if (v.magnitude > targetVel.magnitude) targetVel = v;
                    }
                }
            }

            Vector3 finalVel = new Vector3(targetVel.x, rb.linearVelocity.y, targetVel.z);
            if (rb.IsSleeping()) rb.WakeUp();
            rb.linearDamping = 0;

            if (finalVel.sqrMagnitude > 0.001f) {
                rb.MovePosition(rb.position + finalVel * Time.fixedDeltaTime);
            } else {
                rb.linearVelocity = new Vector3(0, rb.linearVelocity.y, 0);
            }
            foreach (var col in GetComponentsInChildren<Collider>()) col.contactOffset = 0.001f;
        }
    }

    public class ConveyorSurface : MonoBehaviour {
        public GameObject rootConveyor;
        private AASActuatorController controller;
        public void Setup(GameObject root, AASActuatorController ctrl) {
            rootConveyor = root;
            controller = ctrl;
        }
        void Start() {
            var col = GetComponent<Collider>();
            if (col != null) col.material = NoFrictionMaterial;
        }
        private void Register(GameObject other) {
            var rb = other.GetComponentInParent<Rigidbody>();
            if (rb != null && !rb.isKinematic) {
                var tracker = rb.GetComponent<ConveyorContactTracker>() ?? rb.gameObject.AddComponent<ConveyorContactTracker>();
                tracker.NotifyContact(rootConveyor, controller.bindings);
            }
        }
        void OnCollisionStay(Collision c) { Register(c.gameObject); }
        void OnTriggerStay(Collider other) { Register(other.gameObject); }
    }

    public void Init(string serverUrl, string pinsSubmodelId, string behaviorSubmodelId, Dictionary<string, GameObject> componentMap)
    {
        this.pinsUrl = $"{serverUrl}/submodels/{Base64Url(pinsSubmodelId)}/submodel-elements/Inputs";
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
                            foreach (var p in val["value"])
                            {
                                string pid = p["idShort"]?.ToString();
                                float fv = 0f;
                                if (p["value"] != null) float.TryParse(p["value"].ToString().Replace(',', '.'), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out fv);
                                if (pid == "AxisX") axis.x = fv;
                                if (pid == "AxisY") axis.y = fv;
                                if (pid == "AxisZ") axis.z = fv;
                                if (pid == "Speed") speed = fv;
                                if (pid == "LimitMin") min = fv;
                                if (pid == "LimitMax") max = fv;
                            }
                        }
                    }
                    if (type == "TriggerZone" || type == "ContactSensor") continue;
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
                            foreach (var col in target.GetComponentsInChildren<Collider>()) {
                                if (col.gameObject.GetComponent<Rigidbody>() == null) {
                                    var rb = col.gameObject.AddComponent<Rigidbody>();
                                    rb.isKinematic = true;
                                }
                                var surf = col.gameObject.GetComponent<ConveyorSurface>() ?? col.gameObject.AddComponent<ConveyorSurface>();
                                surf.Setup(target, this);
                            }
                        }
                    }
                }
            }
            isInitialized = true;
            StartCoroutine(PollingLoop());
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
                if (root is JObject obj) elements = (obj["result"] ?? obj["value"]) as JArray;
                else if (root is JArray arr) elements = arr;
                if (elements != null)
                {
                    foreach (var el in elements)
                    {
                        string pid = el["idShort"]?.ToString();
                        bool val = false;
                        if (el["value"] != null) bool.TryParse(el["value"].ToString(), out val);
                        var b = bindings.Find(x => x.pinId == pid);
                        if (b != null) b.currentState = val;
                    }
                }
            }
            yield return new WaitForSeconds(pollInterval);
        }
    }

    void Update()
    {
        if (!isInitialized) return;
        foreach (var b in bindings) {
            if (b.target == null) continue;
            switch (b.type) {
                case "TranslateContinuous": if (b.currentState) b.target.transform.Translate(b.axis * b.speed * Time.deltaTime, Space.Self); break;
                case "RotateContinuous": if (b.currentState) b.target.transform.Rotate(b.axis, b.speed * Time.deltaTime * 100f, Space.Self); break;
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