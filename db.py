import sqlite3
from datetime import datetime, timedelta

DB_FILE = "rental.db"
DRIVER_FEE_PER_DAY = 500.0 

def init_db():
    """Initializes the SQLite database tables, updated to include Vehicle brand and year."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Customer (
        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        drivers_license TEXT UNIQUE,
        government_id TEXT 
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Vehicle (
        VehicleID INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,  
        model TEXT,
        year INTEGER, 
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
        customer_id INTEGER,  
        driver_flag INTEGER,
        start_datetime TEXT,
        end_datetime TEXT,
        location TEXT,
        driver_fee REAL,
        total_cost REAL,
        status TEXT DEFAULT 'active',
        distance_km REAL DEFAULT 0.0, -- NEW FIELD ADDED
        FOREIGN KEY(vehicle_id) REFERENCES Vehicle(VehicleID),
        FOREIGN KEY(customer_id) REFERENCES Customer(CustomerID)
    )
    """)
    
    try:
        cur.execute("ALTER TABLE Reservation ADD COLUMN distance_km REAL DEFAULT 0.0")
    except sqlite3.OperationalError as e:
        if "duplicate column name: distance_km" in str(e):
            pass
        else:
            print(f"Migration error: {e}")


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
    CREATE TABLE IF NOT EXISTS Payment (
        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        amount REAL,
        status TEXT,
        method TEXT,
        frequency TEXT,
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


def find_or_create_customer(name, phone, email, license, government_id="N/A"):
    drivers_license_sql = license if (license and license.strip() and license != "N/A") else None

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    try:
        cur.execute("""
        INSERT INTO Customer (name, phone, email, drivers_license, government_id)
        VALUES (?, ?, ?, ?, ?)
        """, (name, phone, email, drivers_license_sql, government_id)) 
        conn.commit()
        customer_id = cur.lastrowid
        conn.close()
        return customer_id
        
    except sqlite3.IntegrityError:
        if drivers_license_sql:
            sql = "SELECT CustomerID FROM Customer WHERE drivers_license=? OR email=?"
            params = (drivers_license_sql, email)
        else:
            sql = "SELECT CustomerID FROM Customer WHERE email=?"
            params = (email,)
            
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        
        if row:
            return row[0] 
        else:
            raise ValueError("A customer with this email or driver's license already exists, but the record could not be retrieved for reuse.")
    
    except Exception as e:
        conn.close()
        raise e

def add_vehicle(brand, model, year, plate, vtype, rate):
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("INSERT INTO Vehicle (brand, model, year, plate, vtype, daily_rate) VALUES (?, ?, ?, ?, ?, ?)", (brand, model, year, plate, vtype, rate))
        conn.commit()
        conn.close()
        return True, "success"
    except sqlite3.IntegrityError:
        return False, "duplicate"
    except Exception as e:
        return False, str(e)

def get_all_vehicles():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT VehicleID, brand, model, year, plate, vtype, daily_rate FROM Vehicle ORDER BY VehicleID")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_vehicle_types():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT vtype FROM Vehicle ORDER BY vtype")
    types = [row[0] for row in cur.fetchall()]
    conn.close()
    return types

def get_brands_by_type(vtype):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT brand FROM Vehicle WHERE vtype=? ORDER BY brand", (vtype,))
    brands = [row[0] for row in cur.fetchall()]
    conn.close()
    return brands

def get_years_by_type_and_brand(vtype, brand):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT year FROM Vehicle WHERE vtype=? AND brand=? ORDER BY year DESC", (vtype, brand))
    years = [str(row[0]) for row in cur.fetchall()]
    conn.close()
    return years

def get_models_by_type_brand_and_year(vtype, brand, year):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT model FROM Vehicle WHERE vtype=? AND brand=? AND year=? ORDER BY model", (vtype, brand, year))
    models = [row[0] for row in cur.fetchall()]
    conn.close()
    return models

