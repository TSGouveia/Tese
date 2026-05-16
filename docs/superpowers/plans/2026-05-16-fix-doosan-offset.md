# Fix Doosan Joint Offset Implementation Plan

I'm using the writing-plans skill to create the implementation plan.

**Goal:** Fix the Doosan robot joint offset in Unity by aligning `AASUrdfImporter.cs` with the official Unity Robotics URDF Importer's order of operations and coordinate mapping.

**Architecture:**
- Create visual geometry **before** applying the origin transform (matches `UrdfVisualExtensions.cs`).
- Use `UrdfOrigin.ImportOriginData` logic (Translate then Rotate) for both joints and visuals.
- Ensure all coordinate conversions use official mappings from `UrdfOrigin` and `BuiltInExtensions`.

**Tech Stack:** C#, Unity, Unity Robotics URDF Importer.

---

### Task 1: Refactor AASUrdfImporter for Alignment

**Files:**
- Modify: `DT Unity/Assets/Scripts/AASUrdfImporter.cs`

- [ ] **Step 1: Update CreateLinkRecursive to apply origin correctly**

```csharp
    // Inside CreateLinkRecursive, for joints:
    GameObject jointAnchor = new GameObject("Joint_" + jointName);
    jointAnchor.transform.SetParent(linkObj.transform, false);

    XElement originXml = joint.Element("origin");
    if (originXml != null)
    {
        // Match UrdfOrigin.ImportOriginData logic: Translate then Rotate
        Vector3 pos = ParseVector3(originXml.Attribute("xyz")?.Value, Vector3.zero);
        Vector3 rpy = ParseVector3(originXml.Attribute("rpy")?.Value, Vector3.zero);
        
        jointAnchor.transform.Translate(pos.Ros2Unity());
        jointAnchor.transform.Rotate(new Vector3(rpy.y * Mathf.Rad2Deg, -rpy.z * Mathf.Rad2Deg, -rpy.x * Mathf.Rad2Deg));
    }
```

- [ ] **Step 2: Update CreateVisual to match official order and logic**

```csharp
    private static void CreateVisual(XElement visualXml, Transform parent, string urdfPath)
    {
        GameObject visObj = new GameObject("Visual");
        visObj.transform.SetParent(parent, false);

        XElement geometryXml = visualXml.Element("geometry");
        if (geometryXml != null)
        {
            try {
                Link.Geometry geometry = new Link.Geometry(geometryXml);
                if (geometry.mesh != null) geometry.mesh.filename = ResolveMeshPath(geometry.mesh.filename, urdfPath);

                GeometryTypes type = UrdfGeometry.GetGeometryType(geometry);
                // Create geometry first (handles scale and mesh-local transforms)
                UrdfGeometryVisual.Create(visObj.transform, type, geometry);
            }
            catch (Exception e) { Debug.LogWarning($"[AAS-URDF] Failed to create visual: {e.Message}"); }
        }

        // Apply origin AFTER geometry creation (matches UrdfVisualExtensions.cs)
        XElement originXml = visualXml.Element("origin");
        if (originXml != null)
        {
            Vector3 pos = ParseVector3(originXml.Attribute("xyz")?.Value, Vector3.zero);
            Vector3 rpy = ParseVector3(originXml.Attribute("rpy")?.Value, Vector3.zero);
            
            visObj.transform.Translate(pos.Ros2Unity());
            visObj.transform.Rotate(new Vector3(rpy.y * Mathf.Rad2Deg, -rpy.z * Mathf.Rad2Deg, -rpy.x * Mathf.Rad2Deg));
        }
    }
```

- [ ] **Step 3: Simplify and cleanup coordinate helpers**
Remove `RosToUnityPos` and `RosToUnityRot` and use the built-in extension methods or inline logic to match `UrdfOrigin`.

- [ ] **Step 4: Commit**

```bash
git add "DT Unity/Assets/Scripts/AASUrdfImporter.cs"
git commit -m "fix: align URDF import logic and order with official importer to resolve joint offsets"
```

### Task 2: Verification

- [ ] **Step 1: Re-import Doosan robot**
- [ ] **Step 2: Verify joint alignment and motion**
- [ ] **Step 3: Verify lerpSpeed is 1f by default**
