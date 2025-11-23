import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import db

class VehicleTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.refresh_vehicle_list()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Vehicles", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,6))

        frame = ctk.CTkFrame(self)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.vehicles_box = ctk.CTkTextbox(frame, width=500, font=("Courier New", 12))
        self.vehicles_box.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")

        right = ctk.CTkFrame(frame)
        right.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(right, text="Add / Register Vehicle").pack(pady=(6,4))
        self.entry_model = ctk.CTkEntry(right, placeholder_text="Model (e.g. Toyota Vios)")
        self.entry_plate = ctk.CTkEntry(right, placeholder_text="Plate (unique)")
        self.entry_type = ctk.CTkEntry(right, placeholder_text="Type (Sedan/SUV/Van/..)")
        self.entry_rate = ctk.CTkEntry(right, placeholder_text="Daily Rate (number)")
        
        self.entry_model.pack(padx=10, pady=4, fill="x")
        self.entry_plate.pack(padx=10, pady=4, fill="x")
        self.entry_type.pack(padx=10, pady=4, fill="x")
        self.entry_rate.pack(padx=10, pady=4, fill="x")
        
        ctk.CTkButton(right, text="Add Vehicle", command=self.handle_add_vehicle).pack(pady=10)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)

    def handle_add_vehicle(self):
        model = self.entry_model.get().strip()
        plate = self.entry_plate.get().strip()
        vtype = self.entry_type.get().strip()
        rate_text = self.entry_rate.get().strip()
        if not (model and plate and vtype and rate_text):
            messagebox.showwarning("Missing", "Please fill all fields.")
            return
        try:
            rate = float(rate_text)
        except:
            messagebox.showerror("Invalid", "Daily rate must be a number.")
            return
        
        ok, msg = db.add_vehicle(model, plate, vtype, rate)

        if msg == "success":
            messagebox.showinfo("Added", f"Vehicle {plate} added.")
            self.entry_model.delete(0, "end")
            self.entry_plate.delete(0, "end")
            self.entry_type.delete(0, "end")
            self.entry_rate.delete(0, "end")
            # Notify Controller to refresh other tabs
            self.controller.refresh_all_tabs()
        elif msg == "duplicate":
            messagebox.showerror("Error", "A vehicle with this plate already exists!")

    def refresh_vehicle_list(self):
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT VehicleID, model, plate, vtype, daily_rate FROM Vehicle ORDER BY VehicleID")
        rows = cur.fetchall()
        conn.close()
        self.vehicles_box.configure(state="normal")
        self.vehicles_box.delete("1.0", "end")
        
        self.vehicles_box.insert("end", f"{'ID':<4} {'PLATE':<14} {'MODEL':<30} {'TYPE':<10} {'RATE/day':>8}\n")
        self.vehicles_box.insert("end", "-"*80 + "\n")
        
        for vid, model, plate, vtype, rate in rows:
            self.vehicles_box.insert("end", f"{vid:<4} {plate:<14} {model:<30} {vtype:<10} {rate:>8.2f}\n")
            
        self.vehicles_box.configure(state="disabled")