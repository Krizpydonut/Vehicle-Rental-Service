import sqlite3
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar, DateEntry

DB_FILE = "rental.db"
DRIVER_FEE_PER_DAY = 500.0 
BASE_DAILY_RATE = 1500.0 


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Vehicle (
        VehicleID INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        plate TEXT UNIQUE,
        vtype TEXT,
        daily_rate REAL,
        available INTEGER DEFAULT 1
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Reservation (
        ReservationID INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        customer_name TEXT,
        customer_phone TEXT,
        customer_email TEXT,
        driver_flag INTEGER,
        driver_license TEXT,
        start_datetime TEXT,
        end_datetime TEXT,
        location TEXT,
        driver_fee REAL,
        total_cost REAL,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(vehicle_id) REFERENCES Vehicle(VehicleID)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS DamageContract (
        ContractID INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        condition TEXT,
        damage_cost REAL,
        notes TEXT,
        created_at TEXT,
        FOREIGN KEY(reservation_id) REFERENCES Reservation(ReservationID)
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Maintenance (
        MaintenanceID INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        checklist TEXT,
        cost REAL,
        notes TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(vehicle_id) REFERENCES Vehicle(VehicleID)
    )
    """)
    conn.close()

def fix_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        # Try to add the missing column
        cur.execute("ALTER TABLE Maintenance ADD COLUMN checklist TEXT")
        conn.commit()
        print("Fixed: Added 'checklist' column.")
    except sqlite3.OperationalError as e:
        # This error means the column likely already exists or the table is missing
        print(f"Database message: {e}")
    conn.close()

def add_vehicle(model, plate, vtype, daily_rate):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Vehicle (model, plate, vtype, daily_rate) VALUES (?, ?, ?, ?)",
            (model, plate, vtype, daily_rate)
        )
        conn.commit()
        conn.close()
        return True, "success"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "duplicate"

def is_vehicle_available(vehicle_id, requested_start, requested_end):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # 1. Check Maintenance Status
    # If a vehicle is in active maintenance, it is unavailable regardless of dates.
    cur.execute("SELECT count(*) FROM Maintenance WHERE vehicle_id=? AND status='active'", (vehicle_id,))
    in_maintenance = cur.fetchone()[0]
    if in_maintenance > 0:
        conn.close()
        return False

    # 2. Check Reservation Overlaps
    cur.execute("""
    SELECT start_datetime, end_datetime FROM Reservation
    WHERE vehicle_id=? AND status='active'
    """, (vehicle_id,))
    rows = cur.fetchall()
    conn.close()
    
    rs = datetime.fromisoformat(requested_start)
    re = datetime.fromisoformat(requested_end)
    
    for s,e in rows:
        sdt = datetime.fromisoformat(s)
        edt = datetime.fromisoformat(e)
        # Overlap logic
        if (rs < edt) and (re > sdt):
            return False
    return True

def start_maintenance(vehicle_id, checklist_str, cost, notes):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Check if already in maintenance
    cur.execute("SELECT count(*) FROM Maintenance WHERE vehicle_id=? AND status='active'", (vehicle_id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return False, "Vehicle is already in maintenance."
    
    cur.execute("""
    INSERT INTO Maintenance (vehicle_id, checklist, cost, notes, start_date, status)
    VALUES (?, ?, ?, ?, ?, 'active')
    """, (vehicle_id, checklist_str, cost, notes, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True, "Maintenance started."

def finish_maintenance(maintenance_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    UPDATE Maintenance 
    SET status='completed', end_date=? 
    WHERE MaintenanceID=?
    """, (datetime.now().isoformat(), maintenance_id))
    conn.commit()
    conn.close()

def create_reservation(vehicle_id, customer_name, phone, email, driver_flag,
                       driver_license, start_dt_iso, end_dt_iso, location):
    s = datetime.fromisoformat(start_dt_iso)
    e = datetime.fromisoformat(end_dt_iso)
    duration_days = max(1, (e - s).days + (1 if (e - s).seconds>0 else 0))
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT daily_rate FROM Vehicle WHERE VehicleID=?", (vehicle_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Vehicle not found")
    daily_rate = row[0]
    driver_fee = DRIVER_FEE_PER_DAY * duration_days if driver_flag else 0.0
    total_cost = (daily_rate * duration_days) + driver_fee
    cur.execute("""
    INSERT INTO Reservation (vehicle_id, customer_name, customer_phone, customer_email,
      driver_flag, driver_license, start_datetime, end_datetime, driver_fee, total_cost, location)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (vehicle_id, customer_name, phone, email, int(driver_flag), driver_license,
          start_dt_iso, end_dt_iso, driver_fee, total_cost, location))
    conn.commit()
    res_id = cur.lastrowid
    conn.close()
    return res_id, total_cost

def list_active_reservations():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.status
    FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    ORDER BY r.start_datetime
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def add_damage(reservation_id, condition, cost, notes=""):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO DamageContract (reservation_id, condition, damage_cost, notes, created_at)
    VALUES (?,?,?,?,?)
    """, (reservation_id, condition, cost, notes, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def finalize_reservation(reservation_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE Reservation SET status='returned' WHERE ReservationID=?", (reservation_id,))
    conn.commit()
    conn.close()
    
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login - Vehicle Rental Service")
        self.geometry("400x250")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="Please login", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10, padx=40, fill="x")
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10, padx=40, fill="x")

        ctk.CTkButton(self, text="Login", command=self.handle_login).pack(pady=20)

        self.correct_username = "admin"
        self.correct_password = "admin123"

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing", "Enter both username and password.")
            return
        if username == self.correct_username and password == self.correct_password:
            self.destroy()
            app = RentalApp()
            app.mainloop()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.")


#UI
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class RentalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vehicle Rental Service")
        self.geometry("1050x850") # Increased slightly for new tab

        #tabs
        self.tabview = ctk.CTkTabview(self, width=980, height=660)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tabview.add("Vehicles")
        self.tabview.add("Rent Vehicle")
        self.tabview.add("Calendar")
        self.tabview.add("Active Reservations")
        self.tabview.add("Return / Damage")
        self.tabview.add("Maintenance") # NEW TAB

        self.build_vehicles_tab()
        self.build_rent_tab()
        self.build_calendar_tab()
        self.build_reservations_tab()
        self.build_return_tab()
        self.build_maintenance_tab()

        self.refresh_vehicle_list()
        self.refresh_reservation_list()
        self.refresh_calendar_marks()
        self.refresh_maintenance_list() # Refresh new list

    #Vehicles tab
    def build_vehicles_tab(self):
        tab = self.tabview.tab("Vehicles")
        header = ctk.CTkLabel(tab, text="Vehicles", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,6))

        frame = ctk.CTkFrame(tab)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        #list of cars
        self.vehicles_box = ctk.CTkTextbox(frame, width=500, font=("Courier New", 12))
        self.vehicles_box.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")

        #add vehicle
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
        ok, msg = add_vehicle(model, plate, vtype, rate)

        if msg == "success":
            messagebox.showinfo("Added", f"Vehicle {plate} added.")
            self.entry_model.delete(0, "end")
            self.entry_plate.delete(0, "end")
            self.entry_type.delete(0, "end")
            self.entry_rate.delete(0, "end")
            self.refresh_vehicle_list()
            self.refresh_calendar_marks()
            self.update_maint_vehicle_dropdown() # Refresh dropdown in Maint tab

        elif msg == "duplicate":
            messagebox.showerror("Error", "A vehicle with this plate already exists!")
            
    def refresh_vehicle_list(self):
        conn = sqlite3.connect(DB_FILE)
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
        
    #Rent tab
    def build_rent_tab(self):
        tab = self.tabview.tab("Rent Vehicle")
        header = ctk.CTkLabel(tab, text="Create a Reservation", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,6))
    
        form = ctk.CTkFrame(tab)
        form.pack(padx=15, pady=8, fill="both", expand=True)

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

    # Populate type dropdown
        self.update_type_dropdown()

