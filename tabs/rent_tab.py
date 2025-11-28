import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from rental_system import Customer
from .base_tab import BaseTab

class RentTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self._reservation_update_map = {}
        self.build_ui()
        self.update_type_dropdown()
        self.update_reservation_dropdown()

    def validate_number(self, P):
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
        
        vcmd = (self.register(self.validate_number), '%P')
        
        col0 = ctk.CTkFrame(form)
        col0.grid(row=0, column=0, padx=3, pady=3, sticky="nsew") 
        col0.grid_columnconfigure(0, weight=0)
        col0.grid_columnconfigure(1, weight=1)

        row_index = 0
        
        ctk.CTkLabel(col0, text="Vehicle Type:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.vehicle_type_var = ctk.StringVar()
        self.vehicle_type_dropdown = ctk.CTkOptionMenu(col0, values=[], variable=self.vehicle_type_var, command=self.update_brand_dropdown)
        self.vehicle_type_dropdown.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1

        ctk.CTkLabel(col0, text="Vehicle Brand:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.vehicle_brand_var = ctk.StringVar()
        self.vehicle_brand_dropdown = ctk.CTkOptionMenu(col0, values=[], variable=self.vehicle_brand_var, command=self.update_year_dropdown)
        self.vehicle_brand_dropdown.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
        row_index += 1
        
        ctk.CTkLabel(col0, text="Vehicle Year:").grid(row=row_index, column=0, padx=5, pady=7, sticky="w")
        self.vehicle_year_var = ctk.StringVar()
        self.vehicle_year_dropdown = ctk.CTkOptionMenu(col0, values=[], variable=self.vehicle_year_var, command=self.update_model_dropdown)
        self.vehicle_year_dropdown.grid(row=row_index, column=1, padx=5, pady=7, sticky="ew")
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
        self.driver_license_entry.grid(row=row_index, column=0, columnspan=2, padx=5, pady=7, sticky="ew")
        
        col2.grid_rowconfigure(row_index, weight=0) 
        row_index += 1 

        ctk.CTkButton(col2, text="Check Availability & Reserve", command=self.handle_reserve).grid(row=row_index, column=0, columnspan=2, pady=(10, 5), padx=5, sticky="s")
        col2.grid_rowconfigure(row_index, weight=1)
        
        self.toggle_driver_fields()

        update_frame = ctk.CTkFrame(tab)
        update_frame.pack(padx=5, pady=5, fill="x")
        update_frame.grid_columnconfigure(0, weight=1)
        update_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(update_frame, text="Update Active Reservation (Change Return Date)", 
                     font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5,10))

        update_left = ctk.CTkFrame(update_frame)
        update_left.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        update_left.grid_columnconfigure(0, weight=0)
        update_left.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(update_left, text="Reservation ID:").grid(row=0, column=0, padx=5, pady=7, sticky="w")
        
        self.update_res_var = ctk.StringVar()
        self.update_res_dropdown = ctk.CTkOptionMenu(update_left, variable=self.update_res_var, values=[], width=250)
        self.update_res_dropdown.grid(row=0, column=1, padx=5, pady=7, sticky="ew")

        update_right = ctk.CTkFrame(update_frame)
        update_right.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        update_right.grid_columnconfigure(0, weight=0)
        update_right.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(update_right, text="New Return Date:").grid(row=0, column=0, padx=5, pady=7, sticky="w")
        self.update_return_date = DateEntry(update_right, date_pattern="yyyy-mm-dd")
        self.update_return_date.grid(row=0, column=1, padx=5, pady=7, sticky="ew")

        ctk.CTkLabel(update_right, text="New Return Time:").grid(row=1, column=0, padx=5, pady=7, sticky="w")
        self.update_return_time = ctk.CTkEntry(update_right, placeholder_text="HH:MM (24h)")
        self.update_return_time.grid(row=1, column=1, padx=5, pady=7, sticky="ew")

        ctk.CTkButton(update_frame, text="Update Return Date", command=self.handle_update_reservation).grid(row=2, column=0, columnspan=2, pady=10)
        
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

    def update_reservation_dropdown(self):
        reservations_full = self.system.get_active_reservations_dropdown_fmt()
        
        reservations_display = []
        self._reservation_update_map = {}
        
        for item in reservations_full:
            parts = item.split(" - ", 1) 
            if len(parts) > 1:
                display_text = parts[1]
                reservations_display.append(display_text)
                self._reservation_update_map[display_text] = item
            else:
                reservations_display.append(item) 
                self._reservation_update_map[item] = item
                
        self.update_res_dropdown.configure(values=reservations_display)
        
        if reservations_display:
            self.update_res_var.set(reservations_display[0])
        else:
            self.update_res_var.set("No active reservations")
            self.update_res_dropdown.configure(values=["No active reservations"])
            

    def get_selected_update_rid(self):
        selected_display_text = self.update_res_var.get()
        
        if not selected_display_text or "No active reservations" in selected_display_text:
            messagebox.showwarning("Missing", "Select an active reservation ID to update.")
            return None
        
        full_value = self._reservation_update_map.get(selected_display_text)
        
        if not full_value:
            messagebox.showerror("Invalid", "Could not find reservation details.")
            return None
            
        try:
            return int(full_value.split(" - ")[0])
        except Exception:
            messagebox.showerror("Invalid", "Selected reservation format is invalid.")
            return None


    def update_type_dropdown(self, *args):
        types = self.system.get_vehicle_types()
        self.vehicle_type_dropdown.configure(values=types)
        if types:
            self.vehicle_type_var.set(types[0])
            self.update_brand_dropdown(types[0])
        else:
            self.vehicle_type_var.set("")
            self.update_brand_dropdown("")

    def update_brand_dropdown(self, selected_type):
        brands = self.system.get_brands_by_type(selected_type)
        self.vehicle_brand_dropdown.configure(values=brands)
        if brands:
            self.vehicle_brand_var.set(brands[0])
            self.update_year_dropdown(brands[0])
        else:
            self.vehicle_brand_var.set("")
            self.update_year_dropdown("")

    def update_year_dropdown(self, selected_brand):
        selected_type = self.vehicle_type_var.get()
        years = self.system.get_years_by_type_and_brand(selected_type, selected_brand)
        self.vehicle_year_dropdown.configure(values=years)
        if years:
            self.vehicle_year_var.set(years[0])
            self.update_model_dropdown(years[0])
        else:
            self.vehicle_year_var.set("")
            self.update_model_dropdown("")

    def update_model_dropdown(self, selected_year):
        selected_type = self.vehicle_type_var.get()
        selected_brand = self.vehicle_brand_var.get()
        models = self.system.get_models_by_type_brand_and_year(selected_type, selected_brand, selected_year)
        self.vehicle_model_dropdown.configure(values=models)
        if models:
            self.vehicle_model_var.set(models[0])
            self.update_vehicle_dropdown(models[0])
        else:
            self.vehicle_model_var.set("")
            self.update_vehicle_dropdown("")

    def update_vehicle_dropdown(self, selected_model):
        selected_type = self.vehicle_type_var.get()
        selected_brand = self.vehicle_brand_var.get()
        selected_year = self.vehicle_year_var.get()
        vehicles = self.system.get_available_vehicles_list(selected_type, selected_brand, selected_year, selected_model)
        self.vehicle_dropdown.configure(values=vehicles)
        if vehicles:
            self.vehicle_id_var.set(vehicles[0])
        else:
            self.vehicle_id_var.set("")
            
    def toggle_driver_fields(self):
        if self.driver_var.get():
            self.driver_license_entry.grid_forget()
        else:
            self.driver_license_entry.grid(row=6, column=0, columnspan=2, padx=5, pady=7, sticky="ew")
            
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
        else:
             driver_license = ""
        
        customer = Customer(name, phone, email, driver_license)

        try:
            res_id, total_cost = self.system.make_reservation(
                vehicle_id, customer, start_dt.isoformat(), end_dt.isoformat(), driver_flag, location
            )
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            return

        messagebox.showinfo("Reserved", f"Reservation created (ID {res_id}). Total estimated cost: {total_cost:.2f}")

        self.app_controller.refresh_reservation_list()
        self.app_controller.refresh_calendar_marks()
        self.app_controller.refresh_return_dropdown()
        self.update_reservation_dropdown()
        
        if "Reports" in self.app_controller.tab_instances:
            self.app_controller.tab_instances["Reports"].refresh_report()
        
        self.cust_name.delete(0, "end")
        self.cust_phone.delete(0, "end")
        self.cust_email.delete(0, "end")
        self.location_entry.delete(0, "end")
        self.driver_license_entry.delete(0, "end")
        
    def handle_update_reservation(self):
        res_id = self.get_selected_update_rid()
        if res_id is None:
            return

        try:
            new_end_dt = self.parse_datetime_inputs(self.update_return_date, self.update_return_time)
        except Exception as e:
            messagebox.showerror("Invalid datetime", f"New return datetime: {str(e)}")
            return
            
        try:
            new_total_cost = self.system.update_reservation_return(res_id, new_end_dt.isoformat())
            messagebox.showinfo("Updated", 
                                f"Reservation {res_id} updated. New return datetime: {new_end_dt.strftime('%Y-%m-%d %H:%M')}. "
                                f"New estimated total cost: {new_total_cost:.2f}")
            
            self.app_controller.refresh_reservation_list()
            self.app_controller.refresh_calendar_marks()
            self.update_reservation_dropdown()
            if "Reports" in self.app_controller.tab_instances:
                self.app_controller.tab_instances["Reports"].refresh_report()
            
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")