import customtkinter as ctk
import db
from login_ui import LoginWindow
from main_gui import RentalApp

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def main():
    db.init_db()
    
    app = RentalApp()
    app.withdraw()
    
    def start_main_app_ui():
        app.deiconify()

    login = LoginWindow(master=app, on_success_callback=start_main_app_ui)
    
    app.mainloop()

if __name__ == "__main__":
    main()