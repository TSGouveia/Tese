# Fix Joint Offsets and Missing Materials Implementation Plan

I'm using the writing-plans skill to create the implementation plan.

**Goal:** Fix joint positioning/rotation and resolve missing materials (purple robots) by aligning coordinate conversions with the official URDF importer and ensuring material preparation is performed.

**Architecture:**
- Update `AASUrdfImporter` to use `UrdfOrigin`'s coordinate mapping logic.
- Ensure `BaSyxManager` calls `PrepareRobot` for custom-imported robots to apply correct shaders and materials.
- Align `AASRobotSync` joint rotation with the right-handed to left-handed conversion (negative angle).

**Tech Stack:** C#, Unity, Unity Robotics URDF Importer.

---

### Task 1: Update AASUrdfImporter Coordinate Conversion

**Files:**
- Modify: `DT Unity/Assets/Scripts/AASUrdfImporter.cs`

- [ ] **Step 1: Update RosToUnityRot to match UrdfOrigin**

```csharp
    private static Quaternion RosToUnityRot(Vector3 rpy)
    {
        // Matches UrdfOrigin.GetRotationFromUrdf: (Pitch, -Yaw, -Roll)
        // Unity Euler order is Y * X * Z
        return Quaternion.Euler(rpy.y * Mathf.Rad2Deg, -rpy.z * Mathf.Rad2Deg, -rpy.x * Mathf.Rad2Deg);
    }
```

- [ ] **Step 2: Update CreateVisual to use UrdfOrigin for consistency (Optional but safer)**
Actually, using `RosToUnityPos` and `RosToUnityRot` is fine if they are correct.

- [ ] **Step 3: Commit**

```bash
git add "DT Unity/Assets/Scripts/AASUrdfImporter.cs"
git commit -m "fix: align URDF rotation conversion with official importer logic"
```

### Task 2: Ensure Material Preparation in BaSyxManager

**Files:**
- Modify: `DT Unity/Assets/Scripts/BaSyxManager.cs`

- [ ] **Step 1: Call PrepareRobot after AASUrdfImporter.Import**

```csharp
            // USE CUSTOM IMPORTER (Python Logic)
            var importResult = AASUrdfImporter.Import(urdfFile, robotName);
            GameObject robotObj = importResult?.root;

            if (robotObj != null)
            {
                // Ensure materials and shaders are correctly applied
                PrepareRobot(robotObj, urdfFile);
                
                // ... rest of the logic ...
```

- [ ] **Step 2: Improve PrepareRobot to be more robust with shaders**

```csharp
        // ... inside PrepareRobot ...
        if (targetShader == null) 
        {
            Debug.LogWarning($"[BaSyx] âš ï¸ Shader '{shaderName}' not found! Falling back to 'Standard' or 'Hidden/InternalErrorShader' check.");
            targetShader = Shader.Find("Standard");
        }
```

- [ ] **Step 3: Commit**

```bash
git add "DT Unity/Assets/Scripts/BaSyxManager.cs"
git commit -m "fix: call PrepareRobot for custom imports to resolve missing materials"
```

### Task 3: Align AASRobotSync Rotation

**Files:**
- Modify: `DT Unity/Assets/Scripts/AASRobotSync.cs`

- [ ] **Step 1: Use negative angle for RH to LH conversion**

```csharp
    void Update()
    {
        foreach (var kvp in jointMap)
        {
            JointData data = kvp.Value;

            // SuavizaÃ§Ã£o do movimento
            data.currentAngle = Mathf.LerpAngle(data.currentAngle, data.targetAngle, Time.deltaTime * lerpSpeed);

            // AplicaÃ§Ã£o da rotaÃ§Ã£o baseada na pose inicial URDF
            // Use negative angle to match UrdfJoint's RH -> LH conversion
            data.transform.localRotation = data.initialRotation * Quaternion.AngleAxis(-data.currentAngle, data.axis);
        }
    }
```

- [ ] **Step 2: Commit**

```bash
git add "DT Unity/Assets/Scripts/AASRobotSync.cs"
git commit -m "fix: invert joint rotation angle to match Unity's coordinate system"
```

### Task 4: Verification

- [ ] **Step 1: Verify joint placement and motion**
- [ ] **Step 2: Verify material colors and shaders (no more purple)**
