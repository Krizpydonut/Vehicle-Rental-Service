import customtkinter as ctk
from tkinter import messagebox
from .base_tab import BaseTab
from operator import itemgetter 

class ReportTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.report_data = [] # Vehicle Usage Data
        self.location_data = [] # Location Usage Data
        
        # Vehicle Table Sort State
        self.vehicle_sort_column = 'reservation_count' 
        self.vehicle_sort_reverse = True 
        
        # Location Table Sort State
        self.location_sort_column = 'reservation_count' 
        self.location_sort_reverse = True 
        
        self.build_ui()
        self.refresh_report()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Vehicle Usage & Location Report", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=(10,6))

        info_label = ctk.CTkLabel(self, text="Click headers to sort data.", text_color="gray")
        info_label.pack(pady=(0, 5))

        # --- Global Controls (Moved outside main table container) ---
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=(0, 5))
        control_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(control_frame, text="Refresh All Data", command=self.refresh_report).grid(row=0, column=0, sticky="e")
        
        # --- Main Table Container (Side-by-Side Layout) ---
        self.tables_container = ctk.CTkFrame(self)
        self.tables_container.pack(padx=10, pady=0, fill="both", expand=True)
        self.tables_container.grid_columnconfigure(0, weight=1) # Location column
        self.tables_container.grid_columnconfigure(1, weight=2) # Vehicle column (Wider)
        self.tables_container.grid_rowconfigure(0, weight=1)

        # --- LOCATION USAGE TABLE (Left Column, uses grid row 0) ---
        self.location_table_frame = ctk.CTkFrame(self.tables_container)
        self.location_table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.location_table_frame.grid_columnconfigure(0, weight=1)
        self.location_table_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.location_table_frame, text="Location Popularity (By Reservations)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Location Header Frame
        loc_header_frame = ctk.CTkFrame(self.location_table_frame, fg_color="transparent")
        loc_header_frame.grid(row=1, column=0, sticky="ew")
        
        loc_headers = [("Location", 'location'), ("Reservations", 'reservation_count')]
        loc_weights = [3, 1]
        
        for i, (text, key) in enumerate(loc_headers):
            btn = ctk.CTkButton(loc_header_frame, text=text, fg_color="gray", hover_color="#555555",
                                command=lambda k=key: self.sort_and_display_location(k))
            btn.grid(row=0, column=i, sticky="ew", padx=(2 if i > 0 else 0, 2), pady=2)
            loc_header_frame.grid_columnconfigure(i, weight=loc_weights[i])

        # Location Scrollable Frame
        self.loc_scrollable_frame = ctk.CTkScrollableFrame(self.location_table_frame)
        self.loc_scrollable_frame.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        for i, w in enumerate(loc_weights):
            self.loc_scrollable_frame.grid_columnconfigure(i, weight=w)


        # --- VEHICLE USAGE TABLE (Right Column, uses grid row 0) ---
        self.vehicle_table_frame = ctk.CTkFrame(self.tables_container)
        self.vehicle_table_frame.grid(row=0, column=1, sticky="nsew") 
        self.vehicle_table_frame.grid_columnconfigure(0, weight=1)
        self.vehicle_table_frame.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.vehicle_table_frame, text="Vehicle Usage Details:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Vehicle Header Frame
        veh_header_frame = ctk.CTkFrame(self.vehicle_table_frame, fg_color="transparent")
        veh_header_frame.grid(row=1, column=0, sticky="ew")
        
        veh_headers = [
            ("Plate", 'plate'), 
            ("Vehicle Model", 'model'),
            ("Reservations", 'reservation_count'), 
            ("Usage (D:H)", 'usage_hours'), 
            ("Distance (km)", 'total_distance_km')
        ]
        veh_weights = [2, 4, 2, 3, 3]
        
        for i, (text, key) in enumerate(veh_headers):
            btn = ctk.CTkButton(veh_header_frame, text=text, fg_color="gray", hover_color="#555555",
                                command=lambda k=key: self.sort_and_display_vehicle(k))
            btn.grid(row=0, column=i, sticky="ew", padx=(2 if i > 0 else 0, 2), pady=2)
            veh_header_frame.grid_columnconfigure(i, weight=veh_weights[i])

        # Vehicle Scrollable Frame
        self.veh_scrollable_frame = ctk.CTkScrollableFrame(self.vehicle_table_frame)
        self.veh_scrollable_frame.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        for i, w in enumerate(veh_weights):
            self.veh_scrollable_frame.grid_columnconfigure(i, weight=w)

    # --- Sorting and Display Logic for VEHICLES ---

    def sort_and_display_vehicle(self, column_key):
        
        if self.vehicle_sort_column == column_key:
            self.vehicle_sort_reverse = not self.vehicle_sort_reverse
        else:
            self.vehicle_sort_column = column_key
            self.vehicle_sort_reverse = True 
            if column_key not in ('reservation_count', 'usage_hours', 'total_distance_km'):
                self.vehicle_sort_reverse = False

        if self.report_data:
            if column_key in ('reservation_count', 'usage_hours', 'total_distance_km'):
                key_func = lambda x: float(x.get(column_key, 0))
            elif column_key == 'model':
                 key_func = itemgetter('model', 'brand', 'plate')
            else:
                key_func = lambda x: x.get(column_key, '')
                
            self.report_data.sort(key=key_func, reverse=self.vehicle_sort_reverse)
        
        self._display_vehicle_table()

    def _display_vehicle_table(self):
        
        for widget in self.veh_scrollable_frame.winfo_children():
            widget.destroy()

        if not self.report_data:
            ctk.CTkLabel(self.veh_scrollable_frame, text="No vehicle usage data available.").grid(row=0, column=0, columnspan=5, pady=10)
            return

        for i, row in enumerate(self.report_data):
            bg_color = ("#333333" if i % 2 == 0 else "#444444") if ctk.get_appearance_mode() == "Dark" else ("#DDDDDD" if i % 2 == 0 else "#EEEEEE")
            
            full_model = f"{row['brand']} {row['model']}"
            if len(full_model) > 28: full_model = full_model[:25] + "..."

            ctk.CTkLabel(self.veh_scrollable_frame, text=f"{row['plate']}", anchor="w", fg_color=bg_color).grid(row=i, column=0, sticky="ew", padx=(2, 0), pady=1)
            ctk.CTkLabel(self.veh_scrollable_frame, text=full_model, anchor="w", fg_color=bg_color).grid(row=i, column=1, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.veh_scrollable_frame, text=f"{row['reservation_count']}", anchor="center", fg_color=bg_color).grid(row=i, column=2, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.veh_scrollable_frame, text=f"{row['usage_display']}", anchor="center", fg_color=bg_color).grid(row=i, column=3, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.veh_scrollable_frame, text=f"{row['total_distance_km']:.2f}", anchor="e", fg_color=bg_color).grid(row=i, column=4, sticky="ew", padx=(2, 4), pady=1)

    # --- Sorting and Display Logic for LOCATIONS ---

    def sort_and_display_location(self, column_key):
        
        if self.location_sort_column == column_key:
            self.location_sort_reverse = not self.location_sort_reverse
        else:
            self.location_sort_column = column_key
            self.location_sort_reverse = True 

        if self.location_data:
            if column_key == 'reservation_count':
                key_func = lambda x: int(x.get(column_key, 0))
            else:
                key_func = lambda x: x.get(column_key, '')
                
            self.location_data.sort(key=key_func, reverse=self.location_sort_reverse)
        
        self._display_location_table()

    def _display_location_table(self):
        
        for widget in self.loc_scrollable_frame.winfo_children():
            widget.destroy()

        if not self.location_data:
            ctk.CTkLabel(self.loc_scrollable_frame, text="No location data available.").grid(row=0, column=0, columnspan=2, pady=10)
            return

        for i, row in enumerate(self.location_data):
            bg_color = ("#333333" if i % 2 == 0 else "#444444") if ctk.get_appearance_mode() == "Dark" else ("#DDDDDD" if i % 2 == 0 else "#EEEEEE")

            ctk.CTkLabel(self.loc_scrollable_frame, text=f"{row['location']}", anchor="w", fg_color=bg_color).grid(row=i, column=0, sticky="ew", padx=(2, 0), pady=1)
            ctk.CTkLabel(self.loc_scrollable_frame, text=f"{row['reservation_count']}", anchor="e", fg_color=bg_color).grid(row=i, column=1, sticky="ew", padx=(2, 4), pady=1)


    # --- Master Refresh ---

    def refresh_report(self):
        try:
            # 1. Fetch data
            self.report_data = self.system.get_usage_report()
            self.location_data = self.system.get_location_report()
            
            # 2. Sort and Display Tables
            self.sort_and_display_vehicle(self.vehicle_sort_column) 
            self.sort_and_display_location(self.location_sort_column)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load report data: {e}")
            self.report_data = []
            self.location_data = []
            self._display_vehicle_table()
            self._display_location_table()