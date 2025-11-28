import customtkinter as ctk
from tkinter import messagebox
from rental_system import MaintenanceRecord
from .base_tab import BaseTab
from datetime import datetime

class MaintenanceTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.check_vars = {}
        self.maintenance_data = []
        self.sort_column = 'MaintenanceID'
        self.sort_reverse = False
        self.build_ui()
        self.update_vehicle_dropdown()
        self.refresh_maintenance_list()

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Vehicle Maintenance Check", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10, 6))

        container = ctk.CTkFrame(tab)
        container.pack(padx=10, pady=10, fill="both", expand=True)

        left = ctk.CTkFrame(container)
        left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Start Maintenance", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        ctk.CTkLabel(left, text="Select Vehicle:").pack(anchor="w", padx=10)
        self.maint_vehicle_var = ctk.StringVar()
        self.maint_vehicle_dropdown = ctk.CTkOptionMenu(left, variable=self.maint_vehicle_var, values=[])
        self.maint_vehicle_dropdown.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(left, text="Checklist (Check items to service):").pack(anchor="w", padx=10)
        check_items = ["Oil Change", "Fuel System", "Tires", "Brakes", "Battery", "Lights", "Fluids"]
        for item in check_items:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(left, text=item, variable=var)
            chk.pack(anchor="w", padx=20, pady=2)
            self.check_vars[item] = var

        ctk.CTkLabel(left, text="Estimated Cost:").pack(anchor="w", padx=10, pady=(10,0))
        self.maint_cost_entry = ctk.CTkEntry(left, placeholder_text="0.00")
        self.maint_cost_entry.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(left, text="Notes / Details:").pack(anchor="w", padx=10)
        self.maint_notes_entry = ctk.CTkTextbox(left, height=60)
        self.maint_notes_entry.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(left, text="Send to Maintenance\n(Makes Vehicle Unavailable)", command=self.handle_start_maintenance).pack(pady=20, padx=10, fill="x")


        right = ctk.CTkFrame(container)
        right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(right, text="Vehicles Currently in Maintenance", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        self.table_container = ctk.CTkFrame(right)
        self.table_container.pack(fill="both", expand=True, padx=10, pady=5)
        self.table_container.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        headers = [
            ("ID", 'MaintenanceID'), 
            ("Plate", 'plate'), 
            ("Vehicle", 'model'),
            ("Cost", 'cost'), 
            ("Started", 'start_date')
        ]
        
        weights = [1, 2, 4, 1, 3] 

        for i, (text, key) in enumerate(headers):
            btn = ctk.CTkButton(header_frame, text=text, fg_color="gray", hover_color="#555555",
                                command=lambda k=key: self.sort_and_display(k))
            btn.grid(row=0, column=i, sticky="ew", padx=(2 if i > 0 else 0, 2), pady=2)
            header_frame.grid_columnconfigure(i, weight=weights[i])

        self.scrollable_data_frame = ctk.CTkScrollableFrame(self.table_container, label_text="Active Maintenance List")
        self.scrollable_data_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.table_container.grid_rowconfigure(1, weight=1)

        for i, w in enumerate(weights):
            self.scrollable_data_frame.grid_columnconfigure(i, weight=w)
        self.scrollable_data_frame.grid_columnconfigure(len(weights), weight=0) 
        
        ctrl = ctk.CTkFrame(right)
        ctrl.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ctrl, text="Maintenance ID to Finish:").pack(side="left", padx=5)
        self.finish_maint_id = ctk.CTkEntry(ctrl, width=60)
        self.finish_maint_id.pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Finish Maintenance\n(Make Available)", command=self.handle_finish_maintenance).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Refresh List", command=self.refresh_maintenance_list).pack(side="right", padx=5)

    def update_vehicle_dropdown(self):
        vehs = self.system.get_all_vehicle_list_fmt()
        self.maint_vehicle_dropdown.configure(values=vehs)
        if vehs:
            self.maint_vehicle_var.set(vehs[0])
        else:
            self.maint_vehicle_var.set("")

    def sort_and_display(self, column_key):
        
        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False

        if self.maintenance_data:
            if column_key == 'cost':
                key_func = lambda x: float(x.get(column_key, 0))
            elif column_key in ('MaintenanceID', 'year'):
                 key_func = lambda x: int(x.get(column_key, 0))
            elif column_key == 'start_date':
                try:
                    key_func = lambda x: datetime.fromisoformat(x.get(column_key, '1970-01-01T00:00:00'))
                except:
                    key_func = lambda x: x.get(column_key, '')
            else:
                key_func = lambda x: (x.get('model', ''), x.get('brand', ''))
                
            self.maintenance_data.sort(key=key_func, reverse=self.sort_reverse)

        self._display_maintenance_list()

    def _display_maintenance_list(self):
        for widget in self.scrollable_data_frame.winfo_children():
            widget.destroy()

        if not self.maintenance_data:
            ctk.CTkLabel(self.scrollable_data_frame, text="No vehicles currently in maintenance.").grid(row=0, column=0, columnspan=6, pady=10)
            return

        for i, row in enumerate(self.maintenance_data):
            bg_color = ("#333333" if i % 2 == 0 else "#444444") if ctk.get_appearance_mode() == "Dark" else ("#DDDDDD" if i % 2 == 0 else "#EEEEEE")
            
            full_vehicle_name = f"{row['brand']} {row['model']}"
            
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['MaintenanceID']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=0, sticky="ew", padx=(2, 0), pady=1)

            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['plate']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=1, sticky="ew", padx=2, pady=1)

            ctk.CTkLabel(self.scrollable_data_frame, text=full_vehicle_name, 
                         anchor="w", fg_color=bg_color).grid(row=i, column=2, sticky="ew", padx=2, pady=1)

            ctk.CTkLabel(self.scrollable_data_frame, text=f"₱{row['cost']:.2f}", 
                         anchor="e", fg_color=bg_color).grid(row=i, column=3, sticky="ew", padx=2, pady=1)

            start_date_fmt = row['start_date'][:16].replace("T", " ")
            ctk.CTkLabel(self.scrollable_data_frame, text=start_date_fmt, 
                         anchor="w", fg_color=bg_color).grid(row=i, column=4, sticky="ew", padx=2, pady=1)

            btn = ctk.CTkButton(self.scrollable_data_frame, text="Details", width=60, height=20,
                                command=lambda r=row: self.show_maintenance_details(r))
            btn.grid(row=i, column=5, sticky="e", padx=(2, 4), pady=1)
            
    def show_maintenance_details(self, row):
        """Displays a detailed view of the maintenance record."""
        details = (
            f"Maintenance ID: {row['MaintenanceID']}\n"
            f"Vehicle: {row['brand']} {row['model']} ({row['plate']})\n"
            f"Start Date: {row['start_date'][:16].replace('T', ' ')}\n"
            f"Cost: ₱{row['cost']:.2f}\n"
            f"-----------------------------------------\n"
            f"Checklist: {row['checklist']}\n"
            f"Notes:\n{row['notes']}"
        )
        messagebox.showinfo(f"Maintenance Details #{row['MaintenanceID']}", details)

    def handle_start_maintenance(self):
        val = self.maint_vehicle_var.get()
        if not val:
            messagebox.showwarning("Missing", "Select a vehicle.")
            return
        try:
            vid = int(val.split(" - ")[0])
        except:
            return

        checked_items = [item for item, var in self.check_vars.items() if var.get()]
        checklist_str = ", ".join(checked_items) if checked_items else "Routine Check"

        cost_txt = self.maint_cost_entry.get().strip()
        try:
            cost = float(cost_txt) if cost_txt else 0.0
        except:
            messagebox.showerror("Invalid", "Cost must be a number.")
            return

        notes = self.maint_notes_entry.get("1.0", "end").strip()
        
        record = MaintenanceRecord(vid, checklist_str, cost, notes)

        success, msg = self.system.start_maintenance(record)
        if success:
            messagebox.showinfo("Started", "Vehicle sent to maintenance.")
            self.refresh_maintenance_list()
            self.app_controller.refresh_rent_dropdowns() 
            self.maint_cost_entry.delete(0, "end")
            self.maint_notes_entry.delete("1.0", "end")
            for var in self.check_vars.values(): var.set(False)
        else:
            messagebox.showerror("Error", msg)

    def refresh_maintenance_list(self):
        self.maintenance_data = self.system.get_active_maintenance()
        self.sort_and_display(self.sort_column)

    def handle_finish_maintenance(self):
        mid_txt = self.finish_maint_id.get().strip()
        if not mid_txt:
            messagebox.showwarning("Missing", "Enter Maintenance ID.")
            return
        try:
            mid = int(mid_txt)
        except:
            messagebox.showerror("Invalid", "ID must be a number.")
            return
        
        self.system.finish_maintenance(mid)
        messagebox.showinfo("Success", "Maintenance finished. Vehicle is available for rent.")
        self.finish_maint_id.delete(0, "end")
        self.refresh_maintenance_list()
        self.app_controller.refresh_rent_dropdowns()