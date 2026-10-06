# Layer 0: Physical Asset Digitization (3D Models)

This directory contains simulation-ready, low-polygon 3D CAD assets exported in the open **glTF 2.0 Binary (`.glb`)** format, modeled in Blender to match the physical modular Fischertechnik FMS testbed at a 1:1 metric scale.

## Asset Catalog

| File | Description | Role / Kinematics |
|---|---|---|
| `Conveyor_Belt.glb` | Linear conveyor belt module | Straight transport segment with sensor & stopper brackets |
| `Conveyor_Horizontal.glb` | Translating conveyor diverter module | Linear axis traversal for workpiece diversion |
| `Conveyor_Rotary.glb` | Rotating conveyor turntable module | Angular rotational axis for 90°/180° routing |
| `Punch_Station.glb` | Workpiece punch / machining station | Vertical linear stamping actuator and detection switches |
| `Workpiece.glb` | Cylindrical industrial puck / workpiece | Dynamic physics object transported across conveyor lines |

## Modeling Standards

- **Scale:** 1:1 metric units (1 Blender unit = 1 meter).
- **Origin & Pivots:** Aligned to kinematic rotation / translation centerlines for procedural assembly in Layer 3 (Unity 3D).
- **Format:** Self-contained GLB binary (embedded geometries and PBR materials).
- **Geometry Optimization:** Clean low-polygon topology optimized for high frame-rate PhysX simulation (>400 FPS).
