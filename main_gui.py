import customtkinter as ctk
from rental_system import VehicleRentalService
# Import the base class (needed by RentalApp to access its methods if used)
from tabs import VehiclesTab, RentTab, CalendarTab, ReservationsTab, ReturnTab, MaintenanceTab, ReportTab

class RentalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vehicle Rental Service")
        self.geometry("950x750")
        self.system = VehicleRentalService()
        self.tabview = ctk.CTkTabview(self, width=980, height=660)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tab_instances = {}
        self.build_tabs()
        
    def build_tabs(self):
        
        vehicles_tab = self.tabview.add("Vehicles")
        self.tab_instances["Vehicles"] = VehiclesTab(master=vehicles_tab, app_controller=self)
        self.tab_instances["Vehicles"].pack(fill="both", expand=True)

        rent_tab = self.tabview.add("Rent Vehicle")
        self.tab_instances["Rent Vehicle"] = RentTab(master=rent_tab, app_controller=self)
        self.tab_instances["Rent Vehicle"].pack(fill="both", expand=True)
        
        calendar_tab = self.tabview.add("Calendar")
        self.tab_instances["Calendar"] = CalendarTab(master=calendar_tab, app_controller=self)
        self.tab_instances["Calendar"].pack(fill="both", expand=True)

        reservations_tab = self.tabview.add("Active Reservations")
        self.tab_instances["Active Reservations"] = ReservationsTab(master=reservations_tab, app_controller=self)
        self.tab_instances["Active Reservations"].pack(fill="both", expand=True)

        return_tab = self.tabview.add("Return / Damage")
        self.tab_instances["Return / Damage"] = ReturnTab(master=return_tab, app_controller=self)
        self.tab_instances["Return / Damage"].pack(fill="both", expand=True)
        
        maintenance_tab = self.tabview.add("Maintenance")
        self.tab_instances["Maintenance"] = MaintenanceTab(master=maintenance_tab, app_controller=self)
        self.tab_instances["Maintenance"].pack(fill="both", expand=True)
        
        # --- NEW TAB: Reports ---
        reports_tab = self.tabview.add("Reports")
        self.tab_instances["Reports"] = ReportTab(master=reports_tab, app_controller=self)
        self.tab_instances["Reports"].pack(fill="both", expand=True)
        
    
    def refresh_reservation_list(self):
        self.tab_instances["Active Reservations"].refresh_list()
        
    def refresh_calendar_marks(self):
        self.tab_instances["Calendar"].refresh_marks()

    def update_maint_vehicle_dropdown(self):
        self.tab_instances["Maintenance"].update_vehicle_dropdown()
        
    def refresh_rent_dropdowns(self):
        self.tab_instances["Rent Vehicle"].update_type_dropdown()
        
    def refresh_return_dropdown(self):
        self.tab_instances["Return / Damage"].update_reservation_dropdown()