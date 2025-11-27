import customtkinter as ctk
from tkinter import messagebox
from rental_system import Vehicle
from .base_tab import BaseTab

class VehiclesTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.vehicle_data = [] # Stores fetched data for sorting
        self.sort_column = 'VehicleID' # Default sort column
        self.sort_reverse = False # Default sort to ascending
        self.build_ui()
        self.refresh_vehicle_list()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Vehicles", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,6))

        frame = ctk.CTkFrame(self)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # --- Sortable Table Container (Left Side) ---
        
        table_container = ctk.CTkFrame(frame)
        table_container.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(1, weight=1) 
        
        # Header Frame (Sort buttons)
        header_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        
        headers = [
            ("ID", 'VehicleID'), 
            ("Brand/Model", 'model'), # We'll sort by model/brand
            ("Year", 'year'), 
            ("Plate", 'plate'), 
            ("Type", 'vtype'),
            ("Rate/day", 'daily_rate')
        ]
        
        # Configure weights for the report table columns
        weights = [1, 4, 1, 2, 2, 2] 
        
        for i, (text, key) in enumerate(headers):
            # Sorting on 'model' is sufficient, as brand/plate can be secondary keys
            sort_key = 'model' if key == 'model' else key 
            
            btn = ctk.CTkButton(header_frame, text=text, fg_color="gray", hover_color="#555555",
                                command=lambda k=sort_key: self.sort_and_display(k))
            btn.grid(row=0, column=i, sticky="ew", padx=(2 if i > 0 else 0, 2), pady=2)
            header_frame.grid_columnconfigure(i, weight=weights[i])

        # Scrollable Frame for data rows
        self.scrollable_data_frame = ctk.CTkScrollableFrame(table_container)
        self.scrollable_data_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        # Configure columns inside the scrollable frame to match the header weights
        for i, w in enumerate(weights):
            self.scrollable_data_frame.grid_columnconfigure(i, weight=w)

        # --- Add Vehicle Panel (Right Side) ---

        right = ctk.CTkFrame(frame)
        right.grid(row=0, column=1, padx=10, pady=8, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(right, text="Add / Register Vehicle").pack(pady=(6,4))
        
        self.entry_brand = ctk.CTkEntry(right, placeholder_text="Brand (e.g. Toyota)")
        self.entry_model = ctk.CTkEntry(right, placeholder_text="Model (e.g. Vios)")
        self.entry_year = ctk.CTkEntry(right, placeholder_text="Year (e.g. 2020)")
        self.entry_plate = ctk.CTkEntry(right, placeholder_text="Plate (unique)")
        self.entry_type = ctk.CTkEntry(right, placeholder_text="Type (Sedan/SUV/Van/..)")
        self.entry_rate = ctk.CTkEntry(right, placeholder_text="Daily Rate (number)")
        
        self.entry_brand.pack(padx=10, pady=4, fill="x")
        self.entry_model.pack(padx=10, pady=4, fill="x")
        self.entry_year.pack(padx=10, pady=4, fill="x")
        self.entry_plate.pack(padx=10, pady=4, fill="x")
        self.entry_type.pack(padx=10, pady=4, fill="x")
        self.entry_rate.pack(padx=10, pady=4, fill="x")
        
        ctk.CTkButton(right, text="Add Vehicle", command=self.handle_add_vehicle).pack(pady=10)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0) # Lock the right panel size
    
    def sort_and_display(self, column_key):
        """Sorts the vehicle data based on the clicked header and re-displays."""
        
        # 1. Determine direction
        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False
            
            # Default to descending for rates
            if column_key == 'daily_rate':
                self.sort_reverse = True

        # 2. Sort the data
        if self.vehicle_data:
            # Function to extract the sorting key, handling types
            if column_key in ('VehicleID', 'year'):
                key_func = lambda x: int(x.get(column_key, 0))
            elif column_key == 'daily_rate':
                key_func = lambda x: float(x.get(column_key, 0.0))
            else:
                key_func = lambda x: x.get(column_key, '')
                
            self.vehicle_data.sort(key=key_func, reverse=self.sort_reverse)
        
        # 3. Display the sorted data
        self._display_vehicle_list()
        
    def _display_vehicle_list(self):
        """Renders the sorted data into the CTkScrollableFrame."""
        
        # Clear existing rows
        for widget in self.scrollable_data_frame.winfo_children():
            widget.destroy()

        if not self.vehicle_data:
            ctk.CTkLabel(self.scrollable_data_frame, text="No vehicles registered.").grid(row=0, column=0, columnspan=6, pady=10)
            return

        for i, row in enumerate(self.vehicle_data):
            # Alternate background colors for readability
            bg_color = ("#333333" if i % 2 == 0 else "#444444") if ctk.get_appearance_mode() == "Dark" else ("#DDDDDD" if i % 2 == 0 else "#EEEEEE")
            
            full_model = f"{row['brand']} {row['model']}"
            
            # ID
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['VehicleID']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=0, sticky="ew", padx=(2, 0), pady=1)
            
            # Brand/Model
            ctk.CTkLabel(self.scrollable_data_frame, text=full_model, 
                         anchor="w", fg_color=bg_color).grid(row=i, column=1, sticky="ew", padx=2, pady=1)

            # Year
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['year']}", 
                         anchor="center", fg_color=bg_color).grid(row=i, column=2, sticky="ew", padx=2, pady=1)
            
            # Plate
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['plate']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=3, sticky="ew", padx=2, pady=1)

            # Type
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['vtype']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=4, sticky="ew", padx=2, pady=1)

            # Rate
            ctk.CTkLabel(self.scrollable_data_frame, text=f"₱{row['daily_rate']:.2f}", 
                         anchor="e", fg_color=bg_color).grid(row=i, column=5, sticky="ew", padx=(2, 4), pady=1)


    def handle_add_vehicle(self):
        brand = self.entry_brand.get().strip()
        model = self.entry_model.get().strip()
        year_text = self.entry_year.get().strip()
        plate = self.entry_plate.get().strip()
        vtype = self.entry_type.get().strip()
        rate_text = self.entry_rate.get().strip()
        
        if not (brand and model and year_text and plate and vtype and rate_text):
            messagebox.showwarning("Missing", "Please fill all fields.")
            return
        try:
            rate = float(rate_text)
            year = int(year_text)
        except:
            messagebox.showerror("Invalid", "Daily rate and Year must be numbers.")
            return
        
        new_vehicle = Vehicle(brand, model, year, plate, vtype, rate)

        ok, msg = self.system.add_new_vehicle(new_vehicle)

        if ok:
            messagebox.showinfo("Added", f"Vehicle {plate} added.")
            
            # Clear fields
            self.entry_brand.delete(0, "end")
            self.entry_model.delete(0, "end")
            self.entry_year.delete(0, "end")
            self.entry_plate.delete(0, "end")
            self.entry_type.delete(0, "end")
            self.entry_rate.delete(0, "end")
            
            # Refresh all related components
            self.refresh_vehicle_list()
            self.app_controller.refresh_calendar_marks()
            self.app_controller.refresh_rent_dropdowns()
            self.app_controller.update_maint_vehicle_dropdown()
            
            if "Reports" in self.app_controller.tab_instances:
                self.app_controller.tab_instances["Reports"].refresh_report()

        elif msg == "duplicate":
            messagebox.showerror("Error", "A vehicle with this plate already exists!")
            
    def refresh_vehicle_list(self):
        # 1. Fetch data
        self.vehicle_data = self.system.get_all_vehicles()
        
        # 2. Sort and display (using current sort settings)
        self.sort_and_display(self.sort_column)