using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.Linq;
using System.Net.Sockets;
using System.Net;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

public class AASRobotSync : MonoBehaviour
{
    private string submodelUrl;
    private string aasServerUrl;
    
    [Header("Telemetry State")]
    public string protocol;
    public string host;
    public string port;
    public string endpoint;
    public string httpMethod = "GET";
    public string units = "rad"; // "rad", "deg"
    public string authType = "None";
    public string username;
    public string password;

    private Dictionary<string, Transform> jointTransforms = new Dictionary<string, Transform>();
    private float updateRate = 0.05f; // 20Hz default
    private float lastUpdateTime = 0;

    // Generic TCP State
    private TcpClient tcpClient;
    private NetworkStream tcpStream;
    private bool isConnecting = false;

    public void Init(string submodelId, string serverUrl)
    {
        this.aasServerUrl = serverUrl;
        this.submodelUrl = $"{serverUrl}/submodels/{Base64Url(submodelId)}";
        StartCoroutine(FetchTelemetryConfig());
    }

    IEnumerator FetchTelemetryConfig()
    {
        using (UnityWebRequest req = UnityWebRequest.Get($"{submodelUrl}/submodel-elements?level=deep"))
        {
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                string json = req.downloadHandler.text;
                List<BaSyxManager.SubmodelElement> elements = ParseElements(json);

                if (elements != null)
                {
                    foreach (var el in elements)
                    {
                        switch (el.idShort)
                        {
                            case "Protocol": protocol = el.value?.ToString(); break;
                            case "Host": host = el.value?.ToString(); break;
                            case "Port": port = el.value?.ToString(); break;
                            case "Endpoint": endpoint = el.value?.ToString(); break;
                            case "HTTP_Method": httpMethod = el.value?.ToString() ?? "GET"; break;
                            case "JointUnits": units = el.value?.ToString(); break;
                            case "Authentication": ParseAuth(el.value); break;
                        }
                    }
                    
                    Debug.Log($"[Sync] ⚙️ Telemetry Configured for {gameObject.name}: Protocol={protocol}, Host={host}:{port}");
                    MapJoints();
                    StartCoroutine(CommunicationLoop());
                }
            }
        }
    }

    private List<BaSyxManager.SubmodelElement> ParseElements(string json)
    {
        try {
            JToken token = JToken.Parse(json);
            if (token is JArray arr) return arr.ToObject<List<BaSyxManager.SubmodelElement>>();
            if (token is JObject obj) {
                if (obj["result"] != null) return obj["result"].ToObject<List<BaSyxManager.SubmodelElement>>();
                if (obj["value"] != null) return obj["value"].ToObject<List<BaSyxManager.SubmodelElement>>();
            }
        } catch {}
        return null;
    }

    void ParseAuth(object val)
    {
        string json = JsonConvert.SerializeObject(val);
        var elements = ParseElements(json);
        if (elements != null) {
            foreach(var e in elements) {
                if (e.idShort == "Type") authType = e.value?.ToString();
                if (e.idShort == "Username") username = e.value?.ToString();
                if (e.idShort == "Password") password = e.value?.ToString();
            }
        }
    }

    void MapJoints()
    {
        jointTransforms.Clear();
        foreach (var t in GetComponentsInChildren<Transform>())
        {
            string cleanName = t.name.Replace("(Clone)", "").Trim().ToLower();
            jointTransforms[cleanName] = t;
        }
    }

    IEnumerator CommunicationLoop()
    {
        while (true)
        {
            if (Time.time - lastUpdateTime >= updateRate)
            {
                lastUpdateTime = Time.time;
                if (string.IsNullOrEmpty(protocol) || protocol == "Offline / No Connection") { 
                    yield return new WaitForSeconds(1); 
                    continue; 
                }

                if (protocol.Contains("HTTP") || protocol.Contains("REST"))
                {
                    yield return StartCoroutine(HandleRestProtocol());
                }
                else if (protocol.Contains("Socket") || protocol.Contains("TCP"))
                {
                    yield return StartCoroutine(HandleTcpProtocol());
                }
                else 
                {
                    // Fallback generic: Sync directly from AAS properties
                    yield return StartCoroutine(SyncFromAASLiveJoints());
                }
            }
            yield return null; 
        }
    }

    IEnumerator HandleRestProtocol()
    {
        string url = $"http://{host}:{port}{endpoint}";
        using (UnityWebRequest req = new UnityWebRequest(url, httpMethod))
        {
            req.downloadHandler = new DownloadHandlerBuffer();
            req.timeout = 1;
            
            if (authType != "None" && !string.IsNullOrEmpty(username)) {
                string auth = Convert.ToBase64String(Encoding.UTF8.GetBytes($"{username}:{password}"));
                req.SetRequestHeader("Authorization", "Basic " + auth);
            }
            
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                ProcessGenericPayload(req.downloadHandler.text);
            }
        }
    }

    IEnumerator HandleTcpProtocol()
    {
        IAsyncResult connectResult = null;
        if (tcpClient == null || (!tcpClient.Connected && !isConnecting))
        {
            isConnecting = true;
            try {
                tcpClient = new TcpClient();
                connectResult = tcpClient.BeginConnect(host, int.Parse(port), null, null);
            } catch { isConnecting = false; }
        }

        if (isConnecting && connectResult != null)
        {
            float timeout = Time.time + 1.0f;
            while (!connectResult.IsCompleted && Time.time < timeout) yield return null;
            try {
                if (tcpClient.Connected) {
                    tcpClient.EndConnect(connectResult);
                    tcpStream = tcpClient.GetStream();
                }
            } catch { }
            isConnecting = false;
            if (!tcpClient.Connected) yield return new WaitForSeconds(5);
        }

        if (tcpClient != null && tcpClient.Connected)
        {
            if (tcpStream != null && tcpStream.DataAvailable)
            {
                // Clear buffer or read specific protocol bytes here
                byte[] buf = new byte[1024];
                tcpStream.Read(buf, 0, buf.Length);
            }
            // By default, if on TCP, we use the AAS as the shared blackboard for joint data
            yield return StartCoroutine(SyncFromAASLiveJoints());
        }
    }

    void ProcessGenericPayload(string payload)
    {
        // Try to find numeric values associated with joint names in the payload
        // This handles cases like ABB XHTML or generic JSON responses
        foreach (var kvp in jointTransforms)
        {
            string jointName = kvp.Key;
            // Look for patterns like "joint_name">VALUE or "joint_name":VALUE
            var match = System.Text.RegularExpressions.Regex.Match(payload, $"{jointName}[^>:]*[\">:]+([^<,\\s}}]+)");
            if (match.Success)
            {
                string valStr = match.Groups[1].Value.Replace(',', '.');
                if (float.TryParse(valStr, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float val))
                {
                    RotateJoint(kvp.Value, val);
                }
            }
        }
        
        // Specific fallback for rax_1...6 patterns if names differ
        for (int i = 1; i <= 6; i++) {
            var match = System.Text.RegularExpressions.Regex.Match(payload, $"rax_{i}[^>:]*[\">:]+([^<,\\s}}]+)");
            if (match.Success) {
                string valStr = match.Groups[1].Value.Replace(',', '.');
                if (float.TryParse(valStr, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float val)) {
                    string targetName = $"rax_{i}";
                    if (jointTransforms.TryGetValue(targetName, out Transform t)) RotateJoint(t, val);
                }
            }
        }
    }

    IEnumerator SyncFromAASLiveJoints()
    {
        string url = $"{submodelUrl}/submodel-elements/LiveJoints?level=deep";
        using (UnityWebRequest req = UnityWebRequest.Get(url))
        {
            req.timeout = 1;
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                var elements = ParseElements(req.downloadHandler.text);
                if (elements != null)
                {
                    foreach (var el in elements)
                    {
                        if (el.value != null && jointTransforms.TryGetValue(el.idShort.ToLower(), out Transform t))
                        {
                            RotateJoint(t, Convert.ToSingle(el.value));
                        }
                    }
                }
            }
        }
    }

    void RotateJoint(Transform t, float value)
    {
        float angle = (units == "deg") ? value : value * Mathf.Rad2Deg;
        t.localRotation = Quaternion.AngleAxis(angle, Vector3.forward);
    }

    string Base64Url(string i) => Convert.ToBase64String(Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');

    void OnDestroy()
    {
        if (tcpClient != null) { tcpClient.Close(); tcpClient = null; }
    }
}
