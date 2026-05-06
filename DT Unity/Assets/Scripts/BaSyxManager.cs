using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Linq;
using System.Xml.Linq;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;
using Unity.Robotics.UrdfImporter;

public class BaSyxManager : MonoBehaviour
{
    [Header("BaSyx Infrastructure")]
    public string registryUrl = "http://localhost:8082/shell-descriptors";
    public string aasServerUrl = "http://localhost:8081";

    [Header("Settings")]
    public float globalScale = 1.0f;
    public string baseCachePath;

    public class MaterialData
    {
        public Color color = Color.white;
        public string texturePath = null;
        public bool hasColor = false;
        public bool hasTexture = false;
    }

    void Awake()
    {
        baseCachePath = Path.Combine(Application.persistentDataPath, "AAS_Robots");
    }

    void Start()
    {
        Debug.Log("[BaSyx] 🧹 Cleaning local cache...");
        if (Directory.Exists(baseCachePath)) Directory.Delete(baseCachePath, true);
        Directory.CreateDirectory(baseCachePath);

        Debug.Log("[BaSyx] 🔍 Searching for robots in Registry...");
        StartCoroutine(SyncRobotsRoutine());
    }

    IEnumerator SyncRobotsRoutine()
    {
        // 1. Get AAS Descriptors from Discovery/Registry
        UnityWebRequest regReq = UnityWebRequest.Get(registryUrl);
        yield return regReq.SendWebRequest();

        if (regReq.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[BaSyx] ❌ Registry error: {regReq.error}");
            yield break;
        }

        var shells = DeserializeList<AasDescriptor>(regReq.downloadHandler.text);
        
        foreach (var shell in shells)
        {
            // Debug.Log($"[BaSyx] 🤖 Processing: {shell.idShort}");
            StartCoroutine(ProcessRobot(shell));
        }
    }

    IEnumerator ProcessRobot(AasDescriptor shell)
    {
        string robotName = string.IsNullOrEmpty(shell.idShort) ? "UnknownRobot" : shell.idShort;
        string robotPath = Path.Combine(baseCachePath, robotName);
        Directory.CreateDirectory(robotPath);

        // 1. Try to fetch full descriptor from Registry
        if ((shell.submodelDescriptors == null || shell.submodelDescriptors.Count == 0) && !string.IsNullOrEmpty(shell.id))
        {
            string detailUrl = $"{registryUrl}/{Base64Url(shell.id)}";
            UnityWebRequest detReq = UnityWebRequest.Get(detailUrl);
            yield return detReq.SendWebRequest();
            if (detReq.result == UnityWebRequest.Result.Success)
            {
                var detailed = JsonConvert.DeserializeObject<AasDescriptor>(detReq.downloadHandler.text);
                if (detailed != null && detailed.submodelDescriptors != null)
                    shell.submodelDescriptors = detailed.submodelDescriptors;
            }
        }

        string geoSubmodelId = null;
        string posSubmodelId = null;

        // 2. Resolve from descriptors
        if (shell.submodelDescriptors != null)
        {
            foreach (var sm in shell.submodelDescriptors)
            {
                if (sm == null) continue;
                if (sm.idShort == "GeometryData") geoSubmodelId = sm.id;
                if (sm.idShort == "PositionData") posSubmodelId = sm.id;
            }
        }

        // 3. Fallback: Check Repository directly if Registry is incomplete
        if (geoSubmodelId == null && !string.IsNullOrEmpty(shell.id))
        {
            Debug.Log($"[BaSyx] 🚀 Registry incomplete. Searching Repository for {robotName}...");
            string repoShellUrl = $"{aasServerUrl}/shells/{Base64Url(shell.id)}";
            UnityWebRequest repoReq = UnityWebRequest.Get(repoShellUrl);
            yield return repoReq.SendWebRequest();

            if (repoReq.result == UnityWebRequest.Result.Success)
            {
                var repoAas = JsonConvert.DeserializeObject<AasRepositoryModel>(repoReq.downloadHandler.text);
                if (repoAas != null && repoAas.submodels != null)
                {
                    foreach (var smRef in repoAas.submodels)
                    {
                        if (smRef.keys == null || smRef.keys.Count == 0) continue;
                        string smId = smRef.keys[0].value;

                        // Fetch submodel metadata to check idShort
                        string smMetaUrl = $"{aasServerUrl}/submodels/{Base64Url(smId)}";
                        UnityWebRequest smReq = UnityWebRequest.Get(smMetaUrl);
                        yield return smReq.SendWebRequest();

                        if (smReq.result == UnityWebRequest.Result.Success)
                        {
                            var smDesc = JsonConvert.DeserializeObject<SubmodelDescriptor>(smReq.downloadHandler.text);
                            if (smDesc != null)
                            {
                                if (smDesc.idShort == "GeometryData") geoSubmodelId = smDesc.id;
                                if (smDesc.idShort == "PositionData") posSubmodelId = smDesc.id;
                            }
                        }
                        if (geoSubmodelId != null && posSubmodelId != null) break;
                    }
                }
            }
        }

        if (geoSubmodelId == null) 
        { 
            Debug.LogWarning($"[BaSyx] ⚠️ GeometryData not found for {robotName}. Check if submodel idShort is 'GeometryData'."); 
            yield break; 
        }

        // 4. Download URDF and Meshes
        Debug.Log($"[BaSyx] 📥 Downloading assets for {robotName}...");
        yield return StartCoroutine(DownloadRecursive(geoSubmodelId, robotPath));
        Debug.Log($"[BaSyx] 📥 Assets for {robotName} downloaded.");

        // 5. Pre-process URDF to handle Material Overrides (UR3e color fix)
        string urdfFile = FindUrdfFile(robotPath);
        if (urdfFile != null)
        {
            string processedUrdf = PreprocessUrdf(urdfFile);
            Debug.Log($"[BaSyx] 🔨 Found URDF for {robotName}: {urdfFile}. Importing...");
            GameObject robotObj = ImportUrdf(processedUrdf, robotName);
            if (robotObj != null)
            {
                PrepareRobot(robotObj, urdfFile);
                
                // 5. Synchronize initial position
                if (posSubmodelId != null) yield return StartCoroutine(SyncInitialPosition(posSubmodelId, robotObj));
            }
            else
            {
                Debug.LogError($"[BaSyx] ❌ ImportUrdf returned null for {robotName}");
            }
        }
        else
        {
            Debug.LogWarning($"[BaSyx] ⚠️ No URDF file found in {robotPath} for {robotName}. Assets downloaded: {Directory.GetFiles(robotPath, "*.*", SearchOption.AllDirectories).Length}");
        }
    }

