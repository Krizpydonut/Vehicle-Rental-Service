import sqlite3
from datetime import datetime, timedelta
import math

DB_FILE = "rental.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

class Customer:
    def __init__(self, name, phone, email, drivers_license=None):
        self.name = name
        self.phoneNumber = phone
        self.email = email
        self.driversLicense = drivers_license

    def provideDocumentation(self):
        """Returns the driver's license for verification."""
        return self.driversLicense

class Vehicle:
    def __init__(self, model, plate, vtype, base_price, vehicle_id=None, available=True):
        self.vehicleID = vehicle_id
        self.model = model
        self.licensePlate = plate
        self.type = vtype
        self.basePrice = base_price
        self.available = available

class Reservation:
    def __init__(self, vehicle: Vehicle, customer: Customer, start_dt_iso, end_dt_iso, driver_flag=False, location=""):
        self.reservationID = None
        self.vehicle = vehicle
        self.customer = customer
        self.startDatetime = start_dt_iso
        self.endDatetime = end_dt_iso
        self.driverFlag = driver_flag
        self.location = location
        self.totalCost = 0.0
        self.status = "active"

    def calculateCost(self):
        """Calculates total cost based on duration and driver fee."""
        DRIVER_FEE_PER_DAY = 500.0
        
        s_dt = datetime.fromisoformat(self.startDatetime)
        e_dt = datetime.fromisoformat(self.endDatetime)
        
        duration = e_dt - s_dt
        rental_days = duration.total_seconds() / (24 * 3600)
        days = math.ceil(rental_days) if rental_days > 0 else 1
        
        base_cost = self.vehicle.basePrice * days
        driver_fee = (DRIVER_FEE_PER_DAY * days) if self.driverFlag else 0.0
        
        self.totalCost = base_cost + driver_fee
        return self.totalCost

class Documentation:
    def __init__(self, reservation_id, doc_type="DamageContract"):
        self.reservationID = reservation_id
        self.type = doc_type

    def generateDocument(self, condition, cost, notes):
        """Creates a damage record in the database."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO DamageContract (reservation_id, condition, damage_cost, notes, created_at)
            VALUES (?,?,?,?,?)
        """, (self.reservationID, condition, cost, notes, datetime.now().isoformat()))
        conn.commit()
        conn.close()

class MaintenanceRecord:
    def __init__(self, vehicle_id, checklist, cost, notes):
        self.vehicleID = vehicle_id
        self.checklist = checklist
        self.cost = cost
        self.notes = notes

