import json
import os
import glob
import re
import customtkinter as ctk
from tkinter import messagebox

# Configuração de Aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if not self.text: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, justify="left", fg_color="#2c3e50",
                             text_color="#ecf0f1", corner_radius=4, padx=10, pady=6,
                             font=ctk.CTkFont(size=11), wraplength=300)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class EditableItem:
    def __init__(self, file_path, submodel_id, id_short, element, model_type, on_change_callback):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.id_short = id_short
        self.element = element
        self.model_type = model_type
        self.template_label = ""
        self.definition = self._extract_definition(element)

        initial_val = self.get_current_value()
        self.tk_var = ctk.StringVar(value=initial_val)
        self.tk_var.trace_add("write", lambda *args: on_change_callback(self.file_path))

    def _extract_definition(self, element):
        try:
            specs = element.get('embeddedDataSpecifications', [])
            for spec in specs:
                content = spec.get('dataSpecificationContent', {})
                definitions = content.get('definition', [])
                for d in definitions:
                    if d.get('language') == 'en': return d.get('text')
            return None
        except:
            return None

    def get_current_value(self):
        try:
            if self.model_type in ['Property', 'File']:
                val = self.element.get('value', '')
                return str(val) if val is not None else ""
            elif self.model_type == 'MultiLanguageProperty':
                values = self.element.get('value', [])
                en_vals = [v for v in values if isinstance(v, dict) and v.get('language') == 'en']
                return en_vals[0].get('text', '') if en_vals else (values[0].get('text', '') if values else '')
            return ""
        except:
            return ""

    def sync_to_json(self):
        new_val = self.tk_var.get()
        if self.model_type in ['Property', 'File']:
            self.element['value'] = new_val
        elif self.model_type == 'MultiLanguageProperty':
            self.element['value'] = [{"language": "en", "text": new_val}]


class AASApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AAS / IDTA Editor Pro")
        self.geometry("1100x850")
        self.all_data, self.all_items, self.modified_files, self.item_widgets = {}, [], set(), []
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1);
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="AAS Editor", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="Carregar Templates", command=self.auto_detect).pack(pady=10, padx=20,
                                                                                              fill="x")
        self.template_var = ctk.StringVar(value="Aguardando...")
        self.template_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.template_var, values=["Nenhum"],
                                               command=self.trigger_refresh)
        self.template_menu.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="SALVAR TUDO", fg_color="#27ae60", command=self.save_all).pack(pady=20,
                                                                                                        padx=20,
                                                                                                        fill="x")
        self.log_box = ctk.CTkTextbox(self.sidebar, height=200, font=ctk.CTkFont(size=10), fg_color="#121212")
        self.log_box.pack(pady=10, padx=15, fill="both", expand=True);
        self.log_box.configure(state="disabled")

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#141414")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1);
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.search_var = ctk.StringVar();
        self.search_var.trace_add("write", self.trigger_refresh)
        ctk.CTkEntry(self.main_frame, placeholder_text="Filtrar...", textvariable=self.search_var, height=35).grid(
            row=0, column=0, sticky="ew", padx=20, pady=15)
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def log(self, message):
        self.log_box.configure(state="normal");
        self.log_box.insert("end", f"> {message}\n");
        self.log_box.see("end");
        self.log_box.configure(state="disabled")

    def parse_version(self, path):
        """Extrai números de versão de uma string de caminho (ex: '3.0.1' -> [3, 0, 1])."""
        parts = re.findall(r'\d+', path)
        return [int(p) for p in parts] if parts else [0]

    def auto_detect(self):
        root = os.path.join(os.getcwd(), "AAS_TEMPLATES")
        if not os.path.exists(root):
            messagebox.showwarning("Erro", "Pasta 'AAS_TEMPLATES' não encontrada.");
            return

        self.all_data.clear();
        self.all_items.clear();
        self.modified_files.clear()
        all_json = glob.glob(os.path.join(root, "**", "*.json"), recursive=True)

        # Agrupar por Template Name para encontrar a versão mais recente
        template_groups = {}
        for p in all_json:
            if "_updated.json" in p: continue

            # Remove a parte da versão do caminho para identificar o 'nome' do template
            # Ex: 'DigitalNameplate/3.0.1/file.json' -> 'DigitalNameplate'
            rel_path = os.path.relpath(p, root)
            path_parts = rel_path.split(os.sep)

            # O nome do template é o diretório pai que não é versão
            name_parts = [part for part in path_parts[:-1] if not re.match(r'^[\d\._-]+$', part)]
            tpl_key = " > ".join(name_parts) if name_parts else "Geral"

            if tpl_key not in template_groups: template_groups[tpl_key] = []
            template_groups[tpl_key].append(p)

        # Selecionar apenas o ficheiro com a maior versão para cada grupo
        final_paths = []
        for key, paths in template_groups.items():
            # Ordena pelo parse da versão contida no caminho completo
            latest = max(paths, key=self.parse_version)
            final_paths.append((key, latest))
            self.log(f"Template '{key}' -> Versão detectada: {os.path.basename(os.path.dirname(latest))}")

        for label, path in final_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.all_data[path] = data
                    temp = []
                    if 'submodels' in data:
                        self.collect_elements(data['submodels'], path, "AAS", temp, True)
                    elif 'submodelElements' in data:
                        self.collect_elements(data['submodelElements'], path, "SM", temp)
                    for i in temp: i.template_label = label; self.all_items.append(i)
            except Exception as e:
                self.log(f"Erro em {path}: {e}")

        labels = sorted(list(set(i.template_label for i in self.all_items)))
        self.template_menu.configure(values=labels)
        if labels: self.template_var.set(labels[0]); self.refresh_ui()

    def collect_elements(self, elements, path, parent_id, target, is_sm_list=False):
        if is_sm_list:
            for sm in elements:
                if isinstance(sm, dict) and 'submodelElements' in sm:
                    self.collect_elements(sm['submodelElements'], path, sm.get('idShort', 'SM'), target)
            return
        for el in elements:
            if not isinstance(el, dict): continue
            id_s, m_t = el.get('idShort'), el.get('modelType')
            if id_s and m_t in ['Property', 'MultiLanguageProperty', 'File']:
                target.append(EditableItem(path, parent_id, id_s, el, m_t, lambda p: self.modified_files.add(p)))
            elif m_t in ['SubmodelElementCollection', 'SubmodelElementList']:
                self.collect_elements(el.get('value', []), path, id_s, target)

    def trigger_refresh(self, *args):
        self.refresh_ui()

    def clear_ui(self):
        for w in self.item_widgets: w.destroy()
        self.item_widgets.clear()

    def refresh_ui(self):
        tpl = self.template_var.get()
        if tpl in ["Aguardando...", "Nenhum"]: return
        self.clear_ui();
        query = self.search_var.get().lower();
        curr_f = ""
        for item in self.all_items:
            if item.template_label != tpl or (query and query not in item.id_short.lower()): continue
            if item.file_path != curr_f:
                curr_f = item.file_path
                h = ctk.CTkLabel(self.scrollable_frame, text=f"📄 {item.filename} (Versão Ativa)",
                                 font=ctk.CTkFont(size=10, weight="bold"), text_color="#3498db")
                h.pack(fill="x", pady=(10, 2), padx=5);
                self.item_widgets.append(h)
            row = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=1)
            l_clr = "#9b59b6" if item.definition else "white"
            lbl = ctk.CTkLabel(row, text=f"{item.id_short}:", width=180, anchor="w", font=ctk.CTkFont(size=11),
                               text_color=l_clr)
            lbl.pack(side="left", padx=(5, 2))
            if item.definition: Tooltip(lbl, item.definition)
            ent = ctk.CTkEntry(row, textvariable=item.tk_var, height=24, font=ctk.CTkFont(size=11), border_width=1)
            ent.pack(side="left", fill="x", expand=True, padx=2)
            self.item_widgets.append(row)

    def save_all(self):
        if not self.modified_files: return
        for item in self.all_items:
            if item.file_path in self.modified_files: item.sync_to_json()
        for path in self.modified_files:
            new_p = path.replace(".json", "_updated.json")
            with open(new_p, 'w', encoding='utf-8') as f:
                json.dump(self.all_data[path], f, indent=2, ensure_ascii=False)
            self.log(f"Salvo: {os.path.basename(new_p)}")
        messagebox.showinfo("Sucesso", "Ficheiros guardados!")
        self.modified_files.clear()


if __name__ == "__main__":
    AASApp().mainloop()