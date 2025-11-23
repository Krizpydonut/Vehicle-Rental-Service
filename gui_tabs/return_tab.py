import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import db

class ReturnTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Process Return & Damage Contract", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        frame = ctk.CTkFrame(self)
        frame.pack(padx=10, pady=8, fill="both", expand=True)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", pady=6)
        ctk.CTkLabel(top, text="Reservation ID to return:").pack(side="left", padx=6)
        self.return_res_id = ctk.CTkEntry(top, width=100, placeholder_text="Reservation ID")
        self.return_res_id.pack(side="left", padx=6)
        ctk.CTkButton(top, text="Load", command=self.load_reservation_for_return).pack(side="left", padx=6)

        self.return_info = ctk.CTkTextbox(frame, height=140)
        self.return_info.pack(fill="x", pady=6)

        #Damage form
        dmg_frame = ctk.CTkFrame(frame)
        dmg_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(dmg_frame, text="Condition of the vehicle (will be charged to customer)").grid(row=0, column=0, columnspan=2, pady=(4,6))
        ctk.CTkLabel(dmg_frame, text="Condition:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.condition = ctk.CTkEntry(dmg_frame)
        self.condition.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(dmg_frame, text="Cost:").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        self.dmg_cost = ctk.CTkEntry(dmg_frame)
        self.dmg_cost.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(dmg_frame, text="Notes:").grid(row=3, column=0, sticky="ne", padx=4, pady=4)
        self.dmg_notes = ctk.CTkTextbox(dmg_frame, height=4)
        self.dmg_notes.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
        dmg_frame.grid_columnconfigure(1, weight=1)

        btns = ctk.CTkFrame(frame)
        btns.pack(pady=6)
        ctk.CTkButton(btns, text="Add Damage Entry", command=self.handle_add_damage).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Finalize Return (Mark returned)", command=self.handle_finalize_return).pack(side="left", padx=6)

        self.damage_list_box = ctk.CTkTextbox(frame, height=10, font=("Courier New", 12))
        self.damage_list_box.pack(fill="both", pady=6, expand=True)
    
    def refresh(self):
        # Clears the form when returning to the tab
        self.return_res_id.delete(0, "end")
        self.return_info.configure(state="normal")
        self.return_info.delete("1.0", "end")
        self.return_info.insert("end", "Enter a Reservation ID and click Load to begin return process.")
        self.return_info.configure(state="disabled")
        self.damage_list_box.configure(state="normal")
        self.damage_list_box.delete("1.0", "end")
        self.damage_list_box.insert("end", "Damage Contract Details will appear here.")
        self.damage_list_box.configure(state="disabled")

    def load_reservation_for_return(self):
        rid_text = self.return_res_id.get().strip()
        if not rid_text:
            messagebox.showwarning("Missing", "Enter Reservation ID.")
            return
        try:
            rid = int(rid_text)
        except:
            messagebox.showerror("Invalid", "Reservation ID must be numeric.")
            return
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        SELECT r.ReservationID, v.plate, v.model, r.customer_name, r.start_datetime, r.end_datetime, r.driver_flag, r.driver_license, r.total_cost, r.status
        FROM Reservation r JOIN Vehicle v ON r.vehicle_id = v.VehicleID
        WHERE r.ReservationID=?
        """, (rid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            messagebox.showerror("Not found", "Reservation not found.")
            return
        rid, plate, model, name, s,e, driver_flag, driver_license, total_cost, status = row
        
        if status != 'active':
            messagebox.showwarning("Status", f"Reservation ID {rid} is already marked as '{status}'.")
            return

        info = f"ResID: {rid}\nPlate: {plate}\nModel: {model}\nCustomer: {name}\nFrom: {s}\nTo: {e}\nDriver provided: {'Yes' if driver_flag else 'No'}\nDriver license on file: {driver_license}\nEstimated Total (before damages): {total_cost:.2f}\n"
        self.return_info.configure(state="normal")
        self.return_info.delete("1.0", "end")
        self.return_info.insert("end", info)
        self.return_info.configure(state="disabled")
        self.refresh_damage_list(rid)

    def refresh_damage_list(self, reservation_id):
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT condition, damage_cost, notes, created_at FROM DamageContract WHERE reservation_id=?", (reservation_id,))
        rows = cur.fetchall()
        conn.close()
        self.damage_list_box.configure(state="normal")
        self.damage_list_box.delete("1.0", "end")
        if not rows:
            self.damage_list_box.insert("end", "No damage entries yet for this reservation.\n")
        else:
            total = 0.0
            for condition, cost, notes, created_at in rows:
                self.damage_list_box.insert("end", f"{created_at} | Condition: {condition} | Cost: {cost:.2f}\n  Notes: {notes}\n\n")
                total += float(cost)
            self.damage_list_box.insert("end", f"\nTotal damage charges: {total:.2f}\n")
        self.damage_list_box.configure(state="disabled")

    def handle_add_damage(self):
        rid_text = self.return_res_id.get().strip()
        if not rid_text:
            messagebox.showwarning("Missing", "Enter Reservation ID first.")
            return
        try:
            rid = int(rid_text)
        except:
            messagebox.showerror("Invalid", "Reservation ID must be numeric.")
            return
        condition = self.condition.get().strip()
        cost_text = self.dmg_cost.get().strip()
        notes = self.dmg_notes.get("1.0", "end").strip()
        if not condition or not cost_text:
            messagebox.showwarning("Missing", "Enter condition and cost.")
            return
        try:
            cost = float(cost_text)
        except:
            messagebox.showerror("Invalid", "Cost must be numeric.")
            return
        db.add_damage(rid, condition, cost, notes)
        messagebox.showinfo("Added", "Damage entry added.")
        self.condition.delete(0, "end")
        self.dmg_cost.delete(0, "end")
        self.dmg_notes.delete("1.0", "end")
        self.refresh_damage_list(rid)

    def handle_finalize_return(self):
        rid_text = self.return_res_id.get().strip()
        if not rid_text:
            messagebox.showwarning("Missing", "Enter Reservation ID first.")
            return
        try:
            rid = int(rid_text)
        except:
            messagebox.showerror("Invalid", "Reservation ID must be numeric.")
            return
            
        # show damage total
        conn = sqlite3.connect(db.DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT SUM(damage_cost) FROM DamageContract WHERE reservation_id=?", (rid,))
        dmg_total = cur.fetchone()[0] or 0.0
        cur.execute("SELECT total_cost, status FROM Reservation WHERE ReservationID=?", (rid,))
        res_data = cur.fetchone()
        conn.close()
        
        if not res_data:
            messagebox.showerror("Error", "Reservation not found in DB.")
            return
            
        base, status = res_data
        
        if status != 'active':
            messagebox.showwarning("Status", f"Reservation ID {rid} is already marked as '{status}'.")
            return

        final = base + dmg_total
        if messagebox.askyesno("Finalize Return", f"Base total: {base:.2f}\nDamage total: {dmg_total:.2f}\nFinal amount due from customer: {final:.2f}\n\nMark reservation as returned?"):
            db.finalize_reservation(rid)
            messagebox.showinfo("Returned", "Reservation marked returned.")
            self.controller.refresh_all_tabs()
            
            # UI Cleanup
            self.return_info.configure(state="normal")
            self.return_info.delete("1.0", "end")
            self.return_info.insert("end", "Reservation finalized and marked returned.")
            self.return_info.configure(state="disabled")
            self.damage_list_box.configure(state="normal")
            self.damage_list_box.delete("1.0", "end")
            self.damage_list_box.insert("end", "No damage entries (reservation closed).")
            self.damage_list_box.configure(state="disabled")