# Design Spec: AAS Backup & Restore Feature

## Overview
This feature introduces "Backup (Download)" and "Restore (Upload)" buttons to the "Manage Deployed AAS" dialog in the Conveyor Wizard. It allows users to export any deployed AAS (its entire configuration and its hosted 3D GLB model) into a single consolidated `.json` file. It also allows restoring the AAS from a backup file, either loading it directly into the wizard interface for editing, or deploying it straight back to the BaSyx registry/repository.

## Detailed Design

### 1. UI Additions in `ManageAASDialog`
Add two new buttons to the horizontal button layout of `manage_deployed_aas`:
- `btn_backup` ("Backup"): Colored blue (`#2980b9`). Connects to `on_backup_clicked`.
- `btn_restore` ("Restore"): Colored teal (`#16a085`). Connects to `on_restore_clicked`.

### 2. State Serialization & Deserialization
To load and save wizard configurations reliably, we implement two helper methods:
- `save_wizard_state(self)`: Serializes the current UI values (kit name, AAS ID, description, transform spinbox values, active actuators and sensors data) and `self.glb_path` into a dictionary.
- `restore_wizard_state(self, state)`: Wipes the current UI, updates text fields, spinboxes, reconstructs PyVista models, and builds corresponding actuator/sensor widgets from a serialized dictionary.

### 3. Backup (Download) Flow
1. Fetch shell descriptor, shell repo details, submodels (Visual, Pins, Behavior), and the GLB mesh attachment from BaSyx repository using `requests`.
2. Convert the GLB binary bytes to base64.
3. Build a consolidated JSON dictionary containing the config parameters and the `glb_base64` mesh.
4. Prompt user for target path via `QFileDialog.getSaveFileName`.
5. Save the JSON file.

### 4. Restore (Upload) Flow
1. Open `.json` file using `QFileDialog.getOpenFileName`.
2. Extract config parameters and decode `glb_base64` back into binary GLB. Write to a temporary file.
3. Show popup question asking if they want to:
   - **Load into Wizard (Yes):** Calls `restore_wizard_state()` to load the backup config and viewport. Close management dialog.
   - **Deploy directly to Server (No):** Save current wizard state, call `restore_wizard_state()` with backup, trigger `self.deploy_to_aas()` to upload AASX to BaSyx, restore previous wizard state, refresh AAS list.
   - **Cancel (Cancel):** Stop action.

## Verification
- Verify Backup button successfully saves a `.json` file containing both config parameters and encoded GLB.
- Verify Restore button prompts the popup question.
- Verify "Load into Wizard" correctly populates all widgets, sets viewport, and closes dialog.
- Verify "Deploy directly" uploads the AAS to the registry/repository without altering the user's active wizard viewport.
