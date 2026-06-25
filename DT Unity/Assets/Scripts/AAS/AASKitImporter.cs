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

            // 1. First Pass: Create/Find GameObjects and Load GLBs
            foreach (JToken token in elements)
            {
                string compName = token["idShort"]?.ToString();
                if (string.IsNullOrEmpty(compName)) continue;

                string meshFile = "";
                string parentName = "";
                Vector3 pos = Vector3.zero;
                Vector3 rot = Vector3.zero;
                Vector3 scale = Vector3.one;

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
                                if (tId == "ScaleX") scale.x = v; if (tId == "ScaleY") scale.y = v; if (tId == "ScaleZ") scale.z = v;
                            }
                        }
                    }
                }

                GameObject compObj = null;
                bool wasPreExisting = false;
                
                // CRITICAL FIX: Search for this component name across ALL already loaded 
                // mesh hierarchies in this kit BEFORE creating a new one.
                foreach (var existing in components.Values) {
                    if (existing == null) continue;
                    // Check if the 'existing' object itself is the target, or one of its children
                    if (existing.name == compName) {
                        compObj = existing;
                        wasPreExisting = true;
                        break;
                    }
                    var found = existing.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == compName);
                    if (found != null) {
                        compObj = found.gameObject;
                        wasPreExisting = true;
                        break;
                    }
                }

                // If not found in existing meshes, and it HAS a mesh file, create a new container
                if (compObj == null && !string.IsNullOrEmpty(meshFile)) 
                {
                    compObj = new GameObject(compName);
                } 
                // If still not found and has NO mesh (virtual node), create it only as a last resort
                else if (compObj == null)
                {
                    compObj = new GameObject(compName);
                }

                components[compName] = compObj;
                parentMap[compName] = parentName;

                if (!wasPreExisting)
                {
                    // Standard Z-up (AAS) to Y-up (Unity) conversion
                    compObj.transform.localPosition = new Vector3(pos.x, pos.z, pos.y);
                    compObj.transform.localEulerAngles = new Vector3(rot.x, rot.z, rot.y);
                    compObj.transform.localScale = new Vector3(scale.x, scale.z, scale.y);
                }
                else 
                {
                    Debug.Log($"[AASKitImporter] 🧊 Found '{compName}' inside GLB. Preserving Blender transform and hierarchy.");
                }

                if (!string.IsNullOrEmpty(meshFile) && !wasPreExisting)
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
                GameObject child = components[kvp.Key];
                Transform targetParent = null;

                if (!string.IsNullOrEmpty(kvp.Value) && components.ContainsKey(kvp.Value))
                    targetParent = components[kvp.Value].transform;
                else
                    targetParent = kitRoot.transform;

                // LOGIC UPDATE: If the child is already a sub-object from Blender
                // and its CURRENT parent is also part of this kit, we DON'T re-parent.
                // This preserves functional hierarchies (like Drill being child of a Move axis).
                bool currentParentIsKitPart = child.transform.parent != null && 
                                              components.Values.Any(c => c.transform == child.transform.parent);
                
                // NEW: Also check if it's already a descendant of the target parent (deep hierarchy)
                bool isAlreadyDescendant = child.transform.IsChildOf(targetParent);

                if (child.transform.parent != targetParent && !currentParentIsKitPart && !isAlreadyDescendant)
                {
                    child.transform.SetParent(targetParent, true);
                    Debug.Log($"[AASKitImporter] 🔗 SetParent for {kvp.Key} to {targetParent.name} (New Root/Manual Parent)");
                }
                else if (isAlreadyDescendant && child.transform.parent != targetParent)
                {
                    Debug.Log($"[AASKitImporter] 🧬 Preserving nested Blender hierarchy for {kvp.Key} (already descendant of {targetParent.name})");
                }
                else if (currentParentIsKitPart && child.transform.parent != targetParent)
                {
                    Debug.Log($"[AASKitImporter] 🧬 Preserving functional Blender hierarchy for {kvp.Key} (Parent: {child.transform.parent.name})");
                }
            }

            // FINAL STEP: Normalize the entire kit hierarchy.
            // This bakes all scales into meshes and resets all transforms to (1,1,1).
            // This is CRITICAL to prevent rotation shearing (skewing) in Unity.
            NormalizeHierarchy(kitRoot.transform);

            return new KitImportData { root = kitRoot, components = components };
        } catch (Exception e) {
            Debug.LogError($"[AASKitImporter] Fatal error parsing kit: {e}");
            return null;
        }
    }

    private static void NormalizeHierarchy(Transform root)
    {
        if (root == null) return;

        // Process this node
        Vector3 localScale = root.localScale;
        
        // 1. Bake any mesh on THIS specific node using its local scale
        BakeMeshesOnObject(root.gameObject, localScale);

        // 2. If this node has scale, we must reset it and fix children
        if (Vector3.Distance(localScale, Vector3.one) > 0.0001f)
        {
            // Capture children
            List<Transform> children = new List<Transform>();
            for (int i = 0; i < root.childCount; i++) children.Add(root.GetChild(i));

            // Detach children to world space (Unity preserves their world transform)
            foreach (var c in children) c.SetParent(null, true);
            
            // Reset parent scale
            root.localScale = Vector3.one;
            
            // Re-attach children (Unity calculates new local scales/positions)
            foreach (var c in children) c.SetParent(root, true);
            
            Debug.Log($"[AASKitImporter] 🧼 Normalized scale for node: {root.name}");
        }

        // 3. Recurse to children (they might now have new local scales inherited from step 2)
        // We use a copy of the child list to avoid issues with hierarchy changes
        List<Transform> next = new List<Transform>();
        for (int i = 0; i < root.childCount; i++) next.Add(root.GetChild(i));
        foreach (var n in next) NormalizeHierarchy(n);
    }

    private static void BakeMeshesOnObject(GameObject obj, Vector3 scale)
    {
        if (Vector3.Distance(scale, Vector3.one) <= 0.0001f) return;

        // Handle standard MeshFilters
        foreach (var mf in obj.GetComponents<MeshFilter>())
        {
            if (mf.sharedMesh != null)
            {
                mf.sharedMesh = BakeMeshInstance(mf.sharedMesh, scale);
                // Sync MeshColliders
                foreach (var mc in obj.GetComponents<MeshCollider>())
                {
                    if (mc.sharedMesh != null) mc.sharedMesh = mf.sharedMesh;
                }
            }
        }

        // Handle SkinnedMeshRenderers (sometimes used in GLBs)
        foreach (var smr in obj.GetComponents<SkinnedMeshRenderer>())
        {
            if (smr.sharedMesh != null)
            {
                smr.sharedMesh = BakeMeshInstance(smr.sharedMesh, scale);
            }
        }
    }

    private static Mesh BakeMeshInstance(Mesh original, Vector3 scale)
    {
        Mesh mesh = Instantiate(original);
        Vector3[] v = mesh.vertices;
        for (int i = 0; i < v.Length; i++)
        {
            v[i] = Vector3.Scale(v[i], scale);
        }
        mesh.vertices = v;
        mesh.RecalculateBounds();
        mesh.RecalculateNormals();
        mesh.RecalculateTangents();
        return mesh;
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
