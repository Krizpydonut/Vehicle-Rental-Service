import customtkinter as ctk
from tkinter import messagebox

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login - Vehicle Rental Service")
        self.geometry("400x250")
        self.resizable(False, False)
        
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

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing", "Enter both username and password.")
            return
        if username == self.correct_username and password == self.correct_password:
            self.login_successful = True
            self.destroy()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.")