"""
Diálogo GUI para buscar y seleccionar plantillas de vehículos.
Selector Marca → Modelo → Año con búsqueda en múltiples fuentes.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import db
from .downloader import DownloadManager
from .providers import ALL_PROVIDERS, get_provider, get_image_providers
from .providers.base import BlueprintSearchResult
from .providers.carquery import CarQueryProvider


class VehicleBlueprintSelector(tk.Toplevel):
    """Ventana modal para buscar y seleccionar plantillas de vehículos."""

    def __init__(self, parent, on_select_callback, initial_make="",
                 initial_model=""):
        super().__init__(parent)
        self.title("Buscar Plantilla de Vehículo")
        self.geometry("950x650")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.on_select = on_select_callback
        self.dm = DownloadManager()
        self.carquery = CarQueryProvider()
        self.results = []
        self._selected_result = None
        self._is_online = True

        # Estilos
        style = ttk.Style()
        style.configure("Search.TButton", font=("Segoe UI", 9, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 8))

        self._build_ui()
        self._load_makes(initial_make, initial_model)

    def _build_ui(self):
        """Construye toda la interfaz."""
        pad = {"padx": 6, "pady": 3}

        # ============= PANEL SUPERIOR: Búsqueda =============
        frame_search = ttk.LabelFrame(self, text="  Buscar vehículo  ")
        frame_search.pack(fill="x", padx=8, pady=(8, 4))

        # Fila 1: Marca + Modelo + Año
        row1 = ttk.Frame(frame_search)
        row1.pack(fill="x", padx=5, pady=5)

        ttk.Label(row1, text="Marca:").pack(side="left", **pad)
        self.var_make = tk.StringVar()
        self.combo_make = ttk.Combobox(row1, textvariable=self.var_make,
                                        width=20, state="normal")
        self.combo_make.pack(side="left", **pad)
        self.combo_make.bind("<<ComboboxSelected>>", self._on_make_changed)
        self.combo_make.bind("<Return>", self._on_make_changed)

        ttk.Label(row1, text="Modelo:").pack(side="left", **pad)
        self.var_model = tk.StringVar()
        self.combo_model = ttk.Combobox(row1, textvariable=self.var_model,
                                         width=20, state="normal")
        self.combo_model.pack(side="left", **pad)

        ttk.Label(row1, text="Año:").pack(side="left", **pad)
        self.var_year = tk.StringVar()
        self.combo_year = ttk.Combobox(row1, textvariable=self.var_year,
                                        width=8, state="normal")
        self.combo_year.pack(side="left", **pad)

        ttk.Button(row1, text="Buscar", style="Search.TButton",
                   command=self._do_search).pack(side="left", padx=10)

        # Fila 2: Filtros
        row2 = ttk.Frame(frame_search)
        row2.pack(fill="x", padx=5, pady=(0, 5))

        self.var_solo_gratis = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="Solo gratuitos",
                        variable=self.var_solo_gratis).pack(side="left", **pad)

        self.var_solo_cache = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="Solo descargados",
                        variable=self.var_solo_cache,
                        command=self._toggle_cache_view).pack(side="left", **pad)

        ttk.Button(row2, text="Importar carpeta MR-Clipart",
                   command=self._import_mr_clipart).pack(side="right", **pad)

        # ============= PANEL CENTRAL: Resultados =============
        frame_results = ttk.LabelFrame(self, text="  Resultados  ")
        frame_results.pack(fill="both", expand=True, padx=8, pady=4)

        # Treeview de resultados
        columns = ("fuente", "tipo", "formato", "año", "gratis", "descripcion")
        self.tree = ttk.Treeview(frame_results, columns=columns,
                                  show="headings", height=12)
        self.tree.heading("fuente", text="Fuente")
        self.tree.heading("tipo", text="Vista")
        self.tree.heading("formato", text="Formato")
        self.tree.heading("año", text="Año")
        self.tree.heading("gratis", text="Gratis")
        self.tree.heading("descripcion", text="Descripción")

        self.tree.column("fuente", width=160)
        self.tree.column("tipo", width=80)
        self.tree.column("formato", width=60)
        self.tree.column("año", width=50)
        self.tree.column("gratis", width=50)
        self.tree.column("descripcion", width=350)

        scroll_tree = ttk.Scrollbar(frame_results, orient="vertical",
                                     command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_tree.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_tree.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_result_selected)

        # ============= PANEL INFERIOR: Dimensiones + Acciones =============
        frame_bottom = ttk.Frame(self)
        frame_bottom.pack(fill="x", padx=8, pady=(4, 8))

        # Dimensiones
        frame_dims = ttk.LabelFrame(frame_bottom, text="  Dimensiones  ")
        frame_dims.pack(side="left", fill="x", expand=True, padx=(0, 5))

        dims_inner = ttk.Frame(frame_dims)
        dims_inner.pack(padx=5, pady=5)

        self.var_length = tk.StringVar(value="-")
        self.var_width = tk.StringVar(value="-")
        self.var_height = tk.StringVar(value="-")
        self.var_wheelbase = tk.StringVar(value="-")
        self.var_weight = tk.StringVar(value="-")

        for i, (label, var) in enumerate([
            ("Longitud:", self.var_length),
            ("Anchura:", self.var_width),
            ("Altura:", self.var_height),
            ("Batalla:", self.var_wheelbase),
            ("Peso:", self.var_weight),
        ]):
            ttk.Label(dims_inner, text=label).grid(row=0, column=i * 2, **pad)
            ttk.Label(dims_inner, textvariable=var,
                      font=("Segoe UI", 9, "bold")).grid(
                row=0, column=i * 2 + 1, **pad)

        # Botones de acción
        frame_actions = ttk.Frame(frame_bottom)
        frame_actions.pack(side="right", padx=(5, 0))

        ttk.Button(frame_actions, text="Descargar y Usar",
                   style="Search.TButton",
                   command=self._do_download_and_select).pack(pady=3)
        ttk.Button(frame_actions, text="Cancelar",
                   command=self.destroy).pack(pady=3)

        # Barra de progreso
        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", padx=8, pady=(0, 2))

        # Status
        self.var_status = tk.StringVar(value="Introduce marca y modelo para buscar")
        ttk.Label(self, textvariable=self.var_status,
                  style="Status.TLabel").pack(fill="x", padx=8, pady=(0, 5))

    # =========================================================================
    # CARGA INICIAL
    # =========================================================================

    def _load_makes(self, initial_make="", initial_model=""):
        """Carga la lista de marcas (BD + CarQuery)."""
        self.var_status.set("Cargando marcas...")

        def _load():
            # Primero desde BD local
            makes_db = db.get_makes()
            make_names = sorted(set(m["name"] for m in makes_db))

            # Luego desde CarQuery en background
            try:
                makes_api = self.carquery.get_makes()
                for m in makes_api:
                    db.save_make(m["name"], m["display"], "carquery")
                    if m["name"].upper() not in [n.upper() for n in make_names]:
                        make_names.append(m["name"].upper())
                make_names.sort()
                self._is_online = True
            except Exception:
                self._is_online = False

            return sorted(set(make_names))

        def _done(makes):
            self.combo_make["values"] = makes
            if initial_make:
                # Buscar coincidencia parcial
                for m in makes:
                    if initial_make.upper() in m.upper():
                        self.var_make.set(m)
                        self._on_make_changed(None)
                        break
            if initial_model:
                self.var_model.set(initial_model)
            status = "Listo" if self._is_online else "Modo offline - solo datos locales"
            self.var_status.set(status)

        self._run_in_thread(_load, _done)

    def _on_make_changed(self, event):
        """Al cambiar la marca, cargar modelos."""
        make = self.var_make.get().strip()
        if not make:
            return

        self.var_status.set(f"Cargando modelos de {make}...")

        def _load():
            # BD local
            models_db = db.get_models(make_name=make)
            model_names = sorted(set(m["name"] for m in models_db))

            # CarQuery
            try:
                models_api = self.carquery.get_models(make)
                make_id = db.save_make(make, source="carquery")
                for m in models_api:
                    db.save_model(make_id, m["name"], source="carquery")
                    if m["name"] not in model_names:
                        model_names.append(m["name"])
                model_names.sort()
            except Exception:
                pass

            return model_names

        def _done(models):
            self.combo_model["values"] = models
            self.var_status.set(f"{len(models)} modelos para {make}")

        self._run_in_thread(_load, _done)

    # =========================================================================
    # BÚSQUEDA
    # =========================================================================

    def _do_search(self):
        """Busca en todos los proveedores en paralelo."""
        make = self.var_make.get().strip()
        model = self.var_model.get().strip()
        if not make or not model:
            messagebox.showwarning("Búsqueda", "Introduce marca y modelo.")
            return

        year_str = self.var_year.get().strip()
        year = int(year_str) if year_str.isdigit() else None

        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.var_status.set("Buscando en todas las fuentes...")
        self.progress["value"] = 0

        solo_gratis = self.var_solo_gratis.get()

        def _search():
            all_results = []
            providers = get_image_providers() if solo_gratis else ALL_PROVIDERS
            if solo_gratis:
                providers = [p for p in providers if p.is_free]

            # Buscar dimensiones
            dims = self.dm.fetch_dimensions(make, model, year)

            # Buscar blueprints locales primero
            local = db.find_blueprint(make, model, year)
            for bp in local:
                if os.path.exists(bp["file_path"]):
                    all_results.append(BlueprintSearchResult(
                        source_key=bp["source_key"],
                        source_name=f"{bp['source_key']} (Descargado)",
                        make=make, model=model, year=bp.get("year"),
                        download_url=bp["file_path"],
                        file_format=bp.get("file_format", ""),
                        view_type=bp.get("view_type", "mixed"),
                        description=f"[Local] {os.path.basename(bp['file_path'])}",
                        is_free=True,
                        extra_data={"local": True, "blueprint_id": bp["id"]},
                    ))

            # Buscar en proveedores en paralelo
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(p.search, make, model, year): p
                    for p in providers
                }
                for future in as_completed(futures):
                    try:
                        provider_results = future.result()
                        all_results.extend(provider_results)
                    except Exception as e:
                        print(f"Error en proveedor: {e}")

            return all_results, dims

        def _done(data):
            results, dims = data
            self.results = results

            # Mostrar dimensiones
            if dims:
                self.var_length.set(f"{dims.get('length_mm', '-')} mm")
                self.var_width.set(f"{dims.get('width_mm', '-')} mm")
                self.var_height.set(f"{dims.get('height_mm', '-')} mm")
                self.var_wheelbase.set(f"{dims.get('wheelbase_mm', '-')} mm")
                self.var_weight.set(f"{dims.get('weight_kg', '-')} kg")

            # Poblar treeview
            for i, r in enumerate(results):
                # No mostrar resultados de solo dimensiones en la tabla
                if r.file_format == "data":
                    continue

                self.tree.insert("", "end", iid=str(i), values=(
                    r.source_name,
                    r.view_type,
                    r.file_format,
                    r.year or "-",
                    "Sí" if r.is_free else "No",
                    r.description[:60],
                ))

            total = len([r for r in results if r.file_format != "data"])
            self.var_status.set(
                f"{total} resultados encontrados para {make} {model}")
            self.progress["value"] = 100

        self._run_in_thread(_search, _done)

    def _toggle_cache_view(self):
        """Muestra solo plantillas descargadas."""
        if self.var_solo_cache.get():
            self.tree.delete(*self.tree.get_children())
            cached = db.get_cached_blueprints(
                make=self.var_make.get().strip() or None,
                model=self.var_model.get().strip() or None)

            self.results = []
            for i, bp in enumerate(cached):
                if not os.path.exists(bp["file_path"]):
                    continue
                r = BlueprintSearchResult(
                    source_key=bp["source_key"],
                    source_name=f"{bp['source_key']} (Local)",
                    make=bp["make_name"], model=bp["model_name"],
                    year=bp.get("year"),
                    download_url=bp["file_path"],
                    file_format=bp.get("file_format", ""),
                    view_type=bp.get("view_type", "mixed"),
                    description=os.path.basename(bp["file_path"]),
                    is_free=True,
                    extra_data={"local": True, "blueprint_id": bp["id"]},
                )
                self.results.append(r)
                self.tree.insert("", "end", iid=str(i), values=(
                    r.source_name, r.view_type, r.file_format,
                    r.year or "-", "Sí", r.description[:60],
                ))

            self.var_status.set(f"{len(self.results)} plantillas descargadas")

    # =========================================================================
    # DESCARGA Y SELECCIÓN
    # =========================================================================

    def _on_result_selected(self, event):
        """Al seleccionar un resultado en el treeview."""
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if idx < len(self.results):
                self._selected_result = self.results[idx]

    def _do_download_and_select(self):
        """Descarga el resultado seleccionado y lo devuelve al formulario."""
        if not self._selected_result:
            messagebox.showwarning("Selección",
                                   "Selecciona un resultado primero.")
            return

        result = self._selected_result

        # Si es una entrada informativa de pago, abrir URL
        if result.extra_data.get("type") == "subscription_info":
            import webbrowser
            url = result.extra_data.get("subscription_url",
                                         result.download_url)
            webbrowser.open(url)
            messagebox.showinfo(
                "Suscripción requerida",
                f"Se ha abierto el navegador en:\n{url}\n\n"
                f"Descarga las plantillas y usa 'Importar carpeta MR-Clipart' "
                f"para importarlas.")
            return

        # Si ya es local, usar directamente
        if result.extra_data.get("local"):
            file_path = result.download_url
            dims = self.dm.fetch_dimensions(
                result.make, result.model, result.year)
            self.on_select(file_path, dims)
            self.destroy()
            return

        # Descargar
        self.var_status.set("Descargando...")
        self.progress["value"] = 0

        provider = get_provider(result.source_key)
        if not provider:
            messagebox.showerror("Error", "Proveedor no encontrado.")
            return

        def _download():
            def progress_cb(pct):
                self.after(0, lambda: self.progress.configure(value=pct * 100))

            return self.dm.download_blueprint(result, provider,
                                               progress_cb=progress_cb)

        def _done(bp_data):
            self.var_status.set("Descarga completada")
            self.progress["value"] = 100

            file_path = bp_data["file_path"]
            dims = bp_data.get("dimensions")

            # Si no tenemos dimensiones del resultado, intentar obtenerlas
            if not dims:
                dims = self.dm.fetch_dimensions(
                    result.make, result.model, result.year)

            self.on_select(file_path, dims)
            self.destroy()

        self._run_in_thread(_download, _done)

    # =========================================================================
    # IMPORTAR MR-CLIPART
    # =========================================================================

    def _import_mr_clipart(self):
        """Importa una carpeta con plantillas de MR-Clipart."""
        folder = filedialog.askdirectory(
            title="Selecciona carpeta con plantillas MR-Clipart")
        if not folder:
            return

        try:
            from .providers.mr_clipart import MRClipartProvider
            mrc = MRClipartProvider()
            count = mrc.import_folder(folder)
            messagebox.showinfo(
                "Importación completada",
                f"Se importaron {count} plantillas de MR-Clipart.\n"
                f"Ahora aparecerán en las búsquedas.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al importar:\n{e}")

    # =========================================================================
    # THREADING
    # =========================================================================

    def _run_in_thread(self, task, callback):
        """Ejecuta una tarea en background y llama al callback en el hilo GUI."""
        def _worker():
            try:
                result = task()
                self.after(0, lambda: callback(result))
            except Exception as e:
                self.after(0, lambda: self.var_status.set(f"Error: {e}"))
                self.after(0, lambda: self.progress.configure(value=0))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