class VehicleRentalService:
    def __init__(self):
        self._init_db_schema()

    def _init_db_schema(self):
        """Ensures tables exist (replicates db.init_db functionality)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Vehicle (
            VehicleID INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT, plate TEXT UNIQUE, vtype TEXT, daily_rate REAL, available INTEGER DEFAULT 1
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Reservation (
            ReservationID INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER,
            customer_name TEXT, customer_phone TEXT, customer_email TEXT,
            driver_flag INTEGER, driver_license TEXT, start_datetime TEXT, end_datetime TEXT,
            location TEXT, driver_fee REAL, total_cost REAL, status TEXT DEFAULT 'active',
            FOREIGN KEY(vehicle_id) REFERENCES Vehicle(VehicleID)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS DamageContract (
            ContractID INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER,
            condition TEXT, damage_cost REAL, notes TEXT, created_at TEXT,
            FOREIGN KEY(reservation_id) REFERENCES Reservation(ReservationID)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Maintenance (
            MaintenanceID INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id INTEGER,
            checklist TEXT, cost REAL, start_date TEXT, end_date TEXT, notes TEXT, status TEXT DEFAULT 'active',
            FOREIGN KEY(vehicle_id) REFERENCES Vehicle(VehicleID)
        )""")
        conn.commit()
        conn.close()

    def add_new_vehicle(self, vehicle: Vehicle):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO Vehicle (model, plate, vtype, daily_rate) VALUES (?, ?, ?, ?)", 
                        (vehicle.model, vehicle.licensePlate, vehicle.type, vehicle.basePrice))
            conn.commit()
            conn.close()
            return True, "success"
        except sqlite3.IntegrityError:
            return False, "duplicate"
        except Exception as e:
            return False, str(e)

    def get_all_vehicles(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Vehicle ORDER BY VehicleID")
        return cur.fetchall()

    def check_availability(self, vehicle_id, start_iso, end_iso):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT available FROM Vehicle WHERE VehicleID=?", (vehicle_id,))
        v_row = cur.fetchone()
        if not v_row or v_row['available'] == 0: 
            conn.close()
            return False

        cur.execute("""
            SELECT 1 FROM Reservation
            WHERE vehicle_id = ? AND status = 'active' AND
            NOT (end_datetime <= ? OR start_datetime >= ?)
        """, (vehicle_id, start_iso, end_iso))
        
        is_free = cur.fetchone() is None
        conn.close()
        return is_free

    def make_reservation(self, vehicle_id, customer: Customer, start_iso, end_iso, driver_flag, location):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Vehicle WHERE VehicleID=?", (vehicle_id,))
        v_row = cur.fetchone()
        conn.close()

        if not v_row: raise ValueError("Vehicle not found")
        vehicle = Vehicle(v_row['model'], v_row['plate'], v_row['vtype'], v_row['daily_rate'], vehicle_id)

        if not self.check_availability(vehicle_id, start_iso, end_iso):
            raise ValueError("Vehicle is unavailable for these dates.")

        res = Reservation(vehicle, customer, start_iso, end_iso, driver_flag, location)
        res.calculateCost()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Reservation (vehicle_id, customer_name, customer_phone, customer_email,
            driver_flag, driver_license, start_datetime, end_datetime, driver_fee, total_cost, location)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (vehicle_id, customer.name, customer.phoneNumber, customer.email, int(driver_flag), 
              customer.driversLicense, start_iso, end_iso, (res.totalCost - (vehicle.basePrice * 1)), # storing simplified driver fee
              res.totalCost, location))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid, res.totalCost

    def get_active_reservations(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.status
            FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
            WHERE r.status = 'active' ORDER BY r.start_datetime
        """)
        return cur.fetchall()
    
    def get_active_reservations_dates(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT start_datetime, end_datetime, ReservationID FROM Reservation WHERE status='active'")
        return cur.fetchall()

    def get_bookings_for_date(self, start_day, end_day):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.location
        FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
        WHERE r.status='active' AND NOT (r.end_datetime <= ? OR r.start_datetime >= ?)
        """, (start_day, end_day))
        return cur.fetchall()

    def get_reservation_details(self, rid):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, 
            r.driver_flag, r.driver_license, r.total_cost, r.vehicle_id
            FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
            WHERE r.ReservationID=?
        """, (rid,))
        return cur.fetchone()

    def get_damage_contracts(self, rid):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT condition, damage_cost, notes, created_at FROM DamageContract WHERE reservation_id=?", (rid,))
        return cur.fetchall()

    def finalize_return(self, rid):
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Calculate totals
        cur.execute("SELECT SUM(damage_cost) FROM DamageContract WHERE reservation_id=?", (rid,))
        res = cur.fetchone()
        dmg_total = res[0] if res[0] else 0.0
        
        cur.execute("SELECT total_cost, vehicle_id FROM Reservation WHERE ReservationID=?", (rid,))
        row = cur.fetchone()
        if not row: return False
        
        base, vid = row['total_cost'], row['vehicle_id']
        final_total = base + dmg_total
        
        cur.execute("UPDATE Reservation SET status='returned', total_cost=? WHERE ReservationID=?", (final_total, rid))
        cur.execute("UPDATE Vehicle SET available=1 WHERE VehicleID=?", (vid,))
        conn.commit()
        conn.close()
        return base, dmg_total, final_total

    def start_maintenance(self, record: MaintenanceRecord):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM Reservation WHERE vehicle_id=? AND status='active'", (record.vehicleID,))
        if cur.fetchone():
            conn.close()
            return False, "Vehicle has active reservation."
            
        cur.execute("""
            INSERT INTO Maintenance (vehicle_id, checklist, cost, start_date, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (record.vehicleID, record.checklist, record.cost, datetime.now().isoformat(), record.notes))
        
        cur.execute("UPDATE Vehicle SET available=0 WHERE VehicleID=?", (record.vehicleID,))
        conn.commit()
        conn.close()
        return True, "Success"

    def get_active_maintenance(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT m.MaintenanceID, v.plate, m.checklist, m.cost, m.start_date, m.notes 
        FROM Maintenance m JOIN Vehicle v ON m.vehicle_id = v.VehicleID
        WHERE m.status='active'
        """)
        return cur.fetchall()

    def finish_maintenance(self, mid):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Maintenance SET status='completed', end_date=? WHERE MaintenanceID=?", (datetime.now().isoformat(), mid))
        cur.execute("SELECT vehicle_id FROM Maintenance WHERE MaintenanceID=?", (mid,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE Vehicle SET available=1 WHERE VehicleID=?", (row['vehicle_id'],))
        conn.commit()
        conn.close()

    def get_vehicle_types(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT vtype FROM Vehicle")
        return [r[0] for r in cur.fetchall()]

    def get_models_by_type(self, vtype):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT model FROM Vehicle WHERE vtype=?", (vtype,))
        return [r[0] for r in cur.fetchall()]
        
    def get_available_vehicles_list(self, vtype, model):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT VehicleID, plate FROM Vehicle WHERE vtype=? AND model=? AND available=1", (vtype, model))
        return [f"{r['VehicleID']} - {r['plate']}" for r in cur.fetchall()]

    def get_all_vehicle_list_fmt(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT VehicleID, plate, model FROM Vehicle ORDER BY plate")
        return [f"{r['VehicleID']} - {r['plate']} ({r['model']})" for r in cur.fetchall()]