# Functions for dropdown updates
    def update_type_dropdown(self):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT vtype FROM Vehicle ORDER BY vtype")
        types = [row[0] for row in cur.fetchall()]
        conn.close()
        self.vehicle_type_dropdown.configure(values=types)
        if types:
            self.vehicle_type_var.set(types[0])
            self.update_model_dropdown(types[0])

    def update_model_dropdown(self, selected_type):
        conn = sqlite3.connect(DB_FILE)
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
        conn = sqlite3.connect(DB_FILE)
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
    # Get selected vehicle ID
        vehicle_text = self.vehicle_id_var.get().strip()
        if not vehicle_text:
            messagebox.showwarning("Missing", "Please select a vehicle.")
            return

        try:
            vehicle_id = int(vehicle_text.split(" - ")[0])
        except:
            messagebox.showerror("Invalid", "Selected vehicle is invalid.")
            return

    # Parse pickup and return datetimes
        try:
            start_dt = self.parse_datetime_inputs(self.rent_pickup_date, self.rent_pickup_time)
            end_dt = self.parse_datetime_inputs(self.rent_return_date, self.rent_return_time)
        except Exception as e:
            messagebox.showerror("Invalid datetime", str(e))
            return

        if end_dt <= start_dt:
            messagebox.showerror("Invalid", "Return must be after pickup.")
            return

    # Customer details
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

    # Driver option
        driver_flag = self.driver_var.get()
        driver_license = ""
        if not driver_flag:
            driver_license = self.driver_license_entry.get().strip()
            if not driver_license:
                messagebox.showwarning("Missing", "Customer driving the car: collect driver's license.")
                return

    # Check availability (INCLUDES MAINTENANCE CHECK NOW)
        if not is_vehicle_available(vehicle_id, start_dt.isoformat(), end_dt.isoformat()):
            messagebox.showinfo("Unavailable", "That vehicle is unavailable (Already booked or in Maintenance).")
            return

    # Create reservation
        try:
            res_id, total_cost = create_reservation(
                vehicle_id, name, phone, email, driver_flag, driver_license,
                start_dt.isoformat(), end_dt.isoformat(), location
            )
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            return

        messagebox.showinfo("Reserved", f"Reservation created (ID {res_id}). Total estimated cost: {total_cost:.2f}")

    # Refresh UI
        self.refresh_reservation_list()
        self.refresh_calendar_marks()


    #Calendar tab 
    def build_calendar_tab(self):
        tab = self.tabview.tab("Calendar")
        header = ctk.CTkLabel(tab, text="Booking Calendar", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        cal_frame = ctk.CTkFrame(tab)
        cal_frame.pack(padx=10, pady=6, fill="both", expand=True)

        left = ctk.CTkFrame(cal_frame)
        left.pack(side="left", padx=6, pady=6, fill="y")
        self.calendar = Calendar(left, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(padx=6, pady=6)
        ctk.CTkButton(left, text="Show Bookings for Date", command=self.show_bookings_for_date).pack(pady=6)
        ctk.CTkButton(left, text="Refresh Calendar", command=self.refresh_calendar_marks).pack(pady=6)

        right = ctk.CTkFrame(cal_frame)
        right.pack(side="left", padx=6, pady=6, fill="both", expand=True)
        ctk.CTkLabel(right, text="Bookings on selected date:", anchor="w").pack(padx=6, pady=(8,4))
        self.bookings_text = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.bookings_text.pack(padx=6, pady=4, fill="both", expand=True)

    def refresh_calendar_marks(self):
        try:
            self.calendar.calevent_remove('all')
        except:
            pass
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT start_datetime, end_datetime, ReservationID FROM Reservation WHERE status='active'")
        rows = cur.fetchall()
        conn.close()
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
        sel = self.calendar.get_date()  # yyyy-mm-dd
        dt_obj = datetime.fromisoformat(sel)
        start_day = datetime(dt_obj.year, dt_obj.month, dt_obj.day)
        end_day = start_day + timedelta(days=1)
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.location
        FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
        WHERE r.status='active' AND
             NOT (r.end_datetime <= ? OR r.start_datetime >= ?)
        ORDER BY r.start_datetime
        """, (start_day.isoformat(), end_day.isoformat()))
        rows = cur.fetchall()
        conn.close()
        self.bookings_text.configure(state="normal")
        self.bookings_text.delete("1.0", "end")
        if not rows:
            self.bookings_text.insert("end", "No bookings on this date.\n")
        else:
            for rid, plate, model, name, s,e ,location in rows:
                self.bookings_text.insert("end", f"#{rid} Plate: {plate} Model: {model}\n  Customer: {name}\n  From {s} to {e}\n  Location: {location}\n\n")
        self.bookings_text.configure(state="disabled")

    #Reservations tab
    def build_reservations_tab(self):
        tab = self.tabview.tab("Active Reservations")
        header = ctk.CTkLabel(tab, text="Reservations", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.reservations_box = ctk.CTkTextbox(frame, height=450, font=("Courier New", 12))
        self.reservations_box.pack(fill="both", expand=True, padx=6, pady=6)
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=6)
        ctk.CTkButton(btn_frame, text="Refresh", command=self.refresh_reservation_list).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Mark Returned (select ID below then use Return tab)", command=self.refresh_reservation_list).pack(side="left", padx=6)

    def refresh_reservation_list(self):
        rows = list_active_reservations()
        self.reservations_box.configure(state="normal")
        self.reservations_box.delete("1.0", "end")
        self.reservations_box.insert("end", f"{'ResID':<6} {'PLATE':<10} {'MODEL':<18} {'CUSTOMER':<20} {'FROM':<19} {'TO':<19} {'STATUS':<8}\n")
        self.reservations_box.insert("end", "-"*110 + "\n")
        for rid, plate, model, cname, s,e,status in rows:
            self.reservations_box.insert("end", f"{rid:<6} {plate:<10} {model:<18} {cname:<20} {s:<19} {e:<19} {status:<8}\n")
        self.reservations_box.configure(state="disabled")

    #Return / Damage tab
    def build_return_tab(self):
        tab = self.tabview.tab("Return / Damage")
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

        #Damage form
        dmg_frame = ctk.CTkFrame(frame)
        dmg_frame.pack(fill="x", pady=6)
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
        dmg_frame.grid_columnconfigure(1, weight=1)

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
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.driver_flag, r.driver_license, r.total_cost
        FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
        WHERE r.ReservationID=?
        """, (rid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            messagebox.showerror("Not found", "Reservation not found.")
            return
        rid, plate, model, name, s,e, driver_flag, driver_license, total_cost = row
        info = f"ResID: {rid}\nPlate: {plate}\nModel: {model}\nCustomer: {name}\nFrom: {s}\nTo: {e}\nDriver provided: {'Yes' if driver_flag else 'No'}\nDriver license on file: {driver_license}\nEstimated Total (before damages): {total_cost:.2f}\n"
        self.return_info.configure(state="normal")
        self.return_info.delete("1.0", "end")
        self.return_info.insert("end", info)
        self.return_info.configure(state="disabled")
        self.refresh_damage_list(rid)

    def refresh_damage_list(self, reservation_id):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT condition, damage_cost, notes, created_at FROM DamageContract WHERE reservation_id=?", (reservation_id,))
        rows = cur.fetchall()
        conn.close()
        self.damage_list_box.configure(state="normal")
        self.damage_list_box.delete("1.0", "end")
        if not rows:
            self.damage_list_box.insert("end", "No damage entries yet for this reservation.\n")
        else:
            total = 0.0
            for condition, cost, notes, created_at in rows:
                self.damage_list_box.insert("end", f"{created_at} | Condition: {condition} | Cost: {cost:.2f}\n  Notes: {notes}\n\n")
                total += float(cost)
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
        add_damage(rid, condition, cost, notes)
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
        # show damage total
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT SUM(damage_cost) FROM DamageContract WHERE reservation_id=?", (rid,))
        dmg_total = cur.fetchone()[0] or 0.0
        cur.execute("SELECT total_cost FROM Reservation WHERE ReservationID=?", (rid,))
        base = cur.fetchone()[0] or 0.0
        final = base + dmg_total
        conn.close()
        if messagebox.askyesno("Finalize Return", f"Base total: {base:.2f}\nDamage total: {dmg_total:.2f}\nFinal amount due from customer: {final:.2f}\n\nMark reservation as returned?"):
            finalize_reservation(rid)
            messagebox.showinfo("Returned", "Reservation marked returned.")
            self.refresh_reservation_list()
            self.refresh_calendar_marks()
            self.return_info.configure(state="normal")
            self.return_info.delete("1.0", "end")
            self.return_info.insert("end", "Reservation finalized and marked returned.")
            self.return_info.configure(state="disabled")
            self.damage_list_box.configure(state="normal")
            self.damage_list_box.delete("1.0", "end")
            self.damage_list_box.insert("end", "No damage entries (reservation closed).")
            self.damage_list_box.configure(state="disabled")

    # ===========================
    # NEW MAINTENANCE TAB METHODS
    # ===========================
    def build_maintenance_tab(self):
        tab = self.tabview.tab("Maintenance")
        header = ctk.CTkLabel(tab, text="Vehicle Maintenance Check", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10, 6))

        # Container
        container = ctk.CTkFrame(tab)
        container.pack(padx=10, pady=10, fill="both", expand=True)

        # Left side: Form to add maintenance
        left = ctk.CTkFrame(container)
        left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Start Maintenance", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        # Vehicle Selection
        ctk.CTkLabel(left, text="Select Vehicle:").pack(anchor="w", padx=10)
        self.maint_vehicle_var = ctk.StringVar()
        self.maint_vehicle_dropdown = ctk.CTkOptionMenu(left, variable=self.maint_vehicle_var, values=[])
        self.maint_vehicle_dropdown.pack(fill="x", padx=10, pady=(0, 10))
        self.update_maint_vehicle_dropdown()

        # Checklist
        ctk.CTkLabel(left, text="Checklist (Check items to service):").pack(anchor="w", padx=10)
        self.check_vars = {}
        check_items = ["Oil Change", "Fuel System", "Tires", "Brakes", "Battery", "Lights", "Fluids"]
        for item in check_items:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(left, text=item, variable=var)
            chk.pack(anchor="w", padx=20, pady=2)
            self.check_vars[item] = var

        # Cost
        ctk.CTkLabel(left, text="Estimated Cost:").pack(anchor="w", padx=10, pady=(10,0))
        self.maint_cost_entry = ctk.CTkEntry(left, placeholder_text="0.00")
        self.maint_cost_entry.pack(fill="x", padx=10, pady=5)

        # Notes
        ctk.CTkLabel(left, text="Notes / Details:").pack(anchor="w", padx=10)
        self.maint_notes_entry = ctk.CTkTextbox(left, height=60)
        self.maint_notes_entry.pack(fill="x", padx=10, pady=5)

        # Button
        ctk.CTkButton(left, text="Send to Maintenance\n(Makes Vehicle Unavailable)", command=self.handle_start_maintenance).pack(pady=20, padx=10, fill="x")


        # Right side: Active Maintenance List
        right = ctk.CTkFrame(container)
        right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(right, text="Vehicles Currently in Maintenance", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.maint_list_box = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.maint_list_box.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Controls for finishing maintenance
        ctrl = ctk.CTkFrame(right)
        ctrl.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ctrl, text="Maintenance ID to Finish:").pack(side="left", padx=5)
        self.finish_maint_id = ctk.CTkEntry(ctrl, width=60)
        self.finish_maint_id.pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Finish Maintenance\n(Make Available)", command=self.handle_finish_maintenance).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Refresh List", command=self.refresh_maintenance_list).pack(side="right", padx=5)

    def update_maint_vehicle_dropdown(self):
        conn = sqlite3.connect(DB_FILE)
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

        success, msg = start_maintenance(vid, checklist_str, cost, notes)
        if success:
            messagebox.showinfo("Started", "Vehicle sent to maintenance. It is now unavailable for rent.")
            self.refresh_maintenance_list()
            # Clear form
            self.maint_cost_entry.delete(0, "end")
            self.maint_notes_entry.delete("1.0", "end")
            for var in self.check_vars.values(): var.set(False)
        else:
            messagebox.showerror("Error", msg)

    def refresh_maintenance_list(self):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        SELECT m.MaintenanceID, v.plate, m.checklist, m.cost, m.start_date, m.notes 
        FROM Maintenance m JOIN Vehicle v ON m.vehicle_id = v.VehicleID
        WHERE m.status='active'
        """)
        rows = cur.fetchall()
        conn.close()
        
        self.maint_list_box.configure(state="normal")
        self.maint_list_box.delete("1.0", "end")
        self.maint_list_box.insert("end", f"{'ID':<4} {'PLATE':<12} {'COST':<10} {'STARTED':<20} {'CHECKS'}\n")
        self.maint_list_box.insert("end", "-"*90+"\n")
        for mid, plate, check, cost, start, notes in rows:
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
        
        finish_maintenance(mid)
        messagebox.showinfo("Success", "Maintenance finished. Vehicle is available for rent.")
        self.finish_maint_id.delete(0, "end")
        self.refresh_maintenance_list()

def main():
    fix_db()
    init_db()
    login = LoginWindow()
    login.mainloop()

if __name__ == "__main__":
    main()