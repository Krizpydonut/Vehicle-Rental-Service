import sqlite3
from datetime import datetime, timedelta

DB_FILE = "rental.db"
DRIVER_FEE_PER_DAY = 500.0 
BASE_DAILY_RATE = 1500.0 

def init_db():
    """Initializes the SQLite database tables."""
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
        start_date TEXT,
        end_date TEXT,
        notes TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(vehicle_id) REFERENCES Vehicle(VehicleID)
    )
    """)
    conn.commit()
    conn.close()

def add_vehicle(model, plate, vtype, rate):
    """Adds a new vehicle to the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("INSERT INTO Vehicle (model, plate, vtype, daily_rate) VALUES (?, ?, ?, ?)", (model, plate, vtype, rate))
        conn.commit()
        conn.close()
        return True, "success"
    except sqlite3.IntegrityError:
        return False, "duplicate"
    except Exception as e:
        return False, str(e)

def get_all_vehicles():
    """Returns all vehicles in the database."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT VehicleID, model, plate, vtype, daily_rate FROM Vehicle ORDER BY VehicleID")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_vehicle_types():
    """Returns a list of distinct vehicle types."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT vtype FROM Vehicle ORDER BY vtype")
    types = [row[0] for row in cur.fetchall()]
    conn.close()
    return types

def get_models_by_type(vtype):
    """Returns a list of distinct models for a given vehicle type."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT model FROM Vehicle WHERE vtype=? ORDER BY model", (vtype,))
    models = [row[0] for row in cur.fetchall()]
    conn.close()
    return models

def get_available_vehicles_by_model(vtype, model):
    """Returns a list of available vehicles (ID and plate) by type and model."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT VehicleID, plate FROM Vehicle WHERE vtype=? AND model=? AND available=1 ORDER BY plate", (vtype, model))
    vehicles = [f"{vid} - {plate}" for vid, plate in cur.fetchall()]
    conn.close()
    return vehicles

def is_vehicle_available(vehicle_id, start_dt_iso, end_dt_iso):
    """Checks if a vehicle is available for the given date range."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT available FROM Vehicle WHERE VehicleID=?", (vehicle_id,))
    available_status = cur.fetchone()
    if available_status is None or available_status[0] == 0:
        conn.close()
        return False

    cur.execute("""
    SELECT 1 FROM Reservation
    WHERE vehicle_id = ? AND status = 'active' AND
          NOT (end_datetime <= ? OR start_datetime >= ?)
    """, (vehicle_id, start_dt_iso, end_dt_iso))
    
    has_overlap = cur.fetchone() is not None
    conn.close()
    return not has_overlap

def calculate_cost(vehicle_id, start_dt_iso, end_dt_iso, driver_flag):
    """Calculates the estimated total cost."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT daily_rate FROM Vehicle WHERE VehicleID=?", (vehicle_id,))
    rate_row = cur.fetchone()
    conn.close()
    
    if rate_row is None:
        raise ValueError("Vehicle not found.")
        
    daily_rate = rate_row[0]
    
    start_dt = datetime.fromisoformat(start_dt_iso)
    end_dt = datetime.fromisoformat(end_dt_iso)
    
    duration = end_dt - start_dt
    
    rental_days = duration.total_seconds() / (24 * 3600)
    import math
    days = math.ceil(rental_days) if rental_days > 0 else 1
    
    base_cost = daily_rate * days
    
    driver_fee = 0.0
    if driver_flag:
        driver_fee = DRIVER_FEE_PER_DAY * days
        
    total_cost = base_cost + driver_fee
    return total_cost, driver_fee

