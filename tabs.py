import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar, DateEntry
from datetime import datetime, timedelta

from rental_system import VehicleRentalService, Vehicle, Customer, Documentation, MaintenanceRecord

class BaseTab(ctk.CTkFrame):
    """Base class for all tab frames to inherit common properties."""
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)
        self.app_controller = app_controller 
        # Shortcut to access the system logic
        self.system = app_controller.system
        self.grid_columnconfigure(0, weight=1)

class VehiclesTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
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
        
        # OOD: Create Vehicle Object
        new_vehicle = Vehicle(model, plate, vtype, rate)

        # OOD: Pass object to System
        ok, msg = self.system.add_new_vehicle(new_vehicle)

        if ok:
            messagebox.showinfo("Added", f"Vehicle {plate} added.")
            self.entry_model.delete(0, "end")
            self.entry_plate.delete(0, "end")
            self.entry_type.delete(0, "end")
            self.entry_rate.delete(0, "end")
            self.refresh_vehicle_list()
            self.app_controller.refresh_calendar_marks()
            self.app_controller.refresh_rent_dropdowns()
            self.app_controller.update_maint_vehicle_dropdown()
        elif msg == "duplicate":
            messagebox.showerror("Error", "A vehicle with this plate already exists!")
            
    def refresh_vehicle_list(self):
        rows = self.system.get_all_vehicles()
        
        self.vehicles_box.configure(state="normal")
        self.vehicles_box.delete("1.0", "end")
        
        self.vehicles_box.insert("end", f"{'ID':<4} {'PLATE':<14} {'MODEL':<30} {'TYPE':<10} {'RATE/day':>8}\n")
        self.vehicles_box.insert("end", "-"*80 + "\n")
        
        for row in rows:
            # Using dictionary access for sqlite3.Row
            self.vehicles_box.insert("end", f"{row['VehicleID']:<4} {row['plate']:<14} {row['model']:<30} {row['vtype']:<10} {row['daily_rate']:>8.2f}\n")
            
        self.vehicles_box.configure(state="disabled")

class RentTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.build_ui()
        self.update_type_dropdown()

    def validate_number(self, P):
        """Callback to validate if input P is a number or empty string."""
        if P == "": 
            return True
        return P.isdigit()

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Create a Reservation", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,4))
    
        form = ctk.CTkFrame(tab)
        form.pack(padx=5, pady=5, fill="x") 

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)
        
        # --- Register Validation Command ---
        vcmd = (self.register(self.validate_number), '%P')
        
        col0 = ctk.CTkFrame(form)
        col0.grid(row=0, column=0, padx=3, pady=3, sticky="nsew") 
        col0.grid_columnconfigure(0, weight=0)
        col0.grid_columnconfigure(1, weight=1)

        row_index = 0
        
        ctk.CTkLabel(col0, text="Vehicle Type:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.vehicle_type_var = ctk.StringVar()
        self.vehicle_type_dropdown = ctk.CTkOptionMenu(col0, values=[], variable=self.vehicle_type_var, command=self.update_model_dropdown)
        self.vehicle_type_dropdown.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col0, text="Vehicle Model:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.vehicle_model_var = ctk.StringVar()
        self.vehicle_model_dropdown = ctk.CTkOptionMenu(col0, values=[], variable=self.vehicle_model_var, command=self.update_vehicle_dropdown)
        self.vehicle_model_dropdown.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col0, text="Select Vehicle:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.vehicle_id_var = ctk.StringVar()
        self.vehicle_dropdown = ctk.CTkOptionMenu(col0, values=[], variable=self.vehicle_id_var)
        self.vehicle_dropdown.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1
        
        col1 = ctk.CTkFrame(form)
        col1.grid(row=0, column=1, padx=3, pady=3, sticky="nsew") 
        col1.grid_columnconfigure(0, weight=0)
        col1.grid_columnconfigure(1, weight=1)

        row_index = 0

        ctk.CTkLabel(col1, text="Location:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.location_entry = ctk.CTkEntry(col1, placeholder_text="Manila, Cavite, etc.")
        self.location_entry.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col1, text="Pickup Date:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.rent_pickup_date = DateEntry(col1, date_pattern="yyyy-mm-dd")
        self.rent_pickup_date.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col1, text="Pickup Time:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.rent_pickup_time = ctk.CTkEntry(col1, placeholder_text="HH:MM (24h)")
        self.rent_pickup_time.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col1, text="Return Date:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.rent_return_date = DateEntry(col1, date_pattern="yyyy-mm-dd")
        self.rent_return_date.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col1, text="Return Time:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.rent_return_time = ctk.CTkEntry(col1, placeholder_text="HH:MM (24h)")
        self.rent_return_time.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1
        
        col2 = ctk.CTkFrame(form)
        col2.grid(row=0, column=2, padx=3, pady=3, sticky="nsew") 
        col2.grid_columnconfigure(0, weight=0)
        col2.grid_columnconfigure(1, weight=1)

        row_index = 0

        ctk.CTkLabel(col2, text="Customer Name:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.cust_name = ctk.CTkEntry(col2, placeholder_text="Full name")
        self.cust_name.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col2, text="Phone:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        # --- APPLIED VALIDATION HERE ---
        self.cust_phone = ctk.CTkEntry(col2, placeholder_text="Phone number", validate="key", validatecommand=vcmd)
        self.cust_phone.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col2, text="Email:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.cust_email = ctk.CTkEntry(col2, placeholder_text="Email")
        self.cust_email.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        self.driver_var = ctk.BooleanVar(value=False)
        self.driver_checkbox = ctk.CTkCheckBox(col2, text="Require Company Driver (adds extra 500/day)", variable=self.driver_var, command=self.toggle_driver_fields)
        ctk.CTkLabel(col2, text="Driver:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.driver_checkbox.grid(row=row_index, column=1, pady=7, padx=5, sticky="w") 
        row_index += 1
        
        self.driver_license_entry = ctk.CTkEntry(col2, placeholder_text="Driver's License (if customer will drive)")
        self.driver_license_entry.grid_info_params = {'row': row_index, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 7, 'sticky': "ew"}
        
        self.driver_license_entry.grid(**self.driver_license_entry.grid_info_params) 
        
        col2.grid_rowconfigure(row_index, weight=0) 
        row_index += 1 

        ctk.CTkButton(col2, text="Check Availability & Reserve", command=self.handle_reserve).grid(row=row_index, column=0, columnspan=2, pady=(10, 5), padx=5, sticky="s")
        col2.grid_rowconfigure(row_index, weight=1)
        
        self.toggle_driver_fields()
        
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

    def update_type_dropdown(self, *args):
        types = self.system.get_vehicle_types()
        self.vehicle_type_dropdown.configure(values=types)
        if types:
            self.vehicle_type_var.set(types[0])
            self.update_model_dropdown(types[0])
        else:
            self.vehicle_type_var.set("")
            self.update_model_dropdown("")

    def update_model_dropdown(self, selected_type):
        models = self.system.get_models_by_type(selected_type)
        self.vehicle_model_dropdown.configure(values=models)
        if models:
            self.vehicle_model_var.set(models[0])
            self.update_vehicle_dropdown(models[0])
        else:
            self.vehicle_model_var.set("")
            self.update_vehicle_dropdown("")

    def update_vehicle_dropdown(self, selected_model):
        selected_type = self.vehicle_type_var.get()
        vehicles = self.system.get_available_vehicles_list(selected_type, selected_model)
        self.vehicle_dropdown.configure(values=vehicles)
        if vehicles:
            self.vehicle_id_var.set(vehicles[0])
        else:
            self.vehicle_id_var.set("")
            
    def toggle_driver_fields(self):
        if self.driver_var.get():
            self.driver_license_entry.grid_forget()
        else:
            params = self.driver_license_entry.grid_info_params
            self.driver_license_entry.grid(row=params['row'], column=params['column'], 
                                           columnspan=params['columnspan'], padx=params['padx'], 
                                           pady=params['pady'], sticky=params['sticky'])


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
        
        # OOD: Create Customer Object
        customer = Customer(name, phone, email, driver_license)

        try:
            # OOD: Pass to system controller
            res_id, total_cost = self.system.make_reservation(
                vehicle_id, customer, start_dt.isoformat(), end_dt.isoformat(), driver_flag, location
            )
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            return

        messagebox.showinfo("Reserved", f"Reservation created (ID {res_id}). Total estimated cost: {total_cost:.2f}")

        self.app_controller.refresh_reservation_list()
        self.app_controller.refresh_calendar_marks()

class CalendarTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.build_ui()
        self.refresh_marks()

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Booking Calendar", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        cal_frame = ctk.CTkFrame(tab)
        cal_frame.pack(padx=10, pady=6, fill="both", expand=True)

        left = ctk.CTkFrame(cal_frame)
        left.pack(side="left", padx=6, pady=6, fill="y")
        self.calendar = Calendar(left, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(padx=6, pady=6)
        ctk.CTkButton(left, text="Show Bookings for Date", command=self.show_bookings_for_date).pack(pady=6)
        ctk.CTkButton(left, text="Refresh Calendar", command=self.refresh_marks).pack(pady=6)

        right = ctk.CTkFrame(cal_frame)
        right.pack(side="left", padx=6, pady=6, fill="both", expand=True)
        ctk.CTkLabel(right, text="Bookings on selected date:", anchor="w").pack(padx=6, pady=(8,4))
        self.bookings_text = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.bookings_text.pack(padx=6, pady=4, fill="both", expand=True)

    def refresh_marks(self):
        try:
            self.calendar.calevent_remove('all')
        except:
            pass
            
        rows = self.system.get_active_reservations_dates()

        for s,e,rid in rows:
            sdt = datetime.fromisoformat(s)
            edt = datetime.fromisoformat(e)
            day = sdt.date()
            while day <= edt.date():
                try:
                    self.calendar.calevent_create(day, f"Booked #{rid}", 'reserved') 
                except Exception:
                    pass
                day = day + timedelta(days=1)

    def show_bookings_for_date(self):
        sel = self.calendar.get_date()
        dt_obj = datetime.fromisoformat(sel)
        start_day = datetime(dt_obj.year, dt_obj.month, dt_obj.day)
        end_day = start_day + timedelta(days=1)
        
        rows = self.system.get_bookings_for_date(start_day.isoformat(), end_day.isoformat())

        self.bookings_text.configure(state="normal")
        self.bookings_text.delete("1.0", "end")
        if not rows:
            self.bookings_text.insert("end", "No bookings on this date.\n")
        else:
            for row in rows:
                self.bookings_text.insert("end", f"#{row['ReservationID']} Plate: {row['plate']} Model: {row['model']}\n  Customer: {row['customer_name']}\n  From {row['start_datetime']} to {row['end_datetime']}\n  Location: {row['location']}\n\n")
        self.bookings_text.configure(state="disabled")

class ReservationsTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.build_ui()
        self.refresh_list()

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Reservations", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.reservations_box = ctk.CTkTextbox(frame, height=450, font=("Courier New", 12))
        self.reservations_box.pack(fill="both", expand=True, padx=6, pady=6)
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=6)
        ctk.CTkButton(btn_frame, text="Refresh", command=self.refresh_list).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Mark Returned (select ID below then use Return tab)").pack(side="left", padx=6)

    def refresh_list(self):
        rows = self.system.get_active_reservations()
        self.reservations_box.configure(state="normal")
        self.reservations_box.delete("1.0", "end")
        self.reservations_box.insert("end", f"{'ResID':<6} {'PLATE':<10} {'MODEL':<18} {'CUSTOMER':<20} {'FROM':<19} {'TO':<19} {'STATUS':<8}\n")
        self.reservations_box.insert("end", "-"*110 + "\n")
        for row in rows:
            self.reservations_box.insert("end", f"{row['ReservationID']:<6} {row['plate']:<10} {row['model']:<18} {row['customer_name']:<20} {row['start_datetime']:<19} {row['end_datetime']:<19} {row['status']:<8}\n")
        self.reservations_box.configure(state="disabled")

class ReturnTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.build_ui()
        self.return_info.configure(state="normal")
        self.return_info.insert("end", "Enter Reservation ID and click 'Load' to begin processing return.")
        self.return_info.configure(state="disabled")

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Process Return & Damage Contract", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        frame = ctk.CTkFrame(tab)
        frame.pack(padx=10, pady=8, fill="both", expand=True)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", pady=6)
        ctk.CTkLabel(top, text="Reservation ID to return:").pack(side="left", padx=6)
        self.return_res_id = ctk.CTkEntry(top, width=100, placeholder_text="Reservation ID")
        self.return_res_id.pack(side="left", padx=6)
        ctk.CTkButton(top, text="Load", command=self.load_reservation_for_return).pack(side="left", padx=6)

        self.return_info = ctk.CTkTextbox(frame, height=140)
        self.return_info.pack(fill="x", pady=6)

        dmg_frame = ctk.CTkFrame(frame)
        dmg_frame.pack(fill="x", pady=6)
        dmg_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(dmg_frame, text="Condition of the vehicle (will be charged to customer)").grid(row=0, column=0, columnspan=2, pady=(4,6))
        ctk.CTkLabel(dmg_frame, text="Condition:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.condition = ctk.CTkEntry(dmg_frame)
        self.condition.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(dmg_frame, text="Cost:").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        self.dmg_cost = ctk.CTkEntry(dmg_frame)
        self.dmg_cost.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(dmg_frame, text="Notes:").grid(row=3, column=0, sticky="ne", padx=4, pady=4)
        self.dmg_notes = ctk.CTkTextbox(dmg_frame, height=4)
        self.dmg_notes.grid(row=3, column=1, sticky="ew", padx=4, pady=4)

        btns = ctk.CTkFrame(frame)
        btns.pack(pady=6)
        ctk.CTkButton(btns, text="Add Damage Entry", command=self.handle_add_damage).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Finalize Return (Mark returned)", command=self.handle_finalize_return).pack(side="left", padx=6)

        self.damage_list_box = ctk.CTkTextbox(frame, height=10, font=("Courier New", 12))
        self.damage_list_box.pack(fill="both", pady=6, expand=True)

    def load_reservation_for_return(self):
        rid_text = self.return_res_id.get().strip()
        if not rid_text:
            messagebox.showwarning("Missing", "Enter Reservation ID.")
            return
        try:
            rid = int(rid_text)
        except:
            messagebox.showerror("Invalid", "Reservation ID must be numeric.")
            return
            
        row = self.system.get_reservation_details(rid)

        if not row:
            messagebox.showerror("Not found", "Reservation not found.")
            return
        
        info = f"ResID: {row['ReservationID']}\nPlate: {row['plate']}\nModel: {row['model']}\nCustomer: {row['customer_name']}\nFrom: {row['start_datetime']}\nTo: {row['end_datetime']}\nDriver provided: {'Yes' if row['driver_flag'] else 'No'}\nDriver license on file: {row['driver_license']}\nEstimated Total (before damages): {row['total_cost']:.2f}\n"
        self.return_info.configure(state="normal")
        self.return_info.delete("1.0", "end")
        self.return_info.insert("end", info)
        self.return_info.configure(state="disabled")
        self.refresh_damage_list(rid)

    def refresh_damage_list(self, reservation_id):
        rows = self.system.get_damage_contracts(reservation_id)
        
        self.damage_list_box.configure(state="normal")
        self.damage_list_box.delete("1.0", "end")
        if not rows:
            self.damage_list_box.insert("end", "No damage entries yet for this reservation.\n")
        else:
            total = 0.0
            for row in rows:
                self.damage_list_box.insert("end", f"{row['created_at']} | Condition: {row['condition']} | Cost: {row['damage_cost']:.2f}\n  Notes: {row['notes']}\n\n")
                total += float(row['damage_cost'])
            self.damage_list_box.insert("end", f"\nTotal damage charges: {total:.2f}\n")
        self.damage_list_box.configure(state="disabled")

    def handle_add_damage(self):
        rid_text = self.return_res_id.get().strip()
        if not rid_text:
            messagebox.showwarning("Missing", "Enter Reservation ID first.")
            return
        try:
            rid = int(rid_text)
        except:
            messagebox.showerror("Invalid", "Reservation ID must be numeric.")
            return
        condition = self.condition.get().strip()
        cost_text = self.dmg_cost.get().strip()
        notes = self.dmg_notes.get("1.0", "end").strip()
        if not condition or not cost_text:
            messagebox.showwarning("Missing", "Enter condition and cost.")
            return
        try:
            cost = float(cost_text)
        except:
            messagebox.showerror("Invalid", "Cost must be numeric.")
            return
        
        # OOD: Create Documentation Object
        doc = Documentation(rid)
        doc.generateDocument(condition, cost, notes)
        
        messagebox.showinfo("Added", "Damage entry added.")
        self.condition.delete(0, "end")
        self.dmg_cost.delete(0, "end")
        self.dmg_notes.delete("1.0", "end")
        self.refresh_damage_list(rid)

    def handle_finalize_return(self):
        rid_text = self.return_res_id.get().strip()
        if not rid_text:
            messagebox.showwarning("Missing", "Enter Reservation ID first.")
            return
        try:
            rid = int(rid_text)
        except:
            messagebox.showerror("Invalid", "Reservation ID must be numeric.")
            return
            
        try:
            # OOD: Delegate finalized logic to system
            base, dmg_total, final = self.system.finalize_return(rid)
        except Exception:
            messagebox.showerror("Error", "Reservation not found or invalid.")
            return
        
        if messagebox.askyesno("Finalize Return", f"Base total: {base:.2f}\nDamage total: {dmg_total:.2f}\nFinal amount due from customer: {final:.2f}\n\nMark reservation as returned?"):
            messagebox.showinfo("Returned", "Reservation marked returned.")
            self.app_controller.refresh_reservation_list()
            self.app_controller.refresh_calendar_marks()
            self.app_controller.refresh_rent_dropdowns()
            
            self.return_info.configure(state="normal")
            self.return_info.delete("1.0", "end")
            self.return_info.insert("end", "Reservation finalized and marked returned.")
            self.return_info.configure(state="disabled")
            self.damage_list_box.configure(state="normal")
            self.damage_list_box.delete("1.0", "end")
            self.damage_list_box.insert("end", "No damage entries (reservation closed).")
            self.damage_list_box.configure(state="disabled")

class MaintenanceTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.check_vars = {}
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

    def update_vehicle_dropdown(self):
        vehs = self.system.get_all_vehicle_list_fmt()
        self.maint_vehicle_dropdown.configure(values=vehs)
        if vehs:
            self.maint_vehicle_var.set(vehs[0])
        else:
            self.maint_vehicle_var.set("")


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
        
        # OOD: Create Record Object
        record = MaintenanceRecord(vid, checklist_str, cost, notes)

        # OOD: Pass to System
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
        rows = self.system.get_active_maintenance()
        
        self.maint_list_box.configure(state="normal")
        self.maint_list_box.delete("1.0", "end")
        self.maint_list_box.insert("end", f"{'ID':<4} {'PLATE':<12} {'COST':<10} {'STARTED':<20} {'CHECKS'}\n")
        self.maint_list_box.insert("end", "-"*90+"\n")
        for row in rows:
            self.maint_list_box.insert("end", f"{row['MaintenanceID']:<4} {row['plate']:<12} {row['cost']:<10.2f} {row['start_date'][:16]:<20} {row['checklist']}\n")
            if row['notes']:
                self.maint_list_box.insert("end", f"    Notes: {row['notes']}\n")
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
        
        self.system.finish_maintenance(mid)
        messagebox.showinfo("Success", "Maintenance finished. Vehicle is available for rent.")
        self.finish_maint_id.delete(0, "end")
        self.refresh_maintenance_list()
        self.app_controller.refresh_rent_dropdowns()