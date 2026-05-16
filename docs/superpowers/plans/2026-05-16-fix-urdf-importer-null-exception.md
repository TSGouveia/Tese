# Fix ArgumentNullException in AASUrdfImporter Implementation Plan

I'm using the writing-plans skill to create the implementation plan.

**Goal:** Fix the `System.ArgumentNullException` in `UrdfAssetPathHandler.GetRelativeAssetPathFromUrdfPath` by prepending `file://` to resolved mesh paths.

**Architecture:** The URDF Importer's `UrdfAssetPathHandler` requires `packageRoot` to be set if the path is not a URI. In runtime mode, `packageRoot` is often null. Prepending `file://` to absolute paths instructs the importer to use the path directly.

**Tech Stack:** C#, Unity, Unity Robotics URDF Importer.

---

### Task 1: Modify AASUrdfImporter to use file:// URIs

**Files:**
- Modify: `DT Unity/Assets/Scripts/AASUrdfImporter.cs:134-150`

- [ ] **Step 1: Update ResolveMeshPath to prepend file://**

```csharp
    private static string ResolveMeshPath(string filename, string urdfPath)
    {
        string clean = filename.Replace("package://", "");
        string rootDir = Path.GetDirectoryName(urdfPath);
        string fileNameOnly = Path.GetFileName(clean);
        
        string resolvedPath = null;
        
        // Strategy: Look for the file by searching from the URDF directory upwards
        // Optimization: check if it exists directly first
        string directPath = Path.Combine(rootDir, clean);
        if (File.Exists(directPath))
        {
            resolvedPath = directPath;
        }
        else
        {
            // Search in the robot's own directory first
            string[] candidates = Directory.GetFiles(rootDir, fileNameOnly, SearchOption.AllDirectories);
            foreach (var c in candidates)
            {
                if (c.Replace("\\", "/").EndsWith(clean)) 
                {
                    resolvedPath = c;
                    break;
                }
            }
        }

        if (resolvedPath == null) resolvedPath = Path.Combine(rootDir, clean);
        
        // Prepend file:// to avoid ArgumentNullException in UrdfAssetPathHandler
        return "file://" + resolvedPath.Replace("\\", "/");
    }
```

- [ ] **Step 2: Update CreateVisual to handle the URI correctly if needed**
Actually, `Link.Geometry` handles the path, and we are already passing it to `UrdfGeometryVisual.Create`. No other changes needed in `CreateVisual`.

- [ ] **Step 3: Commit**

```bash
git add "DT Unity/Assets/Scripts/AASUrdfImporter.cs"
git commit -m "fix: prepend file:// to mesh paths to avoid ArgumentNullException in URDF importer"
```

### Task 2: Verification

- [ ] **Step 1: Explain the fix to the user**
The `ArgumentNullException` happened because `UrdfAssetPathHandler.packageRoot` was null. Prepending `file://` bypasses the code path that uses `packageRoot`.
