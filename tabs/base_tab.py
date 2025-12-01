import customtkinter as ctk

class BaseTab(ctk.CTkFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, **kwargs)
        self.app_controller = app_controller 
        self.system = app_controller.system
        self.grid_columnconfigure(0, weight=1)