def get_available_vehicles_by_model(vtype, brand, year, model):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT VehicleID, plate FROM Vehicle WHERE vtype=? AND brand=? AND year=? AND model=? AND available=1 ORDER BY plate", (vtype, brand, year, model))
    vehicles = [f"{vid} - {plate}" for vid, plate in cur.fetchall()]
    conn.close()
    return vehicles

def is_vehicle_available(vehicle_id, start_dt_iso, end_dt_iso, exclude_res_id=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT available FROM Vehicle WHERE VehicleID=?", (vehicle_id,))
    available_status = cur.fetchone()
    if available_status is None or available_status[0] == 0:
        conn.close()
        return False
    
    sql = """
    SELECT 1 FROM Reservation
    WHERE vehicle_id = ? AND status = 'active' AND
          NOT (end_datetime <= ? OR start_datetime >= ?)
    """
    params = [vehicle_id, start_dt_iso, end_dt_iso]
    
    if exclude_res_id is not None:
        sql += " AND ReservationID != ?"
        params.append(exclude_res_id)
    
    cur.execute(sql, tuple(params))
    
    has_overlap = cur.fetchone() is not None
    conn.close()
    return not has_overlap

def calculate_cost(vehicle_id, start_dt_iso, end_dt_iso, driver_flag):
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

def create_reservation(vehicle_id, customer_id, driver_flag, start_dt_iso, end_dt_iso, location):
    total_cost, driver_fee = calculate_cost(vehicle_id, start_dt_iso, end_dt_iso, driver_flag)
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO Reservation (vehicle_id, customer_id, driver_flag, start_datetime, end_datetime, driver_fee, total_cost, location)
    VALUES (?,?,?,?,?,?,?,?)
    """, (vehicle_id, customer_id, int(driver_flag),
          start_dt_iso, end_dt_iso, driver_fee, total_cost, location))
    conn.commit()
    res_id = cur.lastrowid
    
    cur.execute("""
    INSERT INTO Payment (reservation_id, amount, status, method, frequency, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (res_id, total_cost, 'pending', 'Estimate', 'Daily', datetime.now().isoformat()))
    conn.commit()
    
    conn.close()
    return res_id, total_cost

def update_reservation_end_date(res_id, new_end_dt_iso):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
    SELECT vehicle_id, driver_flag, start_datetime
    FROM Reservation 
    WHERE ReservationID=? AND status='active'
    """, (res_id,))
    row = cur.fetchone()
    
    if row is None:
        conn.close()
        raise ValueError("Active reservation not found.")
        
    vehicle_id, driver_flag, start_dt_iso = row
    
    start_dt = datetime.fromisoformat(start_dt_iso)
    new_end_dt = datetime.fromisoformat(new_end_dt_iso)
    
    if new_end_dt <= start_dt:
        conn.close()
        raise ValueError("New return time must be after the original pickup time.")
    
    if not is_vehicle_available(vehicle_id, start_dt_iso, new_end_dt_iso, exclude_res_id=res_id):
        conn.close()
        raise ValueError("Vehicle is unavailable for the extended period (conflicts with another booking).")

    total_cost, driver_fee = calculate_cost(vehicle_id, start_dt_iso, new_end_dt_iso, driver_flag)

    cur.execute("""
    UPDATE Reservation 
    SET end_datetime=?, total_cost=?, driver_fee=?
    WHERE ReservationID=?
    """, (new_end_dt_iso, total_cost, driver_fee, res_id))

    cur.execute("""
    UPDATE Payment 
    SET amount=?
    WHERE reservation_id=? AND method='Estimate'
    """, (total_cost, res_id))
    
    conn.commit()
    conn.close()
    return total_cost

def list_active_reservations():
    """Returns a list of all active reservations with customer name, location, and vehicle details."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.ReservationID, v.plate, v.model, c.name, r.start_datetime, r.end_datetime, r.status, r.location
    FROM Reservation r 
    JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    JOIN Customer c ON r.customer_id = c.CustomerID
    WHERE r.status = 'active'
    ORDER BY r.start_datetime
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_active_reservations_dates():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT start_datetime, end_datetime, ReservationID FROM Reservation WHERE status='active'")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_bookings_for_date(start_day_iso, end_day_iso):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT r.ReservationID, v.plate, v.model, c.name, r.start_datetime, r.end_datetime, r.location
    FROM Reservation r 
    JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    JOIN Customer c ON r.customer_id = c.CustomerID
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
    SELECT 
        r.ReservationID, v.plate, v.model, c.name, r.start_datetime, r.end_datetime, 
        r.driver_flag, c.drivers_license, r.total_cost
    FROM Reservation r 
    JOIN Vehicle v ON r.vehicle_id = v.VehicleID
    JOIN Customer c ON r.customer_id = c.CustomerID
    WHERE r.ReservationID=?
    """, (rid,))
    row = cur.fetchone()
    conn.close()
    return row

def get_damage_contracts(reservation_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT condition, damage_cost, notes, created_at FROM DamageContract WHERE reservation_id=?", (reservation_id,))
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

def get_final_costs(rid):
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

def finalize_reservation(rid, final_cost, distance_km):
    
    base, dmg_total, vehicle_id = get_final_costs(rid)
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("UPDATE Reservation SET status='returned', total_cost=?, distance_km=? WHERE ReservationID=?", 
                (final_cost, distance_km, rid))
    
    cur.execute("UPDATE Payment SET amount=?, status='paid', method='Finalized' WHERE reservation_id=?", (final_cost, rid))

    cur.execute("UPDATE Vehicle SET available=1 WHERE VehicleID=?", (vehicle_id,))
    conn.commit()
    conn.close()

def get_all_vehicle_list():
    """Returns all vehicle details formatted for maintenance dropdown: ID - Plate (Brand Model)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT VehicleID, plate, model, brand FROM Vehicle ORDER BY plate")
    vehs = [f"{vid} - {plate} ({brand} {model})" for vid, plate, model, brand in cur.fetchall()]
    conn.close()
    return vehs

def start_maintenance(vid, checklist_str, cost, notes):
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
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    SELECT 
        m.MaintenanceID, v.plate, v.brand, v.model, m.checklist, m.cost, m.start_date, m.notes 
    FROM Maintenance m 
    JOIN Vehicle v ON m.vehicle_id = v.VehicleID
    WHERE m.status='active'
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def finish_maintenance(mid):
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

def get_vehicle_usage_report():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT VehicleID, brand, model, plate FROM Vehicle")
    all_vehicles = cur.fetchall()

    usage_data = {}
    for vid, brand, model, plate in all_vehicles:
        usage_data[vid] = {
            'vehicle_id': vid,
            'plate': plate,
            'brand': brand,
            'model': model,
            'usage_hours': 0.0,
            'reservation_count': 0,
            'total_distance_km': 0.0
        }
        
    cur.execute("""
    SELECT 
        r.vehicle_id, 
        r.start_datetime, 
        r.end_datetime,
        r.distance_km -- NEW: Fetch the actual distance traveled
    FROM Reservation r 
    WHERE r.status IN ('active', 'returned')
    """)
    
    reservation_rows = cur.fetchall()
    conn.close()
    
    for vid, start_dt_iso, end_dt_iso, distance_km in reservation_rows:
        if vid in usage_data:
            try:
                start_dt = datetime.fromisoformat(start_dt_iso)
                end_dt = datetime.fromisoformat(end_dt_iso)
                
                duration = end_dt - start_dt
                duration_hours = duration.total_seconds() / 3600.0
                
                usage_data[vid]['usage_hours'] += duration_hours
                usage_data[vid]['reservation_count'] += 1
                usage_data[vid]['total_distance_km'] += distance_km or 0.0
            except Exception:
                continue
                
    return list(usage_data.values())

def get_location_usage_report():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
    SELECT location, COUNT(ReservationID) AS reservation_count
    FROM Reservation
    WHERE status IN ('active', 'returned') AND location IS NOT NULL AND location != ''
    GROUP BY location
    ORDER BY reservation_count DESC
    """)
    
    rows = cur.fetchall()
    conn.close()
    
    results = []
    for location, count in rows:
        results.append({
            'location': location,
            'reservation_count': count
        })
        
    return results

init_db()