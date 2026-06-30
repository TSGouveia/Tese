# Design Spec: Always on Top Option in AAS PLC Studio

## Goal
Add an option to AAS PLC Studio to keep the window always on top of other windows.

## UI Design
- **Location**: In the sidebar list of the application, directly below the "Refresh Registry" button.
- **Type**: A checkbox with the label "📌 Always on Top".
- **Styling**: Styled using PyQt6 stylesheets to match the existing dark, high-contrast theme of the dashboard.

## Implementation Details
1. **Imports**: Add `QCheckBox` to imports from `PyQt6.QtWidgets`.
2. **Setup**: Instantiate `QCheckBox("📌 Always on Top")`, connect its `toggled` signal to the `toggle_always_on_top` slot, and add it to `sidebar_layout`.
3. **Logic**:
   - Create a method `toggle_always_on_top(self, checked)`:
     ```python
     def toggle_always_on_top(self, checked):
         flags = self.windowFlags()
         if checked:
             self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
         else:
             self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
         self.show()
     ```
   - This dynamically toggles the `Qt.WindowType.WindowStaysOnTopHint` flag and calls `show()` to re-render the window with the new flags on Windows.
