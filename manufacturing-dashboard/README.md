# Manufacturing Dashboard (Flask + SQLite)

## Features
- Standard/Admin users per UML class diagram
- Login, logout, create account
- Standard user: view account info, view current/previous orders, order parts (create orders)
- Admin user: sort orders, update/modify orders, manage parts (CRUD)
- Orders linked to Parts and Accounts per ER diagram
- SQLite database, simple session-based auth, password hashing

## Quick start
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
