import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime, timedelta
import sqlite3
import db

class CalendarTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()
        self.refresh_calendar_marks()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Booking Calendar", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        cal_frame = ctk.CTkFrame(self)
        cal_frame.pack(padx=10, pady=6, fill="both", expand=True)

        left = ctk.CTkFrame(cal_frame)
        left.pack(side="left", padx=6, pady=6, fill="y")
        self.calendar = Calendar(left, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(padx=6, pady=6)
        ctk.CTkButton(left, text="Show Bookings for Date", command=self.show_bookings_for_date).pack(pady=6)
        ctk.CTkButton(left, text="Refresh Calendar", command=self.refresh_calendar_marks).pack(pady=6)

        right = ctk.CTkFrame(cal_frame)
        right.pack(side="left", padx=6, pady=6, fill="both", expand=True)
        ctk.CTkLabel(right, text="Bookings on selected date:", anchor="w").pack(padx=6, pady=(8,4))
        self.bookings_text = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.bookings_text.pack(padx=6, pady=4, fill="both", expand=True)

    def refresh_calendar_marks(self):
        try:
            self.calendar.calevent_remove('all')
        except:
            pass
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT start_datetime, end_datetime, ReservationID FROM Reservation WHERE status='active'")
        rows = cur.fetchall()
        conn.close()
        for s,e,rid in rows:
            sdt = datetime.fromisoformat(s)
            edt = datetime.fromisoformat(e)
            day = sdt.date()
            while day <= edt.date():
                try:
                    self.calendar.calevent_create(day, f"Booked #{rid}", 'reserved')
                except Exception:
                    pass
                day = day + timedelta(days=1)

    def show_bookings_for_date(self):
        sel = self.calendar.get_date()  # yyyy-mm-dd
        dt_obj = datetime.fromisoformat(sel)
        start_day = datetime(dt_obj.year, dt_obj.month, dt_obj.day)
        end_day = start_day + timedelta(days=1)
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.location
        FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
        WHERE r.status='active' AND
             NOT (r.end_datetime <= ? OR r.start_datetime >= ?)
        ORDER BY r.start_datetime
        """, (start_day.isoformat(), end_day.isoformat()))
        rows = cur.fetchall()
        conn.close()
        self.bookings_text.configure(state="normal")
        self.bookings_text.delete("1.0", "end")
        if not rows:
            self.bookings_text.insert("end", "No bookings on this date.\n")
        else:
            for rid, plate, model, name, s,e ,location in rows:
                self.bookings_text.insert("end", f"#{rid} Plate: {plate} Model: {model}\n  Customer: {name}\n  From {s} to {e}\n  Location: {location}\n\n")
        self.bookings_text.configure(state="disabled")