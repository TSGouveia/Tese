import json
import os
import glob

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
            return self.element.get('value', '(vazio)')
        elif self.model_type == 'MultiLanguageProperty':
            values = self.element.get('value', [])
            en_vals = [v for v in values if v.get('language') == 'en']
            return en_vals[0].get('text', '(vazio)') if en_vals else '(vazio)'
        return "(tipo não editável)"

    def update_value(self, new_value):
        if self.model_type == 'Property' or self.model_type == 'File':
            self.element['value'] = new_value
        elif self.model_type == 'MultiLanguageProperty':
            # Garante que limpamos outras línguas e guardamos apenas en
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

import re

def get_version_tuple(v_str):
    """Converte uma string de versão tipo '3-0-1' numa lista de inteiros para comparação."""
    try:
        return [int(x) for x in v_str.split('-')]
    except:
        return [0]

def filter_latest_versions(file_paths):
    """
    Agrupa ficheiros pelo nome do template e mantém apenas o que tem a versão mais alta.
    Exemplo: 'IDTA 02006-3-0_Template' vs 'IDTA 02006-3-0-1_Template'
    """
    pattern = re.compile(r"IDTA\s+(\d+)-([\d-]+)_Template_(.*)\.json")
    latest_files = {} # (id_numero, nome_template) -> (versao_tuple, full_path)

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
            # Se não segue o padrão IDTA, incluímos sempre para não perder ficheiros custom
            latest_files[path] = ([0], path)

    return [val[1] for val in latest_files.values()]

def main():
    print("\n" + "="*60)
    print("      INTERFACE INTERATIVA - EDITOR AAS / IDTA")
    print("="*60)
    
    folder_name = input("Introduza o nome da pasta: ")
    folder_path = find_folder_recursively(os.getcwd(), folder_name)
    
    if not folder_path:
        print(f"Erro: Pasta '{folder_name}' não encontrada.")
        return

    all_json_paths = [f for f in glob.glob(os.path.join(folder_path, "**", "*.json"), recursive=True) 
                      if not f.endswith("_updated.json")]
    
    if not all_json_paths:
        print("Nenhum ficheiro JSON encontrado.")
        return

    print("A filtrar versões mais recentes...")
    json_files_paths = filter_latest_versions(all_json_paths)
    print(f"Versões filtradas: {len(all_json_paths)} -> {len(json_files_paths)}")

    all_data = {} # path -> json_data
    all_items = []

    print("A carregar ficheiros e a limpar línguas não-'en'...")
    for path in json_files_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data[path] = data
                
                # Coleta elementos
                if 'submodels' in data:
                    for sm in data['submodels']:
                        collect_editable_elements(sm.get('submodelElements', []), path, sm.get('idShort', 'SM'), all_items)
                elif 'submodelElements' in data:
                    collect_editable_elements(data['submodelElements'], path, data.get('idShort', 'SM'), all_items)
        except Exception as e:
            print(f"Erro ao carregar {os.path.basename(path)}: {e}")

    modified_files = set()

    while True:
        print("\n" + "-"*60)
        print(f"{'ID':<4} | {'Ficheiro':<20} | {'Propriedade':<25} | {'Valor Atual'}")
        print("-"*60)
        
        for idx, item in enumerate(all_items):
            val = item.get_current_value()
            # Truncar para não desformatar a tabela
            val_display = (val[:30] + '..') if isinstance(val, str) and len(val) > 30 else val
            print(f"{idx:<4} | {item.filename[:20]:<20} | {item.id_short[:25]:<25} | {val_display}")

        print("\nComandos: [ID] para editar | 'S' para Gravar e Sair | 'Q' para Sair sem Gravar")
        cmd = input("\nEscolha uma opção: ").strip().lower()

        if cmd == 'q':
            print("Saída cancelada. Nada foi gravado.")
            break
        elif cmd == 's':
            if not modified_files:
                print("Nenhuma alteração para gravar.")
                break
            
            for path in modified_files:
                data = all_data[path]
                base, ext = os.path.splitext(path)
                new_path = f"{base}_updated{ext}"
                try:
                    with open(new_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"Gravado: {os.path.basename(new_path)}")
                except Exception as e:
                    print(f"Erro ao gravar {new_path}: {e}")
            print("\nTodas as alterações foram guardadas em novos ficheiros!")
            break
        
        try:
            item_idx = int(cmd)
            if 0 <= item_idx < len(all_items):
                target_item = all_items[item_idx]
                print(f"\nA editar: {target_item.id_short} (em {target_item.filename})")
                new_val = input(f"Novo valor (atual: '{target_item.get_current_value()}'): ").strip()
                
                if new_val:
                    target_item.update_value(new_val)
                    modified_files.add(target_item.file_path)
                    print("Valor atualizado temporariamente (ainda não gravado no disco).")
            else:
                print("ID inválido.")
        except ValueError:
            print("Comando não reconhecido.")

if __name__ == "__main__":
    main()
