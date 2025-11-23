import customtkinter as ctk
import db

class ReservationsTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.refresh_reservation_list()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Active Reservations", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.reservations_box = ctk.CTkTextbox(frame, height=450, font=("Courier New", 12))
        self.reservations_box.pack(fill="both", expand=True, padx=6, pady=6)
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=6)
        ctk.CTkButton(btn_frame, text="Refresh", command=self.refresh_reservation_list).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Mark Returned (use Return tab)", command=self.refresh_reservation_list).pack(side="left", padx=6)

    def refresh_reservation_list(self):
        rows = db.list_active_reservations()
        self.reservations_box.configure(state="normal")
        self.reservations_box.delete("1.0", "end")
        self.reservations_box.insert("end", f"{'ResID':<6} {'PLATE':<10} {'MODEL':<18} {'CUSTOMER':<20} {'FROM':<19} {'TO':<19} {'STATUS':<8}\n")
        self.reservations_box.insert("end", "-"*110 + "\n")
        for rid, plate, model, cname, s,e,status in rows:
            self.reservations_box.insert("end", f"{rid:<6} {plate:<10} {model:<18} {cname:<20} {s:<19} {e:<19} {status:<8}\n")
        self.reservations_box.configure(state="disabled")