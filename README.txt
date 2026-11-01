TELANGANA FARMER SCHEMES — PYTHON FLASK VERSION
================================================

WHAT IS INCLUDED
- Python Flask backend
- SQLAlchemy database models
- MySQL support (PyMySQL) and SQLite quick-start mode
- Secure password hashing with Werkzeug
- Farmer registration, login, logout
- Land-area-based scheme filtering
- Scheme details, document lists and external links
- Complaint submission and farmer complaint history
- 33 scheme records carried over from the supplied prototype
- Existing CSS and SVG illustrations reused

IMPORTANT ACCURACY / SECURITY NOTES
- This is an educational prototype, not an official Telangana government portal.
- Scheme descriptions, eligibility limits and links were carried over from your
  original project and MUST be checked against current official notifications.
- Eligibility in this version is only a preliminary land-area filter. It does not
  confirm legal eligibility; age, crop, income, category, land records and other
  rules may apply.
- Passwords are securely hashed on the server. Keep SECRET_KEY private.
- Forgot-password flow is a demo identity check, NOT OTP verification. Do not use
  it for a public production service. Add verified SMS OTP before deployment.
- Complaints are stored in this app database; they are NOT sent to a government
  department. An authorised department workflow/integration is still required.
- Use HTTPS, CSRF protection, rate limiting, backups and security review before
  putting real farmers' personal data online.

QUICK START ON WINDOWS (EASIEST: SQLITE)
1. Install Python 3.10 or newer from https://www.python.org/downloads/
   During installation, tick "Add Python to PATH".
2. Extract this ZIP to a folder, for example Desktop\Telangana-Farmer-Schemes-Python.
3. Open that folder in VS Code.
4. Open Terminal > New Terminal.
5. Create a virtual environment:
      py -m venv .venv
6. Activate it:
      .venv\Scripts\activate
   If PowerShell blocks activation, run:
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   Then activate again.
7. Install packages:
      python -m pip install --upgrade pip
      pip install -r requirements.txt
8. Copy .env.example to a new file named .env.
   For quick start, leave DATABASE_URL as sqlite:///farmer_schemes.db.
   Change SECRET_KEY to a long random value.
9. Start the website:
      python app.py
10. Open this address in Chrome:
      http://127.0.0.1:5000

FIRST USE
- Click Create an account.
- Enter name, 10-digit Indian mobile number, land area in acres and password.
- Password must be at least 8 characters.
- Login and view Eligible for you / All schemes.
- Open a scheme to see benefits, documents and application links.
- Use Complaint to submit a complaint and view its saved status.

OPTIONAL: USE MYSQL
1. Install MySQL Server and start the MySQL service.
2. Open MySQL Workbench or MySQL command line.
3. Run the contents of database_schema_mysql.sql.
4. Copy .env.example to .env.
5. Change DATABASE_URL in .env to:
   mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/telangana_farmer_schemes?charset=utf8mb4
   Replace YOUR_PASSWORD with your own MySQL password. URL-encode special
   characters in the password if needed.
6. Restart the app with: python app.py
   Flask-SQLAlchemy creates the tables and inserts the 33 scheme records.

STOP THE SERVER
- In the terminal press Ctrl + C.

COMMON ERRORS
- 'py' is not recognized: reinstall Python and tick Add Python to PATH.
- 'No module named flask': activate .venv and run pip install -r requirements.txt.
- MySQL connection error: check MySQL service, database name, username and password.
- Port 5000 busy: change app.run(port=5001) at the bottom of app.py and open
  http://127.0.0.1:5001.

PROJECT FILES
app.py                       Main Flask application and routes
schemes.json                 Scheme data imported from the original prototype
templates/                   HTML templates
static/css/style.css         Existing project stylesheet
static/images/               Existing SVG illustrations
requirements.txt              Python dependencies
.env.example                  Environment configuration example
database_schema_mysql.sql    MySQL database creation script

This project is for learning and demonstration. It is not affiliated with the
Government of Telangana or Government of India.
