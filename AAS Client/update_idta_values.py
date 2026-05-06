import json
import os
import glob
import re

class EditableItem:
    def __init__(self, file_path, submodel_id, id_short, element, model_type):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.submodel_id = submodel_id
        self.id_short = id_short
        self.element = element
        self.model_type = model_type

    def get_current_value(self):
        if self.model_type == 'Property' or self.model_type == 'File':
            return self.element.get('value', '(empty)')
        elif self.model_type == 'MultiLanguageProperty':
            values = self.element.get('value', [])
            en_vals = [v for v in values if v.get('language') == 'en']
            return en_vals[0].get('text', '(empty)') if en_vals else '(empty)'
        return "(non-editable type)"

    def update_value(self, new_value):
        if self.model_type == 'Property' or self.model_type == 'File':
            self.element['value'] = new_value
        elif self.model_type == 'MultiLanguageProperty':
            # Ensure we clear other languages and save only en
            self.element['value'] = [{"language": "en", "text": new_value}]

def collect_editable_elements(elements, file_path, submodel_id, items_list):
    for element in elements:
        id_short = element.get('idShort')
        if not id_short: continue
        
        m_type = element.get('modelType')
        if m_type in ['Property', 'MultiLanguageProperty', 'File']:
            items_list.append(EditableItem(file_path, submodel_id, id_short, element, m_type))
        elif m_type in ['SubmodelElementCollection', 'SubmodelElementList']:
            sub_elements = element.get('value', [])
            collect_editable_elements(sub_elements, file_path, f"{submodel_id} > {id_short}", items_list)

def find_folder_recursively(root, target_name):
    for dirpath, dirnames, filenames in os.walk(root):
        if target_name in dirnames:
            return os.path.join(dirpath, target_name)
    return None

def get_version_tuple(v_str):
    """Converts a version string like '3-0-1' into a list of integers for comparison."""
    try:
        return [int(x) for x in v_str.split('-')]
    except:
        return [0]

def filter_latest_versions(file_paths):
    """
    Groups files by template name and keeps only the highest version.
    Example: 'IDTA 02006-3-0_Template' vs 'IDTA 02006-3-0-1_Template'
    """
    pattern = re.compile(r"IDTA\s+(\d+)-([\d-]+)_Template_(.*)\.json")
    latest_files = {} # (id_number, template_name) -> (version_tuple, full_path)

    for path in file_paths:
        filename = os.path.basename(path)
        match = pattern.search(filename)
        
        if match:
            id_num = match.group(1)
            v_str = match.group(2)
            template_name = match.group(3).strip()
            v_tuple = get_version_tuple(v_str)
            
            key = (id_num, template_name)
            if key not in latest_files or v_tuple > latest_files[key][0]:
                latest_files[key] = (v_tuple, path)
        else:
            # If it doesn't follow IDTA pattern, always include it
            latest_files[path] = ([0], path)

    return [val[1] for val in latest_files.values()]

def main():
    print("\n" + "="*60)
    print("      INTERACTIVE INTERFACE - AAS / IDTA EDITOR")
    print("="*60)
    
    folder_name = input("Enter folder name: ")
    folder_path = find_folder_recursively(os.getcwd(), folder_name)
    
    if not folder_path:
        print(f"Error: Folder '{folder_name}' not found.")
        return

    all_json_paths = [f for f in glob.glob(os.path.join(folder_path, "**", "*.json"), recursive=True) 
                      if not f.endswith("_updated.json")]
    
    if not all_json_paths:
        print("No JSON files found.")
        return

    print("Filtering latest versions...")
    json_files_paths = filter_latest_versions(all_json_paths)
    print(f"Versions filtered: {len(all_json_paths)} -> {len(json_files_paths)}")

    all_data = {} # path -> json_data
    all_items = []

    print("Loading files and cleaning non-'en' languages...")
    for path in json_files_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data[path] = data
                
                # Collect elements
                if 'submodels' in data:
                    for sm in data['submodels']:
                        collect_editable_elements(sm.get('submodelElements', []), path, sm.get('idShort', 'SM'), all_items)
                elif 'submodelElements' in data:
                    collect_editable_elements(data['submodelElements'], path, data.get('idShort', 'SM'), all_items)
        except Exception as e:
            print(f"Error loading {os.path.basename(path)}: {e}")

    modified_files = set()

    while True:
        print("\n" + "-"*60)
        print(f"{'ID':<4} | {'File':<20} | {'Property':<25} | {'Current Value'}")
        print("-"*60)
        
        for idx, item in enumerate(all_items):
            val = item.get_current_value()
            # Truncate to avoid table formatting issues
            val_display = (val[:30] + '..') if isinstance(val, str) and len(val) > 30 else val
            print(f"{idx:<4} | {item.filename[:20]:<20} | {item.id_short[:25]:<25} | {val_display}")

        print("\nCommands: [ID] to edit | 'S' to Save and Exit | 'Q' to Quit without Saving")
        cmd = input("\nChoose an option: ").strip().lower()

        if cmd == 'q':
            print("Exit cancelled. Nothing was saved.")
            break
        elif cmd == 's':
            if not modified_files:
                print("No changes to save.")
                break
            
            for path in modified_files:
                data = all_data[path]
                base, ext = os.path.splitext(path)
                new_path = f"{base}_updated{ext}"
                try:
                    with open(new_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"Saved: {os.path.basename(new_path)}")
                except Exception as e:
                    print(f"Error saving {new_path}: {e}")
            print("\nAll changes have been saved to new files!")
            break
        
        try:
            item_idx = int(cmd)
            if 0 <= item_idx < len(all_items):
                target_item = all_items[item_idx]
                print(f"\nEditing: {target_item.id_short} (in {target_item.filename})")
                new_val = input(f"New value (current: '{target_item.get_current_value()}'): ").strip()
                
                if new_val:
                    target_item.update_value(new_val)
                    modified_files.add(target_item.file_path)
                    print("Value updated temporarily (not yet saved to disk).")
            else:
                print("Invalid ID.")
        except ValueError:
            print("Command not recognized.")

if __name__ == "__main__":
    main()
