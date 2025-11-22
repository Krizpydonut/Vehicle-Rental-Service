import sqlite3
from datetime import datetime, timedelta

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