import db
from datetime import datetime

class Customer:
    def __init__(self, name, phone, email, drivers_license=None):
        self.name = name
        self.phoneNumber = phone
        self.email = email
        self.driversLicense = drivers_license if drivers_license else None

class Vehicle:
    def __init__(self, brand, model, year, plate, vtype, base_price, vehicle_id=None, available=True):
        self.vehicleID = vehicle_id
        self.brand = brand
        self.year = year
        self.model = model
        self.licensePlate = plate
        self.type = vtype
        self.basePrice = base_price
        self.available = available

class Documentation:
    def __init__(self, reservation_id, doc_type="DamageContract"):
        self.reservationID = reservation_id
        self.type = doc_type

    def generateDocument(self, condition, cost, notes):
        """Creates a damage record in the database using db.py."""
        db.add_damage(self.reservationID, condition, cost, notes)

class MaintenanceRecord:
    def __init__(self, vehicle_id, checklist, cost, notes):
        self.vehicleID = vehicle_id
        self.checklist = checklist
        self.cost = cost
        self.notes = notes

class VehicleRentalService:
    def __init__(self):
        pass

    def add_new_vehicle(self, vehicle: Vehicle):
        return db.add_vehicle(vehicle.brand, vehicle.model, vehicle.year, vehicle.licensePlate, vehicle.type, vehicle.basePrice)

    def get_all_vehicles(self):
        """Fetches vehicles and converts tuples to dicts for the GUI."""
        rows = db.get_all_vehicles()
        result = []
        for r in rows:
            result.append({
                "VehicleID": r[0],
                "brand": r[1],
                "model": r[2],
                "year": r[3],
                "plate": r[4],
                "vtype": r[5],
                "daily_rate": r[6]
            })
        return result

    def get_vehicle_types(self):
        return db.get_vehicle_types()
    
    def get_brands_by_type(self, vtype):
        return db.get_brands_by_type(vtype)

    def get_years_by_type_and_brand(self, vtype, brand):
        """NEW: Filters distinct years by type and brand."""
        return db.get_years_by_type_and_brand(vtype, brand)
        
    def get_models_by_type_brand_and_year(self, vtype, brand, year):
        """UPDATED: Filters models by type, brand, and year."""
        return db.get_models_by_type_brand_and_year(vtype, brand, year)

    def get_available_vehicles_list(self, vtype, brand, year, model):
        """UPDATED: Filters available vehicles by type, brand, year, and model."""
        return db.get_available_vehicles_by_model(vtype, brand, year, model)
    
    def get_all_vehicle_list_fmt(self):
        return db.get_all_vehicle_list()

    def make_reservation(self, vehicle_id, customer: Customer, start_iso, end_iso, driver_flag, location):
        customer_id = db.find_or_create_customer(
            customer.name, 
            customer.phoneNumber, 
            customer.email, 
            customer.driversLicense
        )
        
        if not db.is_vehicle_available(vehicle_id, start_iso, end_iso):
             raise ValueError("Vehicle is unavailable for these dates.")

        res_id, total_cost = db.create_reservation(
            vehicle_id, customer_id, driver_flag, start_iso, end_iso, location
        )
        return res_id, total_cost

    def get_active_reservations(self):
        rows = db.list_active_reservations()
        result = []
        for r in rows:
            result.append({
                "ReservationID": r[0],
                "plate": r[1],
                "model": r[2],
                "customer_name": r[3],
                "start_datetime": r[4],
                "end_datetime": r[5],
                "status": r[6],
                "location": r[7]
            })
        return result
    
    def get_active_reservations_dates(self):
        return db.get_active_reservations_dates()
    
    def get_active_reservations_dropdown_fmt(self):
        """Fetches active reservations formatted for a GUI dropdown: 'ID - Plate (Customer)'"""
        rows = db.list_active_reservations()
        result = []
        for r in rows:
            result.append(f"{r[0]} - {r[1]} ({r[3]})")
        return result

    def get_bookings_for_date(self, start_day, end_day):
        rows = db.get_bookings_for_date(start_day, end_day)
        result = []
        for r in rows:
            result.append({
                "ReservationID": r[0],
                "plate": r[1],
                "model": r[2],
                "customer_name": r[3],
                "start_datetime": r[4],
                "end_datetime": r[5],
                "location": r[6]
            })
        return result

    def get_reservation_details(self, rid):
        row = db.get_reservation_details(rid)
        if not row: return None
        return {
            "ReservationID": row[0],
            "plate": row[1],
            "model": row[2],
            "customer_name": row[3],
            "start_datetime": row[4],
            "end_datetime": row[5],
            "driver_flag": row[6],
            "driver_license": row[7],
            "total_cost": row[8]
        }

    def get_damage_contracts(self, rid):
        rows = db.get_damage_contracts(rid)
        result = []
        for r in rows:
            result.append({
                "condition": r[0],
                "damage_cost": r[1],
                "notes": r[2],
                "created_at": r[3]
            })
        return result

    def finalize_return(self, rid, distance_km):
        base, dmg_total, vid = db.get_final_costs(rid)
        final_total = base + dmg_total
        
        db.finalize_reservation(rid, final_total, distance_km)
        
        return base, dmg_total, final_total
    
    def update_reservation_return(self, res_id, new_end_iso):
        """Logic to update the reservation end time and recalculate cost."""
        return db.update_reservation_end_date(res_id, new_end_iso)

    def start_maintenance(self, record: MaintenanceRecord):
        return db.start_maintenance(record.vehicleID, record.checklist, record.cost, record.notes)

    def get_active_maintenance(self):
        rows = db.get_active_maintenance()
        result = []
        for r in rows:
            result.append({
                "MaintenanceID": r[0],
                "plate": r[1],
                "checklist": r[2],
                "cost": r[3],
                "start_date": r[4],
                "notes": r[5]
            })
        return result

    def finish_maintenance(self, mid):
        db.finish_maintenance(mid)
        
    # --- UPDATED: Report Method ---
    def get_usage_report(self):
        """
        Retrieves vehicle usage, formats total distance traveled, 
        and formats the usage time for the report.
        """
        report_data = db.get_vehicle_usage_report()
        
        for item in report_data:
            # Distance is now retrieved directly from DB (sum of distance_km)
            item['total_distance_km'] = item['total_distance_km']
            
            # Convert usage hours to a readable format (Days and Hours)
            hours = item['usage_hours']
            days = int(hours // 24)
            remaining_hours = int(hours % 24)
            # Use f-string for displayable string
            item['usage_display'] = f"{days} days, {remaining_hours} hours"
            
        return report_data
    
    def get_location_report(self):
        """Retrieves and formats location usage data."""
        return db.get_location_usage_report()