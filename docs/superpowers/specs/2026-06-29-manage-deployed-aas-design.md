# Design Spec: Manage Deployed AAS Feature

## Overview
Currently, the Conveyor Wizard has a "Clone Existing AAS" button that allows importing an existing AAS configuration from the server into the wizard. However, there is no way for the user to delete or manage these deployed AAS files directly from the UI.
This feature replaces the "Clone Existing AAS" button with a "Manage Deployed AAS" button which opens a dialog listing all deployed AAS. From this dialog, the user can select an AAS and either:
1. **Clone & Edit**: Load its configuration into the wizard (reusing the existing clone logic).
2. **Delete**: Wipe the AAS (shell, registry descriptor, submodels, submodel descriptors) from the server after confirmation.

## Detailed Design

### 1. Main Page UI Changes
In `conveyor_wizard.py` ([setup_steps](file:///C:/Users/LazyT/Desktop/Tese/AAS%20Client/conveyor_wizard.py#L301)):
- Remove `self.btn_clone_aas` ("Clone Existing AAS") and replace it with `self.btn_manage_aas` ("Manage Deployed AAS").
- Connect `self.btn_manage_aas.clicked` to a new method `self.manage_deployed_aas`.

### 2. Manage AAS Dialog (`ManageAASDialog`)
A PyQt5 `QDialog` that displays:
- A `QListWidget` with the deployed AAS shells fetched from the registry (`http://localhost:8082/shell-descriptors`).
- Details stored in item metadata (using `Qt.ItemDataRole.UserRole`).
- Actions:
  - **Clone & Edit (Button):** Triggers loading data into the wizard and closes the dialog.
  - **Delete AAS (Button):** Wipes the selected AAS and associated submodels, then refreshes the list.
  - **Close (Button):** Closes the dialog.

### 3. Server Deletion Flow
When **Delete** is clicked on a selected AAS descriptor:
1. Confirm action: *"Are you sure you want to delete AAS '{idShort}' and all its submodels?"*
2. Encode shell ID to URL-safe Base64:
   ```python
   encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")
   ```
3. Fetch shell details from repo to list associated submodel references:
   ```http
   GET http://localhost:8081/shells/{encoded_shell_id}
   ```
4. For each submodel reference found:
   - Delete submodel from repository:
     ```http
     DELETE http://localhost:8081/submodels/{encoded_sm_id}
     ```
   - Delete submodel descriptor from registry:
     ```http
     DELETE http://localhost:8083/submodel-descriptors/{encoded_sm_id}
     ```
5. Delete shell from repository:
   ```http
   DELETE http://localhost:8081/shells/{encoded_shell_id}
   ```
6. Delete shell descriptor from registry:
   ```http
   DELETE http://localhost:8082/shell-descriptors/{encoded_shell_id}
   ```
7. Show success popup and refresh the list in the dialog.

## Verification
- Verify the button displays correctly on the start page.
- Verify clicking it fetches and lists all current AAS from the registry.
- Verify clicking "Clone & Edit" works exactly like the old clone logic.
- Verify deleting an AAS works, cleans up both shells and submodels in both repo/registry, and refreshes the list.
