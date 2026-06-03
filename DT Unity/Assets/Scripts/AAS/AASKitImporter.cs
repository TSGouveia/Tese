using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using Newtonsoft.Json.Linq;
using GLTFast;

public class AASKitImporter : MonoBehaviour
{
    public class KitImportData
    {
        public GameObject root;
        public Dictionary<string, GameObject> components;
    }

    public static async Task<KitImportData> ImportWithMetadataAsync(string jsonElements, string kitPath, string kitName, Transform parent = null)
    {
        try {
            JToken rootToken = JToken.Parse(jsonElements);
            JArray elements = null;
            
            if (rootToken is JObject obj && obj["result"] != null) elements = obj["result"] as JArray;
            else if (rootToken is JArray arr) elements = arr;

            if (elements == null) return null;

            GameObject kitRoot = new GameObject(kitName);
            if (parent != null) kitRoot.transform.SetParent(parent, false);

            Dictionary<string, GameObject> components = new Dictionary<string, GameObject>();
            Dictionary<string, string> parentMap = new Dictionary<string, string>();

            // 1. First Pass: Create GameObjects and Load GLBs
            foreach (JToken token in elements)
            {
                string compName = token["idShort"]?.ToString();
                if (string.IsNullOrEmpty(compName)) continue;

                GameObject compObj = new GameObject(compName);
                components[compName] = compObj;

                string meshFile = "";
                string parentName = "";
                Vector3 pos = Vector3.zero;
                Vector3 rot = Vector3.zero;

                JToken valueNode = token["value"];
                if (valueNode != null && valueNode.Type == JTokenType.Array)
                {
                    foreach (JToken prop in valueNode)
                    {
                        string idShort = prop["idShort"]?.ToString();
                        if (idShort == "Mesh") meshFile = prop["value"]?.ToString();
                        if (idShort == "Parent") parentName = prop["value"]?.ToString();
                        if (idShort == "Transform")
                        {
                            foreach (JToken tp in prop["value"])
                            {
                                string tId = tp["idShort"]?.ToString();
                                float v = tp["value"] != null ? (float)tp["value"] : 0f;
                                if (tId == "PosX") pos.x = v; if (tId == "PosY") pos.y = v; if (tId == "PosZ") pos.z = v;
                                if (tId == "RotX") rot.x = v; if (tId == "RotY") rot.y = v; if (tId == "RotZ") rot.z = v;
                            }
                        }
                    }
                }

                parentMap[compName] = parentName;
                
                // Blender (RH, Z-up) to Unity (LH, Y-up)
                compObj.transform.localPosition = new Vector3(-pos.x, pos.z, pos.y);
                compObj.transform.localEulerAngles = new Vector3(rot.x * Mathf.Rad2Deg, -rot.z * Mathf.Rad2Deg, -rot.y * Mathf.Rad2Deg);

                if (!string.IsNullOrEmpty(meshFile))
                {
                    string localPath = ResolveMeshPath(meshFile, kitPath);
                    if (!string.IsNullOrEmpty(localPath))
                    {
                        if (localPath.ToLower().EndsWith(".glb") || localPath.ToLower().EndsWith(".gltf"))
                        {
                            var gltf = new GltfImport();
                            string uri = "file:///" + localPath.Replace("\\", "/");
                            bool success = await gltf.Load(uri);
                            if (success) 
                            {
                                await gltf.InstantiateMainSceneAsync(compObj.transform);
                                
                                // POST-IMPORT FIXES (UVs and Colliders)
                                foreach (var renderer in compObj.GetComponentsInChildren<MeshRenderer>())
                                {
                                    // 1. UV Rotation Fix
                                    bool isBelt = renderer.name.ToLower().Contains("belt") || 
                                                  renderer.materials.Any(m => m.name.ToLower().Contains("belt"));
                                    if (isBelt)
                                    {
                                        MeshFilter mf = renderer.GetComponent<MeshFilter>();
                                        if (mf != null && mf.sharedMesh != null)
                                        {
                                            Debug.Log($"[AASKitImporter] 🔄 Rotating UVs for belt: {renderer.name}");
                                            RotateMeshUVs(mf.sharedMesh);
                                        }
                                    }

                                    // 2. Automatic Colliders
                                    MeshFilter filter = renderer.GetComponent<MeshFilter>();
                                    if (filter != null && filter.sharedMesh != null)
                                    {
                                        MeshCollider mc = renderer.gameObject.AddComponent<MeshCollider>();
                                        // A MeshCollider MUST be convex to collide with other Rigidbodies (like our spawned cube)
                                        mc.convex = true;
                                    }
                                }
                                
                                // Rigidbody for stability
                                Rigidbody rb = compObj.AddComponent<Rigidbody>();
                                
                                if (compName.ToLower().Contains("product") || compName.ToLower().Contains("magnetic")) {
                                    rb.isKinematic = false; // Let gravity work!
                                    rb.collisionDetectionMode = CollisionDetectionMode.Continuous;
                                    rb.constraints = RigidbodyConstraints.FreezeRotation; // Slide, don't roll
                                    Debug.Log($"[AASKitImporter] 📦 Configured {compName} as a Dynamic Product.");
                                } else {
                                    rb.isKinematic = true;
                                }

                                Debug.Log($"[AASKitImporter] Successfully loaded GLB: {localPath}");
                            }
                            else Debug.LogWarning($"[AASKitImporter] glTFast failed to load: {uri}");
                        }
                    }
                }
            }

            // 2. Second Pass: Set Hierarchy
            foreach (var kvp in parentMap)
            {
                if (!string.IsNullOrEmpty(kvp.Value) && components.ContainsKey(kvp.Value))
                    components[kvp.Key].transform.SetParent(components[kvp.Value].transform, false);
                else
                    components[kvp.Key].transform.SetParent(kitRoot.transform, false);
            }

            return new KitImportData { root = kitRoot, components = components };
        } catch (Exception e) {
            Debug.LogError($"[AASKitImporter] Fatal error parsing kit: {e}");
            return null;
        }
    }

    private static void RotateMeshUVs(Mesh mesh)
    {
        Vector2[] uvs = mesh.uv;
        for (int i = 0; i < uvs.Length; i++)
        {
            float oldX = uvs[i].x;
            uvs[i].x = uvs[i].y;
            uvs[i].y = 1.0f - oldX;
        }
        mesh.uv = uvs;
    }

    private static string ResolveMeshPath(string filename, string rootDir)
    {
        string clean = filename.Split(new[] { '/', '\\', '-' }).Last();
        if (System.IO.Directory.Exists(rootDir))
        {
            string[] allFiles = System.IO.Directory.GetFiles(rootDir, clean, System.IO.SearchOption.AllDirectories);
            if (allFiles.Length > 0) return allFiles[0];
        }
        return null;
    }
}
