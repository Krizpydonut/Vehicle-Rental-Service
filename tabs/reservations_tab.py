import customtkinter as ctk
from datetime import datetime
from .base_tab import BaseTab

class ReservationsTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.reservation_data = []
        self.sort_column = 'start_datetime'
        self.sort_reverse = False
        self.build_ui()
        self.refresh_list()

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Active Reservations", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(pady=8)
        
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(5, 0))
        ctk.CTkLabel(btn_frame, text="Current Active Rentals:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Refresh List", command=self.refresh_list).pack(side="right", padx=10)

        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=1, column=0, sticky="ew")
        
        headers = [
            ("ResID", 'ReservationID'), 
            ("Plate", 'plate'), 
            ("Customer", 'customer_name'), 
            ("From Date", 'start_datetime'), 
            ("To Date", 'end_datetime'),
            ("Location", 'location')
        ]
        
        weights = [1, 2, 3, 3, 3, 2] 
        
        for i, (text, key) in enumerate(headers):
            btn = ctk.CTkButton(header_frame, text=text, fg_color="gray", hover_color="#555555",
                                command=lambda k=key: self.sort_and_display(k))
            btn.grid(row=0, column=i, sticky="ew", padx=(2 if i > 0 else 0, 2), pady=2)
            header_frame.grid_columnconfigure(i, weight=weights[i])

        self.scrollable_data_frame = ctk.CTkScrollableFrame(frame)
        self.scrollable_data_frame.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        
        for i, w in enumerate(weights):
            self.scrollable_data_frame.grid_columnconfigure(i, weight=w)

    def sort_and_display(self, column_key):
        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            if column_key in ('start_datetime', 'end_datetime', 'ReservationID'):
                self.sort_reverse = False
            else:
                self.sort_reverse = True

        if self.reservation_data:
            if column_key in ('start_datetime', 'end_datetime'):
                try:
                    key_func = lambda x: datetime.fromisoformat(x.get(column_key, '1970-01-01T00:00:00'))
                except:
                    key_func = lambda x: x.get(column_key, '')
            elif column_key == 'ReservationID':
                key_func = lambda x: int(x.get(column_key, 0))
            else:
                key_func = lambda x: x.get(column_key, '')
                
            self.reservation_data.sort(key=key_func, reverse=self.sort_reverse)
        self._display_reservation_list()

    def _display_reservation_list(self):
        """Renders the sorted data into the CTkScrollableFrame."""
        
        # Clear existing rows
        for widget in self.scrollable_data_frame.winfo_children():
            widget.destroy()

        if not self.reservation_data:
            ctk.CTkLabel(self.scrollable_data_frame, text="No active reservations found.").grid(row=0, column=0, columnspan=6, pady=10)
            return

        for i, row in enumerate(self.reservation_data):
            # Alternate background colors for readability
            bg_color = ("#333333" if i % 2 == 0 else "#444444") if ctk.get_appearance_mode() == "Dark" else ("#DDDDDD" if i % 2 == 0 else "#EEEEEE")
            start_date_fmt = row['start_datetime'][:16].replace("T", " ")
            end_date_fmt = row['end_datetime'][:16].replace("T", " ")
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['ReservationID']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=0, sticky="ew", padx=(2, 0), pady=1)
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['plate']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=1, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['customer_name']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=2, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.scrollable_data_frame, text=start_date_fmt, 
                         anchor="w", fg_color=bg_color).grid(row=i, column=3, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.scrollable_data_frame, text=end_date_fmt, 
                         anchor="w", fg_color=bg_color).grid(row=i, column=4, sticky="ew", padx=2, pady=1)
            ctk.CTkLabel(self.scrollable_data_frame, text=f"{row['location']}", 
                         anchor="w", fg_color=bg_color).grid(row=i, column=5, sticky="ew", padx=(2, 4), pady=1)

    def refresh_list(self):
        self.reservation_data = self.system.get_active_reservations()
        self.sort_and_display(self.sort_column)