    string PreprocessUrdf(string path)
    {
        try
        {
            XDocument doc = XDocument.Load(path);
            bool changed = false;

            foreach (var visual in doc.Descendants("visual"))
            {
                var mesh = visual.Element("geometry")?.Element("mesh");
                var mat = visual.Element("material");

                if (mesh != null && mat != null)
                {
                    string filename = mesh.Attribute("filename")?.Value?.ToLower() ?? "";
                    // Only intervene if it's a DAE/OBJ (which can have internal materials)
                    if (filename.EndsWith(".dae") || filename.EndsWith(".obj"))
                    {
                        string matName = mat.Attribute("name")?.Value ?? "";
                        Color matColor = ParseRGBA(mat.Element("color")?.Attribute("rgba")?.Value);
                        
                        // If material is generic gray, remove it so importer uses mesh's internal materials
                        if (matName.Contains("Grey") || matName.Contains("Gray") || IsGray(matColor))
                        {
                            // Debug.Log($"[BaSyx] 🛠️ Removing URDF material override for {filename} to prioritize mesh colors.");
                            mat.Remove();
                            changed = true;
                        }
                    }
                }
            }

            if (changed)
            {
                string newPath = path.Replace(".urdf", "_processed.urdf").Replace(".xacro", "_processed.urdf");
                doc.Save(newPath);
                return newPath;
            }
        }
        catch (Exception e) { Debug.LogWarning($"[BaSyx] ⚠️ URDF Preprocess error: {e.Message}"); }
        return path;
    }

    IEnumerator DownloadRecursive(string submodelId, string targetDir)
    {
        string elementsUrl = $"{aasServerUrl}/submodels/{Base64Url(submodelId)}/submodel-elements?level=deep";
        UnityWebRequest req = UnityWebRequest.Get(elementsUrl);
        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[BaSyx] ❌ Failed to get elements for {submodelId}: {req.error}");
            yield break;
        }

