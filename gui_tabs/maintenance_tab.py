import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import db

class MaintenanceTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.refresh_maintenance_list()
        self.refresh_vehicle_list()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Vehicle Maintenance Check", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10, 6))

        container = ctk.CTkFrame(self)
        container.pack(padx=10, pady=10, fill="both", expand=True)

        # Left side: Form to add maintenance
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
        
        # Checklist
        ctk.CTkLabel(left, text="Checklist (Check items to service):").pack(anchor="w", padx=10)
        self.check_vars = {}
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

        # Right side: Active Maintenance List
        right = ctk.CTkFrame(container)
        right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(right, text="Vehicles Currently in Maintenance", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.maint_list_box = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.maint_list_box.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctrl = ctk.CTkFrame(right)
        ctrl.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ctrl, text="Maintenance ID to Finish:").pack(side="left", padx=5)
        self.finish_maint_id = ctk.CTkEntry(ctrl, width=60)
        self.finish_maint_id.pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Finish Maintenance\n(Make Available)", command=self.handle_finish_maintenance).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Refresh List", command=self.refresh_maintenance_list).pack(side="right", padx=5)

    def refresh_vehicle_list(self):
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT VehicleID, plate, model FROM Vehicle ORDER BY plate")
        vehs = [f"{vid} - {plate} ({model})" for vid, plate, model in cur.fetchall()]
        conn.close()
        self.maint_vehicle_dropdown.configure(values=vehs)
        if vehs:
            self.maint_vehicle_var.set(vehs[0])

    def handle_start_maintenance(self):
        val = self.maint_vehicle_var.get()
        if not val:
            messagebox.showwarning("Missing", "Select a vehicle.")
            return
        try:
            vid = int(val.split(" - ")[0])
        except:
            return

        # Gather checks
        checked_items = [item for item, var in self.check_vars.items() if var.get()]
        checklist_str = ", ".join(checked_items) if checked_items else "Routine Check"

        cost_txt = self.maint_cost_entry.get().strip()
        try:
            cost = float(cost_txt) if cost_txt else 0.0
        except:
            messagebox.showerror("Invalid", "Cost must be a number.")
            return

        notes = self.maint_notes_entry.get("1.0", "end").strip()

        success, msg = db.start_maintenance(vid, checklist_str, cost, notes)
        if success:
            messagebox.showinfo("Started", "Vehicle sent to maintenance. It is now unavailable for rent.")
            self.controller.refresh_all_tabs()
            # Clear form
            self.maint_cost_entry.delete(0, "end")
            self.maint_notes_entry.delete("1.0", "end")
            for var in self.check_vars.values(): var.set(False)
        else:
            messagebox.showerror("Error", msg)

    def refresh_maintenance_list(self):
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        SELECT m.MaintenanceID, v.plate, m.cost, m.start_date, m.checklist, m.notes 
        FROM Maintenance m JOIN Vehicle v ON m.vehicle_id = v.VehicleID
        WHERE m.status='active'
        """)
        rows = cur.fetchall()
        conn.close()
        
        self.maint_list_box.configure(state="normal")
        self.maint_list_box.delete("1.0", "end")
        self.maint_list_box.insert("end", f"{'ID':<4} {'PLATE':<12} {'COST':<10} {'STARTED':<20} {'CHECKS'}\n")
        self.maint_list_box.insert("end", "-"*90+"\n")
        for mid, plate, cost, start, check, notes in rows:
            self.maint_list_box.insert("end", f"{mid:<4} {plate:<12} {cost:<10.2f} {start[:16]:<20} {check}\n")
            if notes:
                self.maint_list_box.insert("end", f"    Notes: {notes}\n")
            self.maint_list_box.insert("end", "\n")
        self.maint_list_box.configure(state="disabled")

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
        
        db.finish_maintenance(mid)
        messagebox.showinfo("Success", "Maintenance finished. Vehicle is available for rent.")
        self.finish_maint_id.delete(0, "end")
        self.controller.refresh_all_tabs()