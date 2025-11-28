import customtkinter as ctk
from tkinter import messagebox

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success_callback):
        super().__init__(master)
        self.transient(master)
        self.title("Login - Vehicle Rental Service")
        self.geometry("400x250")
        self.resizable(False, False)

        self.grab_set() 
        
        self.on_success_callback = on_success_callback
        self.login_successful = False

        ctk.CTkLabel(self, text="Please login", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10, padx=40, fill="x")
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10, padx=40, fill="x")

        self.username_entry.bind('<Return>', lambda event: self.handle_login())
        self.password_entry.bind('<Return>', lambda event: self.handle_login())
        
        ctk.CTkButton(self, text="Login", command=self.handle_login).pack(pady=20)

        self.correct_username = "admin"
        self.correct_password = "admin123"
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 


    def handle_login(self):
        if self.username_entry.get().strip() == self.correct_username and self.password_entry.get().strip() == self.correct_password:
            self.login_successful = True
            self.grab_release()
            self.destroy()
            self.on_success_callback()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.")
            
    def on_closing(self):
        self.master.destroy()