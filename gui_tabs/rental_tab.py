import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import sqlite3
import db

class RentTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.refresh()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Create a Reservation", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,6))
    
        form = ctk.CTkFrame(self)
        form.pack(padx=15, pady=8, fill="both", expand=True)
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        # Left frame: select vehicle and dates
        left = ctk.CTkFrame(form)
        left.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Select Vehicle Type").pack(pady=(6,4))
        self.vehicle_type_var = ctk.StringVar()
        self.vehicle_type_dropdown = ctk.CTkOptionMenu(left, values=[], variable=self.vehicle_type_var, command=self.update_model_dropdown)
        self.vehicle_type_dropdown.pack(padx=6, pady=4, fill="x")

        ctk.CTkLabel(left, text="Select Vehicle Model").pack(pady=(6,4))
        self.vehicle_model_var = ctk.StringVar()
        self.vehicle_model_dropdown = ctk.CTkOptionMenu(left, values=[], variable=self.vehicle_model_var, command=self.update_vehicle_dropdown)
        self.vehicle_model_dropdown.pack(padx=6, pady=4, fill="x")

        ctk.CTkLabel(left, text="Select Vehicle").pack(pady=(6,4))
        self.vehicle_id_var = ctk.StringVar()
        self.vehicle_dropdown = ctk.CTkOptionMenu(left, values=[], variable=self.vehicle_id_var)
        self.vehicle_dropdown.pack(padx=6, pady=4, fill="x")
        
        ctk.CTkLabel(left, text="Location (Where will the vehicle be used)").pack(pady=(6,2))
        self.location_entry = ctk.CTkEntry(left, placeholder_text="Example: Manila, Cavite, etc.")
        self.location_entry.pack(padx=6, pady=2, fill="x")

        ctk.CTkLabel(left, text="Pickup Date & Time").pack(pady=(6,2))
        self.rent_pickup_date = DateEntry(left, date_pattern="yyyy-mm-dd")
        self.rent_pickup_time = ctk.CTkEntry(left, placeholder_text="HH:MM (24h)")
        self.rent_pickup_date.pack(padx=6, pady=2, fill="x")
        self.rent_pickup_time.pack(padx=6, pady=2, fill="x")

        ctk.CTkLabel(left, text="Return Date & Time").pack(pady=(6,2))
        self.rent_return_date = DateEntry(left, date_pattern="yyyy-mm-dd")
        self.rent_return_time = ctk.CTkEntry(left, placeholder_text="HH:MM (24h)")
        self.rent_return_date.pack(padx=6, pady=2, fill="x")
        self.rent_return_time.pack(padx=6, pady=2, fill="x")
        
        # Right frame: customer details & driver option
        right = ctk.CTkFrame(form)
        right.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Customer Details").pack(pady=(6,4))
        self.cust_name = ctk.CTkEntry(right, placeholder_text="Full name")
        self.cust_phone = ctk.CTkEntry(right, placeholder_text="Phone number")
        self.cust_email = ctk.CTkEntry(right, placeholder_text="Email")
        self.cust_name.pack(padx=6, pady=4, fill="x")
        self.cust_phone.pack(padx=6, pady=4, fill="x")
        self.cust_email.pack(padx=6, pady=4, fill="x")

        self.driver_var = ctk.BooleanVar(value=False)
        self.driver_checkbox = ctk.CTkCheckBox(right, text="Require Company Driver (adds extra 500/day)", variable=self.driver_var, command=self.toggle_driver_fields)
        self.driver_checkbox.pack(pady=6)
        self.driver_license_entry = ctk.CTkEntry(right, placeholder_text="Driver's License (if customer will drive)")
        self.driver_license_entry.pack_forget()

        ctk.CTkButton(right, text="Check Availability & Reserve", command=self.handle_reserve).pack(pady=12)

    def refresh(self):
        self.update_type_dropdown()

    def update_type_dropdown(self):
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT vtype FROM Vehicle ORDER BY vtype")
        types = [row[0] for row in cur.fetchall()]
        conn.close()
        self.vehicle_type_dropdown.configure(values=types)
        if types:
            self.vehicle_type_var.set(types[0])
            self.update_model_dropdown(types[0])

    def update_model_dropdown(self, selected_type):
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT model FROM Vehicle WHERE vtype=? ORDER BY model", (selected_type,))
        models = [row[0] for row in cur.fetchall()]
        conn.close()
        self.vehicle_model_dropdown.configure(values=models)
        if models:
            self.vehicle_model_var.set(models[0])
            self.update_vehicle_dropdown(models[0])

    def update_vehicle_dropdown(self, selected_model):
        selected_type = self.vehicle_type_var.get()
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT VehicleID, plate FROM Vehicle WHERE vtype=? AND model=? AND available=1 ORDER BY plate", (selected_type, selected_model))
        vehicles = [f"{vid} - {plate}" for vid, plate in cur.fetchall()]
        conn.close()
        self.vehicle_dropdown.configure(values=vehicles)
        if vehicles:
            self.vehicle_id_var.set(vehicles[0])
            
    def toggle_driver_fields(self):
        if self.driver_var.get():
            self.driver_license_entry.pack_forget()
        else:
            self.driver_license_entry.pack(padx=6, pady=4, fill="x")

    def parse_datetime_inputs(self, date_widget, time_entry):
        date_str = date_widget.get_date().isoformat()
        time_str = time_entry.get().strip()
        if not time_str:
            time_str = "09:00"
        try:
            hh, mm = map(int, time_str.split(":"))
            dt = datetime.fromisoformat(date_str) + timedelta(hours=hh, minutes=mm)
            return dt
        except Exception as e:
            raise ValueError("Invalid time format. Use HH:MM (24h).")

    def handle_reserve(self):
        vehicle_text = self.vehicle_id_var.get().strip()
        if not vehicle_text:
            messagebox.showwarning("Missing", "Please select a vehicle.")
            return

        try:
            vehicle_id = int(vehicle_text.split(" - ")[0])
        except:
            messagebox.showerror("Invalid", "Selected vehicle is invalid.")
            return

        try:
            start_dt = self.parse_datetime_inputs(self.rent_pickup_date, self.rent_pickup_time)
            end_dt = self.parse_datetime_inputs(self.rent_return_date, self.rent_return_time)
        except Exception as e:
            messagebox.showerror("Invalid datetime", str(e))
            return

        if end_dt <= start_dt:
            messagebox.showerror("Invalid", "Return must be after pickup.")
            return

        name = self.cust_name.get().strip()
        phone = self.cust_phone.get().strip()
        email = self.cust_email.get().strip()
        location = self.location_entry.get().strip()
        
        if not (name and phone and email):
            messagebox.showwarning("Missing", "Please fill all customer details.")
            return
        
        if not location:
            messagebox.showwarning("Missing", "Please enter the location where the vehicle will be used.")
            return

        driver_flag = self.driver_var.get()
        driver_license = ""
        if not driver_flag:
            driver_license = self.driver_license_entry.get().strip()
            if not driver_license:
                messagebox.showwarning("Missing", "Customer driving the car: collect driver's license.")
                return

        # Check availability (INCLUDES MAINTENANCE CHECK)
        if not db.is_vehicle_available(vehicle_id, start_dt.isoformat(), end_dt.isoformat()):
            messagebox.showinfo("Unavailable", "That vehicle is unavailable (Already booked or in Maintenance).")
            return

        try:
            res_id, total_cost = db.create_reservation(
                vehicle_id, name, phone, email, driver_flag, driver_license,
                start_dt.isoformat(), end_dt.isoformat(), location
            )
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            return

        messagebox.showinfo("Reserved", f"Reservation created (ID {res_id}). Total estimated cost: {total_cost:.2f}")
        self.controller.refresh_all_tabs()