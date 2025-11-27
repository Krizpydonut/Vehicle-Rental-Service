import customtkinter as ctk
from tkinter import messagebox
from rental_system import Documentation
from .base_tab import BaseTab # Import BaseTab

class ReturnTab(BaseTab):
    def __init__(self, master, app_controller):
        super().__init__(master, app_controller)
        self._reservation_map = {}
        self.build_ui()
        self.update_reservation_dropdown()
        self.return_info.configure(state="normal")
        self.return_info.insert("end", "Select a reservation from the dropdown and click 'Load'.")
        self.return_info.configure(state="disabled")
        
    def validate_distance(self, P):
        """Callback to validate if input P is a positive float or empty string."""
        if P == "": 
            return True
        try:
            return float(P) >= 0.0
        except ValueError:
            return False

    def build_ui(self):
        tab = self
        header = ctk.CTkLabel(tab, text="Process Return & Damage Contract", font=ctk.CTkFont(size=18))
        header.pack(pady=8)
        frame = ctk.CTkFrame(tab)
        frame.pack(padx=10, pady=8, fill="both", expand=True)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", pady=6)
        
        ctk.CTkLabel(top, text="Reservation to return:").pack(side="left", padx=6)
        self.return_res_var = ctk.StringVar()
        self.return_res_dropdown = ctk.CTkOptionMenu(top, variable=self.return_res_var, values=[], width=300)
        self.return_res_dropdown.pack(side="left", padx=6)
        
        ctk.CTkButton(top, text="Load", command=self.load_reservation_for_return).pack(side="left", padx=6)

        self.return_info = ctk.CTkTextbox(frame, height=140)
        self.return_info.pack(fill="x", pady=6)
        
        distance_frame = ctk.CTkFrame(frame)
        distance_frame.pack(fill="x", pady=6)
        distance_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(distance_frame, text="Distance Traveled (km):").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        vcmd = (self.register(self.validate_distance), '%P')
        self.distance_km_entry = ctk.CTkEntry(distance_frame, placeholder_text="e.g. 150.5 km", validate="key", validatecommand=vcmd)
        self.distance_km_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        dmg_frame = ctk.CTkFrame(frame)
        dmg_frame.pack(fill="x", pady=6)
        dmg_frame.grid_columnconfigure(1, weight=1)
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

        btns = ctk.CTkFrame(frame)
        btns.pack(pady=6)
        ctk.CTkButton(btns, text="Add Damage Entry", command=self.handle_add_damage).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Finalize Return (Mark returned)", command=self.handle_finalize_return).pack(side="left", padx=6)

        self.damage_list_box = ctk.CTkTextbox(frame, height=10, font=("Courier New", 12))
        self.damage_list_box.pack(fill="both", pady=6, expand=True)
        
    def update_reservation_dropdown(self):
        reservations_full = self.system.get_active_reservations_dropdown_fmt()
        
        reservations_display = []
        self._reservation_map = {}
        
        for item in reservations_full:
            parts = item.split(" - ", 1) 
            if len(parts) > 1:
                display_text = parts[1]
                reservations_display.append(display_text)
                self._reservation_map[display_text] = item
            else:
                reservations_display.append(item) 
                self._reservation_map[item] = item
                
        self.return_res_dropdown.configure(values=reservations_display)
        
        if reservations_display:
            self.return_res_var.set(reservations_display[0])
        else:
            self.return_res_var.set("No active reservations")
            self.return_res_dropdown.configure(values=["No active reservations"])
            

    def get_selected_rid(self):
        selected_display_text = self.return_res_var.get()
        
        if not selected_display_text or "No active reservations" in selected_display_text:
            messagebox.showwarning("Missing", "Select an active reservation.")
            return None
        
        full_value = self._reservation_map.get(selected_display_text)
        
        if not full_value:
            messagebox.showerror("Invalid", "Could not find reservation details.")
            return None
            
        try:
            return int(full_value.split(" - ")[0])
        except Exception:
            messagebox.showerror("Invalid", "Selected reservation format is invalid.")
            return None


    def load_reservation_for_return(self):
        rid = self.get_selected_rid()
        if rid is None:
            return
            
        row = self.system.get_reservation_details(rid)

        if not row:
            messagebox.showerror("Not found", "Reservation not found.")
            return
        
        info = f"ResID: {row['ReservationID']}\nPlate: {row['plate']}\nModel: {row['model']}\nCustomer: {row['customer_name']}\nFrom: {row['start_datetime']}\nTo: {row['end_datetime']}\nDriver provided: {'Yes' if row['driver_flag'] else 'No'}\nDriver license on file: {row['driver_license']}\nEstimated Total (before damages): {row['total_cost']:.2f}\n"
        self.return_info.configure(state="normal")
        self.return_info.delete("1.0", "end")
        self.return_info.insert("end", info)
        self.return_info.configure(state="disabled")
        self.refresh_damage_list(rid)
        
        self.distance_km_entry.delete(0, "end")


    def refresh_damage_list(self, reservation_id):
        rows = self.system.get_damage_contracts(reservation_id)
        
        self.damage_list_box.configure(state="normal")
        self.damage_list_box.delete("1.0", "end")
        if not rows:
            self.damage_list_box.insert("end", "No damage entries yet for this reservation.\n")
        else:
            total = 0.0
            for row in rows:
                self.damage_list_box.insert("end", f"{row['created_at']} | Condition: {row['condition']} | Cost: {row['damage_cost']:.2f}\n  Notes: {row['notes']}\n\n")
                total += float(row['damage_cost'])
            self.damage_list_box.insert("end", f"\nTotal damage charges: {total:.2f}\n")
        self.damage_list_box.configure(state="disabled")

    def handle_add_damage(self):
        rid = self.get_selected_rid()
        if rid is None:
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
        
        doc = Documentation(rid)
        doc.generateDocument(condition, cost, notes)
        
        messagebox.showinfo("Added", "Damage entry added.")
        self.condition.delete(0, "end")
        self.dmg_cost.delete(0, "end")
        self.dmg_notes.delete("1.0", "end")
        self.refresh_damage_list(rid)

    def handle_finalize_return(self):
        rid = self.get_selected_rid()
        if rid is None:
            return
            
        distance_text = self.distance_km_entry.get().strip()
        if not distance_text:
            messagebox.showwarning("Missing", "Please enter the distance traveled (km).")
            return
        try:
            distance_km = float(distance_text)
            if distance_km < 0:
                 raise ValueError("Distance cannot be negative.")
        except:
            messagebox.showerror("Invalid", "Distance must be a valid non-negative number.")
            return
            
        try:
            base, dmg_total, final = self.system.finalize_return(rid, distance_km)
        except Exception:
            messagebox.showerror("Error", "Reservation not found or invalid.")
            return
        
        if messagebox.askyesno("Finalize Return", f"Base total: {base:.2f}\nDamage total: {dmg_total:.2f}\nFinal amount due from customer: {final:.2f}\nDistance reported: {distance_km:.2f} km\n\nMark reservation as returned?"):
            messagebox.showinfo("Returned", "Reservation marked returned.")
            self.app_controller.refresh_reservation_list()
            self.app_controller.refresh_calendar_marks()
            self.app_controller.refresh_rent_dropdowns()
            self.app_controller.refresh_return_dropdown()
            if "Reports" in self.app_controller.tab_instances:
                self.app_controller.tab_instances["Reports"].refresh_report()

            self.return_info.configure(state="normal")
            self.return_info.delete("1.0", "end")
            self.return_info.insert("end", f"Reservation finalized and marked returned. Distance: {distance_km:.2f} km")
            self.return_info.configure(state="disabled")
            self.damage_list_box.configure(state="normal")
            self.damage_list_box.delete("1.0", "end")
            self.damage_list_box.insert("end", "No damage entries (reservation closed).")
            self.damage_list_box.configure(state="disabled")
            self.distance_km_entry.delete(0, "end")