def create_reservation(vehicle_id, customer_name, phone, email, driver_flag, driver_license, start_dt_iso, end_dt_iso, location):
    """Creates a new reservation entry."""
    total_cost, driver_fee = calculate_cost(vehicle_id, start_dt_iso, end_dt_iso, driver_flag)
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
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
    """Returns a list of all active reservations."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.status
    FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    WHERE r.status = 'active'
    ORDER BY r.start_datetime
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_active_reservations_dates():
    """Returns dates for active reservations for the calendar."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT start_datetime, end_datetime, ReservationID FROM Reservation WHERE status='active'")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_bookings_for_date(start_day_iso, end_day_iso):
    """Returns reservation details that overlap with a specific date."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.location
    FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    WHERE r.status='active' AND
         NOT (r.end_datetime <= ? OR r.start_datetime >= ?)
    ORDER BY r.start_datetime
    """, (start_day_iso, end_day_iso))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_reservation_details(rid):
    """Returns detailed information for a single reservation."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.driver_flag, r.driver_license, r.total_cost
    FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    WHERE r.ReservationID=?
    """, (rid,))
    row = cur.fetchone()
    conn.close()
    return row

def get_damage_contracts(reservation_id):
    """Returns a list of damage entries for a reservation."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT condition, damage_cost, notes, created_at FROM DamageContract WHERE reservation_id=?", (reservation_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_damage(reservation_id, condition, cost, notes=""):
    """Adds a damage contract entry."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO DamageContract (reservation_id, condition, damage_cost, notes, created_at)
    VALUES (?,?,?,?,?)
    """, (reservation_id, condition, cost, notes, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_final_costs(rid):
    """Calculates the total base cost and damage cost for a reservation."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT SUM(damage_cost) FROM DamageContract WHERE reservation_id=?", (rid,))
    dmg_total = cur.fetchone()[0] or 0.0
    cur.execute("SELECT total_cost, vehicle_id FROM Reservation WHERE ReservationID=?", (rid,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise ValueError("Reservation not found.")
    base = row[0]
    return base, dmg_total, row[1] 

def finalize_reservation(rid):
    """Marks a reservation as returned and makes the vehicle available."""
    base, dmg_total, vehicle_id = get_final_costs(rid)
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE Reservation SET status='returned', total_cost=? WHERE ReservationID=?", (base + dmg_total, rid))
    cur.execute("UPDATE Vehicle SET available=1 WHERE VehicleID=?", (vehicle_id,))
    conn.commit()
    conn.close()

def get_all_vehicle_list():
    """Returns a list of all vehicles (ID, plate, model) for dropdowns."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT VehicleID, plate, model FROM Vehicle ORDER BY plate")
    vehs = [f"{vid} - {plate} ({model})" for vid, plate, model in cur.fetchall()]
    conn.close()
    return vehs

def start_maintenance(vid, checklist_str, cost, notes):
    """Sends a vehicle to maintenance and marks it unavailable."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM Maintenance WHERE vehicle_id=? AND status='active'", (vid,))
    if cur.fetchone():
        conn.close()
        return False, "Vehicle is already in active maintenance."

    cur.execute("SELECT 1 FROM Reservation WHERE vehicle_id=? AND status='active'", (vid,))
    if cur.fetchone():
        conn.close()
        return False, "Vehicle has active reservation and cannot be sent to maintenance yet."

    cur.execute("""
    INSERT INTO Maintenance (vehicle_id, checklist, cost, start_date, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (vid, checklist_str, cost, datetime.now().isoformat(), notes))
    
    cur.execute("UPDATE Vehicle SET available=0 WHERE VehicleID=?", (vid,))
    conn.commit()
    conn.close()
    return True, "Success"

def get_active_maintenance():
    """Returns a list of vehicles currently in maintenance."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT m.MaintenanceID, v.plate, m.checklist, m.cost, m.start_date, m.notes 
    FROM Maintenance m JOIN Vehicle v ON m.vehicle_id = v.VehicleID
    WHERE m.status='active'
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def finish_maintenance(mid):
    """Finishes a maintenance record and makes the vehicle available."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("UPDATE Maintenance SET status='completed', end_date=? WHERE MaintenanceID=?", (datetime.now().isoformat(), mid))
    
    cur.execute("SELECT vehicle_id FROM Maintenance WHERE MaintenanceID=?", (mid,))
    row = cur.fetchone()
    if row:
        vid = row[0]
        cur.execute("UPDATE Vehicle SET available=1 WHERE VehicleID=?", (vid,))
    
    conn.commit()
    conn.close()

init_db()