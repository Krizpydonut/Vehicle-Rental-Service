import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime, timedelta
from .base_tab import BaseTab # Import BaseTab

class CalendarTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self.build_ui()
        self.refresh_marks()

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Booking Calendar", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        cal_frame = ctk.CTkFrame(tab)
        cal_frame.pack(padx=10, pady=6, fill="both", expand=True)

        left = ctk.CTkFrame(cal_frame)
        left.pack(side="left", padx=6, pady=6, fill="y")
        self.calendar = Calendar(left, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(padx=6, pady=6)
        ctk.CTkButton(left, text="Show Bookings for Date", command=self.show_bookings_for_date).pack(pady=6)
        ctk.CTkButton(left, text="Refresh Calendar", command=self.refresh_marks).pack(pady=6)

        right = ctk.CTkFrame(cal_frame)
        right.pack(side="left", padx=6, pady=6, fill="both", expand=True)
        ctk.CTkLabel(right, text="Bookings on selected date:", anchor="w").pack(padx=6, pady=(8,4))
        self.bookings_text = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.bookings_text.pack(padx=6, pady=4, fill="both", expand=True)

    def refresh_marks(self):
        try:
            self.calendar.calevent_remove('all')
        except:
            pass
            
        rows = self.system.get_active_reservations_dates()

        for row in rows:
            try:
                s, e, rid = row
            except Exception:
                try:
                    s = row['start_datetime']
                    e = row['end_datetime']
                    rid = row['ReservationID']
                except Exception:
                    try:
                        vals = tuple(row)
                        s, e, rid = vals[0], vals[1], vals[2]
                    except Exception:
                        continue

            try:
                sdt = datetime.fromisoformat(s)
                edt = datetime.fromisoformat(e)
            except Exception:
                continue

            day = sdt.date()
            while day <= edt.date():
                try:
                    self.calendar.calevent_create(day, f"Booked #{rid}", 'reserved')
                except Exception:
                    pass
                day = day + timedelta(days=1)

    def show_bookings_for_date(self):
        sel = self.calendar.get_date()
        dt_obj = datetime.fromisoformat(sel)
        start_day = datetime(dt_obj.year, dt_obj.month, dt_obj.day)
        end_day = start_day + timedelta(days=1)
        
        rows = self.system.get_bookings_for_date(start_day.isoformat(), end_day.isoformat())

        self.bookings_text.configure(state="normal")
        self.bookings_text.delete("1.0", "end")
        if not rows:
            self.bookings_text.insert("end", "No bookings on this date.\n")
        else:
            for row in rows:
                self.bookings_text.insert("end", f"#{row['ReservationID']} Plate: {row['plate']} Model: {row['model']}\n  Customer: {row['customer_name']}\n  From {row['start_datetime']} to {row['end_datetime']}\n  Location: {row['location']}\n\n")
        self.bookings_text.configure(state="disabled")