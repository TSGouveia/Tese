# Fix Doosan Joint Offset (Rigorous Math) Implementation Plan

I'm using the writing-plans skill to create the implementation plan.

**Goal:** Fix the remaining joint offset issue on the Doosan robot by replacing Unity's `Quaternion.Euler` with an exact, mathematically rigorous implementation of the ROS (Intrinsic Z-Y-X / Extrinsic X-Y-Z) to Unity left-handed quaternion conversion.

**Architecture:**
- Unity's `Quaternion.Euler` and `Transform.Rotate` can sometimes introduce ambiguity or slight flipping depending on internal order and Euler angle singularities (Gimbal lock).
- To guarantee 100% fidelity to the Python `urdfpy` library, I will manually construct the Right-Handed quaternion from URDF RPY, and then apply the official `Ros2Unity` mapping `(y, -z, -x, w)`.

**Tech Stack:** C#, Unity.

---

### Task 1: Rigorous Quaternion Math in AASUrdfImporter

**Files:**
- Modify: `DT Unity/Assets/Scripts/AASUrdfImporter.cs`

- [ ] **Step 1: Implement RosToUnityRot with exact math**

```csharp
    private static Quaternion RosToUnityRot(Vector3 rpy)
    {
        // URDF RPY is Extrinsic X-Y-Z (or Intrinsic Z-Y-X) in a Right-Handed system.
        double roll = rpy.x;
        double pitch = rpy.y;
        double yaw = rpy.z;

        double cy = Math.Cos(yaw * 0.5);
        double sy = Math.Sin(yaw * 0.5);
        double cp = Math.Cos(pitch * 0.5);
        double sp = Math.Sin(pitch * 0.5);
        double cr = Math.Cos(roll * 0.5);
        double sr = Math.Sin(roll * 0.5);

        // Intrinsic Z-Y-X quaternion multiplication
        double q_x = sr * cp * cy - cr * sp * sy;
        double q_y = cr * sp * cy + sr * cp * sy;
        double q_z = cr * cp * sy - sr * sp * cy;
        double q_w = cr * cp * cy + sr * sp * sy;

        // Convert to Unity's Left-Handed coordinate system
        // Mapping: X_unity = -Y_ros, Y_unity = Z_ros, Z_unity = X_ros
        // Quaternion mapping: (q_y, -q_z, -q_x, q_w)
        return new Quaternion((float)q_y, (float)-q_z, (float)-q_x, (float)q_w);
    }
```

- [ ] **Step 2: Replace Quaternion.Euler calls with RosToUnityRot**

```csharp
    // Inside CreateLinkRecursive and CreateVisual:
    jointAnchor.transform.localRotation = RosToUnityRot(rpy);
    // ...
    visObj.transform.localRotation = RosToUnityRot(rpy);
```

- [ ] **Step 3: Commit**

```bash
git add "DT Unity/Assets/Scripts/AASUrdfImporter.cs"
git commit -m "fix: implement rigorous math for ROS to Unity quaternion conversion to eliminate joint offsets"
```

### Task 2: Verification

- [ ] **Step 1: Explain the math to the user.**
