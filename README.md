🚗 Vehicle Rental Service Management System

This is a desktop application built using Python and CustomTkinter (CTK) for managing a small-scale vehicle rental business. It handles vehicle registration, customer reservations, tracking maintenance, processing returns (including damages), and generating usage reports.

✨ Features

The application is structured into several functional tabs for easy management:

Login Interface: Secure access with a hardcoded admin credential (admin/admin123).

Vehicles: Register new vehicles and view/sort the complete fleet list in a table format.

Rent Vehicle: Create new reservations, filter available vehicles by type, brand, year, and model, and update return dates for existing reservations.

Calendar: Visualize active bookings on a calendar and view reservation details for a specific date.

Active Reservations: View and sort a clear list of all ongoing rentals, including customer names and vehicle pickup locations.

Return / Damage: Process vehicle returns, record the distance traveled, finalize costs, and log damage contracts.

Maintenance: Send vehicles for service, track active maintenance tasks in a sortable table, and mark vehicles as available upon completion.

Reports: Generate detailed usage reports, including vehicle mileage/time tracking and location popularity, all displayed in sortable tables.

💻 Setup and Installation

Prerequisites

You must have Python installed on your system.

Install Required Libraries:
The application relies on customtkinter (for the GUI) and tkcalendar (for the date picker widget).

pip install customtkinter
pip install tkcalendar



Running the Application

Clone the repository (if hosted on GitHub) or ensure all files are in the same directory structure as shown above.

Run the main script:

python main.py



Login: Use the default admin credentials:

Username: admin

Password: admin123

📊 Core Data Flow Overview

The system uses a 3-tier structure to separate the UI from data access:

Layer

File(s)

Role

Presentation (GUI)

main_gui.py, tabs/*.py, login_ui.py

Displays the UI, captures user input, and triggers actions.

Business Logic

rental_system.py

Enforces business rules (e.g., check availability, calculate costs) and translates GUI requests into database commands.

Data Persistence

db.py

Handles all interactions with the SQLite database (rental.db), managing connections, tables, and CRUD operations.

🤝 Contribution

If you find any bugs or have suggestions for improvements (e.g., moving to a more secure database, enhancing reports), feel free to open an issue or submit a pull request!
