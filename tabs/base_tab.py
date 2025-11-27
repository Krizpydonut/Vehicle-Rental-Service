import customtkinter as ctk
from rental_system import VehicleRentalService, Vehicle, Customer, Documentation, MaintenanceRecord

class BaseTab(ctk.CTkFrame):
    """Base class for all tab frames to inherit common properties."""
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)
        self.app_controller = app_controller 
        self.system = app_controller.system
        self.grid_columnconfigure(0, weight=1)