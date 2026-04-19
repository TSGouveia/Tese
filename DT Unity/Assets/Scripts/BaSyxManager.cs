using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Unity.Robotics.UrdfImporter;

public class BaSyxManager : MonoBehaviour
{
    [Header("Configurações BaSyx")]
    public string registryUrl = "http://localhost:8082/shell-descriptors";
    public string repositoryUrl = "http://localhost:8081";

    [Header("Configurações de Importação")]
    public bool clearDataOnStartup = true;
    public float positionUpdateInterval = 0.1f; 
    public float globalScale = 1.0f;

    private string baseDownloadPath;
    private Transform robotsContainer;
    private Dictionary<string, GameObject> activeRobots = new Dictionary<string, GameObject>();

    void Start()
    {
        baseDownloadPath = Path.Combine(Application.persistentDataPath, "AAS_Robots");
        
        // Criar um container para organizar os robôs na cena
        robotsContainer = new GameObject("[IMPORTED_ROBOTS]").transform;

        if (clearDataOnStartup && Directory.Exists(baseDownloadPath)) 
        {
            Debug.Log("[BaSyx] 🧹 A limpar cache local...");
            Directory.Delete(baseDownloadPath, true);
        }
        if (!Directory.Exists(baseDownloadPath)) Directory.CreateDirectory(baseDownloadPath);
        
        StartCoroutine(SyncRobotsRoutine());
    }

    IEnumerator SyncRobotsRoutine()
    {
        Debug.Log("[BaSyx] 🔍 A procurar shells no Registry...");
        using (UnityWebRequest webRequest = UnityWebRequest.Get(registryUrl))
        {
            yield return webRequest.SendWebRequest();
            if (webRequest.result != UnityWebRequest.Result.Success) yield break;

            JToken token = JToken.Parse(webRequest.downloadHandler.text);
            JArray shells = token is JArray ? (JArray)token : (JArray)token["result"];
            
            if (shells == null) yield break;

            foreach (JObject shell in shells)
            {
                string id = shell["id"]?.ToString();
                if (string.IsNullOrEmpty(id) || id == "paging_metadata") continue;

                // Evitar spawn duplicado do mesmo robô (AAS ID)
                if (activeRobots.ContainsKey(id)) continue;

                yield return StartCoroutine(ProcessRobot(shell));
            }
        }
    }

    IEnumerator ProcessRobot(JObject shellDesc)
    {
        string id = shellDesc["id"].ToString();
        string idShort = shellDesc["idShort"]?.ToString() ?? "Robot_" + id.GetHashCode();
        string robotDownloadDir = Path.Combine(baseDownloadPath, idShort);
        
        if (!Directory.Exists(robotDownloadDir)) Directory.CreateDirectory(robotDownloadDir);
        Debug.Log($"[BaSyx] 🤖 A processar: {idShort}");

        // 1. Procurar Submodels
        string geometrySubmodelId = FindSubmodelIdShort(shellDesc, "GeometryData");
        if (string.IsNullOrEmpty(geometrySubmodelId)) yield return StartCoroutine(FindSubmodelInRepository(id, "GeometryData", (res) => geometrySubmodelId = res));

        string posSubmodelId = FindSubmodelIdShort(shellDesc, "PositionData");
        if (string.IsNullOrEmpty(posSubmodelId)) yield return StartCoroutine(FindSubmodelInRepository(id, "PositionData", (res) => posSubmodelId = res));

        // 2. Download Geometria
        if (!string.IsNullOrEmpty(geometrySubmodelId)) yield return StartCoroutine(DownloadGeometry(geometrySubmodelId, robotDownloadDir));

        // 3. Importação do URDF
        string urdfPath = FindUrdfInDirectory(robotDownloadDir);
        if (!string.IsNullOrEmpty(urdfPath))
        {
            GameObject robotGo = ImportRobot(urdfPath, idShort);
            if (robotGo != null)
            {
                // Organizar na hierarquia (dentro do container, mas isolado)
                robotGo.transform.SetParent(robotsContainer);
                activeRobots[id] = robotGo;
                
                PrepareRobot(robotGo);
                
                // 4. Posicionamento Único
                if (!string.IsNullOrEmpty(posSubmodelId)) StartCoroutine(PositionSyncRoutine(robotGo, posSubmodelId));
            }
        }
        else Debug.LogError($"[BaSyx] ❌ URDF não encontrado para {idShort}");
    }

    void PrepareRobot(GameObject robot)
    {
        robot.transform.localScale = Vector3.one * globalScale;
        
        // Limpeza total de componentes que impedem movimento absoluto ou causam erros
        foreach (var s in robot.GetComponentsInChildren<MonoBehaviour>()) { 
            string n = s.GetType().Name; 
            if (n.Contains("UrdfJoint") || n.Contains("UrdfInertial")) Destroy(s); 
        }
        foreach (var b in robot.GetComponentsInChildren<ArticulationBody>()) Destroy(b);
        foreach (var c in robot.GetComponentsInChildren<Collider>()) Destroy(c);
        
        Debug.Log($"[BaSyx] ✅ {robot.name} pronto e isolado.");
    }

    IEnumerator PositionSyncRoutine(GameObject robot, string smId)
    {
        string encodedSmId = Base64UrlEncode(smId);
        yield return StartCoroutine(GetPositionFromAAS(encodedSmId, (pos) => {
            Debug.Log($"[BaSyx] 📍 Posição absoluta aplicada a {robot.name}: {pos}");
            robot.transform.position = pos;
        }));
    }

