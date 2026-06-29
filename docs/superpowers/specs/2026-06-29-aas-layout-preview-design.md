# Design Spec: AAS Layout Preview Feature

## Overview
This feature introduces a "Preview Deployed Layout" button to the start screen of the Conveyor Wizard. It queries all active AAS from the BaSyx servers, downloads their GLB meshes, applies their global coordinates (position, rotation, scale), and renders them simultaneously in the PyVista viewport. Actuator direction arrows are omitted in this mode to prevent visual clutter, presenting a clean layout preview of the factory floor.

## Detailed Design

### 1. UI Button on Start Screen
Add a new button to `setup_steps` on the first page of the wizard stack:
- `btn_preview_layout` ("Preview Deployed Layout"): Colored violet (`#8e44ad`). Connects to `preview_deployed_layout` method.

### 2. Layout Generation Flow
When `btn_preview_layout` is clicked:
1. Display the wait cursor.
2. Query active shell descriptors from registry (`http://localhost:8082/shell-descriptors`). If empty, inform the user and return.
3. Clear the PyVista plotter (`self.plotter.clear()`).
4. Re-initialize coordinate caching maps (`self.meshes = {}`, `self.actors = {}`, etc.).
5. Iterate through each shell descriptor:
   - Fetch the shell details from the repository (`http://localhost:8081/shells/{encoded_shell_id}`).
   - Extract and fetch the VisualStructure submodel details.
   - Read the VisualStructure `Transform` properties: PosX, PosY, PosZ, RotX, RotY, RotZ, ScaleX, ScaleY, ScaleZ.
   - Read the VisualStructure `Mesh` attachment filename and download the mesh bytes from the attachment endpoint.
   - Save the mesh to a temporary file.
   - Load the model using `trimesh.load()`.
   - Build a 4x4 transformation matrix `M` in numpy using `trimesh.transformations` translation, rotation (Euler sxyz), and scale functions.
   - Apply the transformation matrix to the trimesh scene (`scene.apply_transform(M)`).
   - Render the transformed meshes onto the main viewport plotter (mapping their material colors/textures).
   - Add a 3D point label containing the AAS name (`idShort`) floating at the center bounds of the transformed model.
6. Reset the camera to frame all rendered models (`self.plotter.reset_camera()`).
7. Restore the override wait cursor.
8. Show a success message detailing the number of loaded shells.

## Verification
- Verify the "Preview Deployed Layout" button appears correctly.
- Verify clicking it queries all active AAS.
- Verify models are loaded and translated correctly in the 3D viewport.
- Verify actuator arrows are not shown in this preview mode.
- Verify starting a new wizard task (e.g., clicking "Select GLB") clears the layout preview and functions normally.
