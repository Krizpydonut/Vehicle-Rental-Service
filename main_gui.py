import customtkinter as ctk
from tkinter import messagebox
from gui_tabs.vehicle_tab import VehicleTab
from gui_tabs.rental_tab import RentTab
from gui_tabs.calendar_tab import CalendarTab
from gui_tabs.active_reservation_tab import ReservationsTab
from gui_tabs.return_tab import ReturnTab
from gui_tabs.maintenance_tab import MaintenanceTab

class RentalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vehicle Rental Service")
        self.geometry("1050x850")

        self.tabview = ctk.CTkTabview(self, width=980, height=660)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        # Create Tabs
        t_veh = self.tabview.add("Vehicles")
        t_rent = self.tabview.add("Rent Vehicle")
        t_cal = self.tabview.add("Calendar")
        t_res = self.tabview.add("Active Reservations")
        t_ret = self.tabview.add("Return / Damage")
        t_maint = self.tabview.add("Maintenance")

        # Instantiate Component Classes from separate files
        self.tab_vehicles = VehicleTab(t_veh, controller=self)
        self.tab_rent = RentTab(t_rent, controller=self)
        self.tab_calendar = CalendarTab(t_cal, controller=self)
        self.tab_reservations = ReservationsTab(t_res, controller=self)
        self.tab_return = ReturnTab(t_ret, controller=self)
        self.tab_maintenance = MaintenanceTab(t_maint, controller=self)

        # Pack them
        self.tab_vehicles.pack(fill="both", expand=True)
        self.tab_rent.pack(fill="both", expand=True)
        self.tab_calendar.pack(fill="both", expand=True)
        self.tab_reservations.pack(fill="both", expand=True)
        self.tab_return.pack(fill="both", expand=True)
        self.tab_maintenance.pack(fill="both", expand=True)
        
        # Initial Refresh
        self.refresh_all_tabs()

    def refresh_all_tabs(self):
        # Trigger refresh methods on all tabs
        self.tab_vehicles.refresh_vehicle_list()
        self.tab_rent.refresh()
        self.tab_calendar.refresh_calendar_marks()
        self.tab_reservations.refresh_reservation_list()
        self.tab_return.refresh()
        self.tab_maintenance.refresh_maintenance_list()
        self.tab_maintenance.refresh_vehicle_list()