    IEnumerator GetPositionFromAAS(string encodedSmId, Action<Vector3> onResult)
    {
        string url = $"{repositoryUrl}/submodels/{encodedSmId}/submodel-elements";
        using (UnityWebRequest req = UnityWebRequest.Get(url))
        {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                JToken token = JToken.Parse(req.downloadHandler.text);
                JArray elements = token is JArray ? (JArray)token : (JArray)token["result"];
                if (elements == null) yield break;

                float x = 0, y = 0, z = 0;
                bool found = false;

                void Search(JArray items) {
                    foreach (JObject el in items) {
                        string type = el["modelType"]?.ToString();
                        string key = el["idShort"]?.ToString().ToUpper();
                        if (type == "Property") {
                            string val = el["value"]?.ToString();
                            if (float.TryParse(val, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out float f)) {
                                if (key == "X" || key == "POS_X") { x = f; found = true; }
                                else if (key == "Y" || key == "POS_Y") { y = f; found = true; }
                                else if (key == "Z" || key == "POS_Z") { z = f; found = true; }
                            }
                        } else if (type == "SubmodelElementCollection") Search((JArray)el["value"]);
                    }
                }
                Search(elements);
                if (found) onResult(new Vector3(x, y, z));
            }
        }
    }

    // --- Helpers ---
    string DecryptAasPath(string raw) {
        if (raw.Contains("-PATH_")) {
            string p = raw.Split(new string[] { "-PATH_" }, StringSplitOptions.None)[1];
            if (p.Contains("-")) p = p.Substring(0, p.LastIndexOf('-'));
            return p.Replace("_SL_", "/").Replace("_DOT_", ".");
        }
        if (raw.Contains("/aasx/robot/")) return raw.Split(new string[] { "/aasx/robot/" }, StringSplitOptions.None)[1];
        return Path.GetFileName(raw.Contains("-") ? raw.Split('-')[raw.Split('-').Length - 1] : raw);
    }

    IEnumerator DownloadGeometry(string smId, string dir) {
        yield return StartCoroutine(DownloadRecursive($"{repositoryUrl}/submodels/{Base64UrlEncode(smId)}/submodel-elements", dir, new HashSet<string>()));
    }

    IEnumerator DownloadRecursive(string url, string dir, HashSet<string> seen) {
        using (UnityWebRequest req = UnityWebRequest.Get(url)) {
            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success) yield break;
            JToken token = JToken.Parse(req.downloadHandler.text);
            JArray items = token is JArray ? (JArray)token : (JArray)token["result"];
            if (items == null) yield break;

            foreach (JObject el in items) {
                if (el["modelType"]?.ToString() == "File") {
                    string rel = DecryptAasPath(el["value"]?.ToString() ?? el["idShort"]?.ToString());
                    if (seen.Contains(rel)) continue;
                    string dest = Path.Combine(dir, rel);
                    Directory.CreateDirectory(Path.GetDirectoryName(dest));
                    using (UnityWebRequest dl = UnityWebRequest.Get($"{url}/{el["idShort"]}/attachment")) {
                        yield return dl.SendWebRequest();
                        if (dl.result == UnityWebRequest.Result.Success) { File.WriteAllBytes(dest, dl.downloadHandler.data); seen.Add(rel); }
                    }
                } else if (el["modelType"]?.ToString() == "SubmodelElementCollection") 
                    yield return StartCoroutine(DownloadRecursive($"{url}/{el["idShort"]}/submodel-elements", dir, seen));
            }
        }
    }

    GameObject ImportRobot(string path, string name) {
        try {
            var settings = new ImportSettings { chosenAxis = ImportSettings.axisType.yAxis, convexMethod = ImportSettings.convexDecomposer.unity };
            return UrdfRobotExtensions.CreateRuntime(Path.GetFullPath(path), settings);
        } catch { return null; }
    }

    string FindUrdfInDirectory(string dir) { string[] fs = Directory.GetFiles(dir, "*.urdf", SearchOption.AllDirectories); return fs.Length > 0 ? fs[0] : null; }
    string Base64UrlEncode(string i) => Convert.ToBase64String(Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');
    string FindSubmodelIdShort(JObject shell, string t) {
        var sms = shell["submodelDescriptors"];
        if (sms != null) foreach (var sm in sms) if (sm["idShort"]?.ToString() == t) return sm["id"]?.ToString();
        return null;
    }
    IEnumerator FindSubmodelInRepository(string id, string t, Action<string> onRes) {
        using (UnityWebRequest req = UnityWebRequest.Get($"{repositoryUrl}/shells/{Base64UrlEncode(id)}")) {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success) {
                JArray sms = (JArray)JObject.Parse(req.downloadHandler.text)["submodels"];
                foreach (JObject smRef in sms) {
                    string sid = smRef["keys"]?[0]?["value"]?.ToString();
                    string idS = null; yield return StartCoroutine(GetSubmodelIdShort(sid, (res) => idS = res));
                    if (idS == t) { onRes(sid); yield break; }
                }
            }
        }
        onRes(null);
    }
    IEnumerator GetSubmodelIdShort(string sid, Action<string> onRes) {
        using (UnityWebRequest req = UnityWebRequest.Get($"{repositoryUrl}/submodels/{Base64UrlEncode(sid)}")) {
            yield return req.SendWebRequest();
            onRes(req.result == UnityWebRequest.Result.Success ? JObject.Parse(req.downloadHandler.text)["idShort"]?.ToString() : null);
        }
    }
}
