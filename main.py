import customtkinter as ctk
import db
from login_ui import LoginWindow
from main_gui import RentalApp

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def main():
    db.init_db()
    login = LoginWindow()
    login.mainloop() 
    
    if login.login_successful:
        try:
            login.withdraw() 
            login.destroy()
        except:
            pass
        app = RentalApp()
        app.mainloop()

if __name__ == "__main__":
    main()