        var elements = DeserializeList<SubmodelElement>(req.downloadHandler.text);
        if (elements == null || elements.Count == 0)
        {
            Debug.LogWarning($"[BaSyx] ⚠️ No elements found in submodel {submodelId}");
            yield break;
        }

        int fileCount = 0;
        foreach (var el in elements)
        {
            if (el == null || string.IsNullOrEmpty(el.idShort)) continue;

            if (el.modelType == "File")
            {
                fileCount++;
                // 1. Reconstruir a HIERARQUIA a partir do idShort (é o único sítio com as pastas _SL_)
                string relPath = el.idShort;
                if (relPath.Contains("-PATH_")) relPath = "PATH_" + relPath.Split(new[] { "-PATH_" }, StringSplitOptions.None).Last();
                relPath = relPath.Replace("PATH_", "").Replace("_SL_", "/").Replace("_DOT_", ".").Replace("_DASH_", "-");

                // 2. Tentar obter o caminho real a partir do 'value' (caso o BaSyx o tenha preservado)
                string val = el.value?.ToString();
                if (!string.IsNullOrEmpty(val) && val.Contains("/"))
                {
                    relPath = val;
                }
                
                // Fallback para o URDF principal se necessário
                if (el.idShort.Contains("Main_URDF") && !relPath.EndsWith(".urdf")) relPath = "robot.urdf";
                else if (!relPath.Contains(".")) relPath += ".urdf";

                // 3. Limpar o caminho para ser relativo e seguro
                string cleanPath = relPath;
                
                // Remover prefixos comuns de AAS/AASX
                string[] prefixesToRemove = { "/aasx/robot/", "/aasx/", "aasx/", "robot/" };
                foreach (var prefix in prefixesToRemove)
                {
                    if (cleanPath.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                    {
                        cleanPath = cleanPath.Substring(prefix.Length);
                        break;
                    }
                }

                // Limpar "../", "..\" e "/" iniciais
                cleanPath = cleanPath.Replace("\\", "/").TrimStart('/');
                while (cleanPath.StartsWith("../")) cleanPath = cleanPath.Substring(3);
                while (cleanPath.Contains("../")) cleanPath = cleanPath.Replace("../", "");
                
                string dest = Path.Combine(targetDir, cleanPath);
                string dir = Path.GetDirectoryName(dest);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir)) Directory.CreateDirectory(dir);

                // 3. Download do anexo usando o idShort original
                string downloadUrl = $"{aasServerUrl}/submodels/{Base64Url(submodelId)}/submodel-elements/{el.idShort}/attachment";
                UnityWebRequest dl = UnityWebRequest.Get(downloadUrl);
                yield return dl.SendWebRequest();

                if (dl.result == UnityWebRequest.Result.Success)
                {
                    File.WriteAllBytes(dest, dl.downloadHandler.data);
                    // Debug.Log($"   [+] Saved: {cleanPath} in {targetDir}");
                }
            }
        }
    }

    GameObject ImportUrdf(string path, string name)
    {
        try
        {
            // Debug.Log($"[BaSyx] 🔨 Importing URDF: {path}");
            var settings = new ImportSettings { chosenAxis = ImportSettings.axisType.yAxis, convexMethod = ImportSettings.convexDecomposer.unity };
            
            GameObject robot = UrdfRobotExtensions.CreateRuntime(Path.GetFullPath(path), settings);
            
            if (robot != null)
            {
                // Garantir que entra no contentor ANTES de qualquer outra coisa
                GameObject container = GameObject.Find("AAS_Robots_Container");
                if (container == null) container = new GameObject("AAS_Robots_Container");
                robot.transform.SetParent(container.transform, false);
                robot.name = name;
                
                // Parar a física no momento em que nasce
                StripPhysics(robot);
            }
            return robot;
        }
        catch (Exception e) { Debug.LogError($"[BaSyx] ❌ Import Error: {e.Message}"); return null; }
    }

    void StripPhysics(GameObject root)
    {
        // 1. Primeiro remover scripts que dependem dos componentes de física
        foreach (var s in root.GetComponentsInChildren<MonoBehaviour>(true))
        {
            if (s == null || s == this) continue;
            string typeName = s.GetType().Name;
            if (typeName.Contains("Urdf") || typeName.Contains("Articulation")) 
                DestroyImmediate(s);
        }

        // 2. Agora remover os componentes de física propriamente ditos
        // Ordem: ArticulationBody -> Rigidbody -> Colliders -> Joints -> Inertials
        foreach (var b in root.GetComponentsInChildren<ArticulationBody>(true)) DestroyImmediate(b);
        foreach (var rb in root.GetComponentsInChildren<Rigidbody>(true)) DestroyImmediate(rb);
        foreach (var c in root.GetComponentsInChildren<Collider>(true)) DestroyImmediate(c);
        foreach (var j in root.GetComponentsInChildren<UnityEngine.Joint>(true)) DestroyImmediate(j);
        
        // Remover Inertials que podem ter sobrado (se não forem scripts)
        // No Unity Robotics Importer, Inertial é geralmente um script UrdfInertial, já removido acima.

        // Garantir que as peças ficam estáticas
        foreach (var t in root.GetComponentsInChildren<Transform>(true)) {
            // (Opcional) Podes forçar o scale aqui se necessário
        }
    }

    void PrepareRobot(GameObject robot, string urdfPath)
    {
        if (robot == null) return;
        robot.transform.localScale = Vector3.one * globalScale;

        // Limpar tudo o que é física e scripts do importer
        StripPhysics(robot);

        // Extrair materiais
        Dictionary<string, MaterialData> urdfMaterials = ParseUrdfMaterials(urdfPath);

        // 3. Material and Shader Validation (Unity 6 / URP)
        bool isURP = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline != null;
        string shaderName = isURP ? "Universal Render Pipeline/Lit" : "Standard";
        Shader targetShader = Shader.Find(shaderName);
        if (targetShader == null) Debug.LogWarning($"[BaSyx] ⚠️ Shader '{shaderName}' not found!");

        foreach (var renderer in robot.GetComponentsInChildren<Renderer>())
        {
            // Try to find material based on link name by traversing hierarchy
            MaterialData linkMat = null;
            Transform current = renderer.transform;
            
            while (current != null && current != robot.transform)
            {
                string cleanName = current.name.Replace("(Clone)", "").Trim();
                // Attempt exact or partial match (many importers change names slightly)
                linkMat = urdfMaterials.FirstOrDefault(x => 
                    string.Equals(x.Key, cleanName, StringComparison.OrdinalIgnoreCase) || 
                    cleanName.StartsWith(x.Key, StringComparison.OrdinalIgnoreCase) ||
                    x.Key.StartsWith(cleanName, StringComparison.OrdinalIgnoreCase)).Value;

                if (linkMat != null) break;
                current = current.parent;
            }

            // Check if mesh has vertex colors
            MeshFilter mf = renderer.GetComponent<MeshFilter>();
            bool hasVertexColors = mf != null && mf.sharedMesh != null && mf.sharedMesh.colors != null && mf.sharedMesh.colors.Length > 0;

            Material[] mats = renderer.materials;
            for (int i = 0; i < mats.Length; i++)
            {
                Material mat = mats[i];
                Texture originalTex = mat.mainTexture;
                Color originalColor = isURP ? mat.GetColor("_BaseColor") : mat.color;

                if (targetShader != null) mat.shader = targetShader;

                // Detect if URDF material is a generic gray placeholder
                bool isPlaceholder = linkMat == null || !linkMat.hasColor || IsGray(linkMat.color);
                
                // If URDF has no color or is generic gray, try to keep mesh color
                // Only override if mesh color is invalid (e.g. error magenta) or URDF has a "real" non-gray color
                Color finalColor = originalColor;

                bool isErrorShader = (originalColor.r > 0.8f && originalColor.g < 0.2f && originalColor.b > 0.8f); // Magenta

                // Priority Logic:
                // 1. If we have a texture, prioritize it (color = white to avoid tinting)
                // 2. If URDF material is NOT gray, use it
                // 3. Otherwise, use original mesh color (if not gray) or fallback to URDF gray
                
                if (originalTex != null)
                {
                    finalColor = Color.white;
                    // Debug.Log($"[BaSyx] 🎨 Using TEXTURE for {renderer.name}");
                }
                else if (linkMat != null && linkMat.hasColor && (!isPlaceholder || isErrorShader))
                {
                    finalColor = linkMat.color;
                    // Debug.Log($"[BaSyx] 🎨 Using URDF COLOR {finalColor} for {renderer.name}");
                }
                else if (isPlaceholder && !IsGray(originalColor) && !isErrorShader)
                {
                    // Mesh had a color and URDF says gray -> Keep mesh color
                    finalColor = originalColor;
                    // Debug.Log($"[BaSyx] 🎨 Using MESH COLOR {finalColor} for {renderer.name}");
                }
                
                // Fallback to default gray if color is empty or broken
                if (finalColor.a < 0.01f || (isErrorShader && isPlaceholder)) 
                    finalColor = Color.gray;

                // Force white if vertex colors exist to avoid tinting
                if (hasVertexColors) finalColor = Color.white;

                if (isURP)
                {
                    if (originalTex != null) mat.SetTexture("_BaseMap", originalTex);
                    mat.SetColor("_BaseColor", finalColor);
                    mat.SetFloat("_Metallic", 0.1f);
                    mat.SetFloat("_Smoothness", 0.4f);
                }
                else
                {
                    if (originalTex != null) mat.mainTexture = originalTex;
                    mat.color = finalColor;
                    mat.SetFloat("_Metallic", 0.1f);
                    mat.SetFloat("_Glossiness", 0.4f);
                }
            }
            renderer.materials = mats;
        }
        Debug.Log($"[BaSyx] ✅ {robot.name} prepared.");
    }

    IEnumerator SyncInitialPosition(string submodelId, GameObject robot)
    {
        string elementsUrl = $"{aasServerUrl}/submodels/{Base64Url(submodelId)}/submodel-elements";
        UnityWebRequest req = UnityWebRequest.Get(elementsUrl);
        yield return req.SendWebRequest();

        if (req.result == UnityWebRequest.Result.Success)
        {
            var elements = DeserializeList<SubmodelElement>(req.downloadHandler.text);
            Vector3 pos = Vector3.zero;
            foreach (var el in elements)
            {
                if (el == null || string.IsNullOrEmpty(el.idShort) || el.value == null) continue;

                string k = el.idShort.ToUpper();
                try
                {
                    if (k.Contains("X")) pos.x = SafeFloat(el.value);
                    if (k.Contains("Y")) pos.y = SafeFloat(el.value);
                    if (k.Contains("Z")) pos.z = SafeFloat(el.value);
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[BaSyx] ⚠️ Failed to sync coordinate {el.idShort}: {e.Message} (Value type: {el.value.GetType().Name})");
                }
            }
            robot.transform.position = pos;
            // Debug.Log($"[BaSyx] 📍 Initial position synced: {pos}");
        }
    }

    float SafeFloat(object v)
    {
        if (v == null) return 0f;
        if (v is float f) return f;
        if (v is double d) return (float)d;
        if (v is int i) return (float)i;
        if (v is long l) return (float)l;
        if (v is string s && float.TryParse(s, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out float res)) return res;
        
        try { return Convert.ToSingle(v, System.Globalization.CultureInfo.InvariantCulture); }
        catch { return 0f; }
    }

    Texture2D LoadTexture(string path)
    {
        try
        {
            byte[] data = File.ReadAllBytes(path);
            Texture2D tex = new Texture2D(2, 2);
            if (tex.LoadImage(data)) return tex;
        }
        catch (Exception e) { Debug.LogWarning($"[BaSyx] ⚠️ Error loading texture {path}: {e.Message}"); }
        return null;
    }

    bool IsGray(Color c)
    {
        float avg = (c.r + c.g + c.b) / 3f;
        // Stricter check: must be very close to gray to be considered "placeholder"
        return Mathf.Abs(c.r - avg) < 0.02f && Mathf.Abs(c.g - avg) < 0.02f && Mathf.Abs(c.b - avg) < 0.02f;
    }

    Color ParseRGBA(string rgba)
    {
        if (string.IsNullOrEmpty(rgba)) return Color.gray;
        try
        {
            var p = rgba.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries)
                        .Select(s => float.Parse(s, System.Globalization.CultureInfo.InvariantCulture))
                        .ToArray();
            return p.Length >= 3 ? new Color(p[0], p[1], p[2], p.Length > 3 ? p[3] : 1f) : Color.gray;
        }
        catch { return Color.gray; }
    }

    Dictionary<string, MaterialData> ParseUrdfMaterials(string path)
    {
        var materials = new Dictionary<string, MaterialData>();
        try
        {
            XDocument doc = XDocument.Load(path);
            var globals = new Dictionary<string, MaterialData>();

            // 1. Collect global materials
            foreach (var m in doc.Descendants("material"))
            {
                string n = m.Attribute("name")?.Value;
                if (string.IsNullOrEmpty(n)) continue;
                if (globals.ContainsKey(n)) continue;

                var data = new MaterialData();
                var c = m.Element("color");
                if (c != null) { data.color = ParseRGBA(c.Attribute("rgba")?.Value); data.hasColor = true; }
                
                var t = m.Element("texture");
                if (t != null) { data.texturePath = t.Attribute("filename")?.Value; data.hasTexture = true; }

                if (data.hasColor || data.hasTexture) globals[n] = data;
            }

            // 2. Associate materials with links
            foreach (var l in doc.Descendants("link"))
            {
                string ln = l.Attribute("name")?.Value;
                if (string.IsNullOrEmpty(ln)) continue;

                foreach (var v in l.Elements("visual"))
                {
                    var m = v.Element("material");
                    if (m == null) continue;

                    string mn = m.Attribute("name")?.Value;
                    var data = new MaterialData();

                    // Check for local color/texture definition
                    var c = m.Element("color");
                    if (c != null) { data.color = ParseRGBA(c.Attribute("rgba")?.Value); data.hasColor = true; }
                    
                    var t = m.Element("texture");
                    if (t != null) { data.texturePath = t.Attribute("filename")?.Value; data.hasTexture = true; }

                    // If no local definition, try global by name
                    if (!data.hasColor && !data.hasTexture && !string.IsNullOrEmpty(mn) && globals.ContainsKey(mn))
                    {
                        data = globals[mn];
                    }

                    if (data.hasColor || data.hasTexture) materials[ln] = data;
                }
            }
        }
        catch (Exception e) { Debug.LogWarning($"[BaSyx] ⚠️ Error processing URDF for materials: {e.Message}"); }
        return materials;
    }

    [Serializable] public class AasDescriptor { public string idShort; public string id; public List<SubmodelDescriptor> submodelDescriptors; }
    [Serializable] public class SubmodelDescriptor { public string idShort; public string id; }
    [Serializable] public class SubmodelElement { public string idShort; public string modelType; public object value; }

    [Serializable] public class AasRepositoryModel { public List<SubmodelReference> submodels; }
    [Serializable] public class SubmodelReference { public List<SubmodelKey> keys; }
    [Serializable] public class SubmodelKey { public string value; }

    [Serializable]
    public class PagedResponse<T>
    {
        public List<T> result;
    }

    private List<T> DeserializeList<T>(string json)
    {
        if (string.IsNullOrEmpty(json)) return new List<T>();
        string trimmed = json.Trim();
        if (trimmed.StartsWith("{"))
        {
            var paged = JsonConvert.DeserializeObject<PagedResponse<T>>(json);
            return paged?.result ?? new List<T>();
        }
        return JsonConvert.DeserializeObject<List<T>>(json) ?? new List<T>();
    }

    string Base64Url(string i) => Convert.ToBase64String(Encoding.UTF8.GetBytes(i)).Replace("+", "-").Replace("/", "_").TrimEnd('=');
    string FindUrdfFile(string dir) 
    { 
        // 1. Procurar por ficheiros que terminem em .urdf ou .xacro
        var fs = Directory.GetFiles(dir, "*.*", SearchOption.AllDirectories)
                .Where(f => f.EndsWith(".urdf", StringComparison.OrdinalIgnoreCase) || 
                            f.EndsWith(".xacro", StringComparison.OrdinalIgnoreCase))
                .ToArray();

        if (fs.Length == 0) return null;

        // 2. Se houver vários, dar prioridade ao que parece ser o principal
        // Prioridade: Ficheiros com "robot" no nome > .urdf > .xacro
        return fs.OrderByDescending(f => f.Contains("robot"))
                 .ThenByDescending(f => f.EndsWith(".urdf", StringComparison.OrdinalIgnoreCase))
                 .First();
    }
}
