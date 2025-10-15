from flask import Flask, render_template, request, redirect, url_for,flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user,login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from data import india_data
import pymysql
import os

localserver = True
app = Flask(__name__)

app.secret_key = "supersecretkey"



DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # 1. Use the URL from the environment (e.g., in production/Render)
    # 2. Fix the scheme for PyMySQL if the URL starts with 'mysql://'
    if DATABASE_URL.startswith("mysql://"):
        DB_URI = DATABASE_URL.replace("mysql://", "mysql+pymysql://")
    else:
        DB_URI = DATABASE_URL
        
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    localserver = False
    print("Using Production Database URI.")
else:
    # Fallback to the local setup for development
    # Note: Using the simple format prevents the SQLAlchemy ValueError
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:hKWcMhrDMbrGjtBMBLVAeZFAAitgEATS@caboose.proxy.rlwy.net:45189/railway"

    print("Using Local Database URI (Development Mode).")

# --------------------------------------------------------------------------

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
# Set the view function name that handles logins (Flask-Login needs to know where to redirect)
login_manager.login_view = 'login'
# Optional: Set the message category for the flash message when a user is redirected
login_manager.login_message_category = 'info'

# User Loader function: This is mandatory for Flask-Login.
# It tells Flask-Login how to retrieve a Users object from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    # 'user_id' is passed as a string by Flask-Login, so we convert it to int.
    return Users.query.get(int(user_id))
    


class Users(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    usertype = db.Column(db.String(50), nullable=False)
    email= db.Column(db.String(100), nullable=True)
class Facility(db.Model):
    fid=db.Column(db.Integer, primary_key=True)
    states=db.Column(db.String(100), nullable=False)
    district=db.Column(db.String(100), nullable=False)
    sdistrict=db.Column(db.String(100), nullable=False)
    fname=db.Column(db.String(100), nullable=False)
    ftype=db.Column(db.String(100), nullable=False)
    programme=db.Column(db.String(100), nullable=False)
    beneficiaries=db.Column(db.Integer, nullable=False)
    amt_allotted=db.Column(db.Float, nullable=False)
    month=db.Column(db.String(20), nullable=False)
    year=db.Column(db.Integer, nullable=False)


@app.route("/")
def home():
    return render_template("home.html", page="home")

#SIIGN UP PAGE
@app.route("/signup",methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        usertype = request.form.get("usertype")
        email = request.form.get("email")
        print(username, password, usertype)
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
            return render_template("signup.html", error="Username already exists. Please choose a different one.")
        else:
            # 1. Acquire a connection from the engine
            with db.engine.connect() as connection:
                # 2. Start a transaction (optional but recommended for INSERT)
                with connection.begin():
                    # 3. Execute the raw SQL using the connection object's execute method
                    #    It is also highly recommended to use text() and PARAMETER BINDING
                    #    instead of f-strings to prevent SQL Injection attacks.
                    encpassword=generate_password_hash(password)
                    password=encpassword
                    sql_query = text(
                        "INSERT INTO users(username, password, usertype, email) "
                        "VALUES (:username, :password, :usertype, :email)"
                    )
                    
                    connection.execute(
                        sql_query,
                        {"username": username, "password": password, "usertype": usertype, "email": email}
                    )
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login"))

    # GET request → Show signup page
    return render_template("signup.html")
# --------------------------
# LOGIN PAGE (Home Route)
# --------------------------
@app.route("/login",methods=["GET", "POST"])

def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        usertype = request.form.get("usertype")
        email = request.form.get("email")
        print(username, password, usertype)
        users = Users.query.filter_by(username=username, usertype=usertype, email=email).first()

        if users and check_password_hash(users.password, password):
            login_user(users)
            flash("Login successful!", "success")
            if users.usertype == "SUPER ADMIN":

                return redirect(url_for("admin"))
            elif users.usertype == "FACILITY DATA ENTRY OPERATOR":
                
                return redirect(url_for("index"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("login.html", error="Invalid credentials. Please try again.")

    # GET request → Show login page
    return render_template("login.html")




    
# --------------------------
# ADMIN DASHBOARD
# --------------------------
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.usertype != "SUPER ADMIN":
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for("login"))
    
    selected_state = None
    selected_district = None
    selected_subdistrict = None
    district_list = []
    subdistrict_list = []

    if request.method == "POST":
        selected_state = request.form.get("state")
        selected_district = request.form.get("district")
        selected_subdistrict = request.form.get("subdistrict")

        # Populate district dropdown
        if selected_state:
            district_list = list(india_data.get(selected_state, {}).keys())

        # Populate subdistrict dropdown
        if selected_state and selected_district:
            subdistrict_list = india_data[selected_state].get(selected_district, [])

    return render_template(
        "admin.html",
        states=india_data.keys(),
        districts=district_list,
        subdistricts=subdistrict_list,
        selected_state=selected_state,
        selected_district=selected_district,
        selected_subdistrict=selected_subdistrict,
    )
    
    



# --------------------------
# DATA ENTRY PAGE
# --------------------------
@app.route("/data_entry", methods=["GET", "POST"])
@login_required
def index():
    # Variables for dropdowns (using names that will be passed to template)
    selected_state = None
    selected_district = None
    selected_subdistrict = None
    
    # Lists to populate the dropdowns
    district_list = []
    subdistrict_list = []

    # --- Database Insertion Logic ---
    if request.method == "POST":
        # Check if the submission is a filter change (has 'action' = 'filter')
        # or a final data entry (has 'fname' field, for example)
        
        # 1. Capture the selected values from the form.
        selected_state = request.form.get("states")      # Matches name="states" in HTML
        selected_district = request.form.get("district") # Matches name="district" in HTML
        selected_subdistrict = request.form.get("sdistrict") # Matches name="sdistrict" in HTML

        # 2. Logic to populate the dependent dropdowns (for the re-render)
        if selected_state:
            district_list = list(india_data.get(selected_state, {}).keys())
        
        if selected_state and selected_district:
            subdistrict_list = india_data.get(selected_state, {}).get(selected_district, [])


        # 3. Database INSERT Logic (Only run if this is a final data submission)
        # We check for a field that only exists on the final entry form (e.g., fname)
        if request.form.get("action") == "record_submit": 
            states = selected_state # Use the variable already retrieved
            district = selected_district
            sdistrict = selected_subdistrict
            fname = request.form.get("fname")
            ftype = request.form.get("ftype")
            programme = request.form.get("programme")
            beneficiaries = request.form.get("beneficiaries")
            amt_allotted = request.form.get("amt_allotted")
            month = request.form.get("month")
            year = request.form.get("year")
            # --- FIX THE INTEGER/NUMERIC FIELDS HERE ---
        
            # Helper to safely convert to integer, using None if the string is empty
            def safe_int(value):
                # request.form.get returns a string or None. If it's an empty string, convert to None.
                if value is None or value.strip() == '':
                    return None
                try:
                    return int(value)
                except ValueError:
                    # Handle case where it's non-empty but non-numeric (e.g., "abc")
                    return None 

            # Re-assign the numerical fields using the safe_int function
            beneficiaries = safe_int(request.form.get("beneficiaries"))
            amt_allotted = safe_int(request.form.get("amt_allotted"))
            year = safe_int(request.form.get("year")) # Assuming 'year' is also an integer column
            
            month = request.form.get("month") # This is likely a string (e.g., "January")
            
        # --- End of FIX ---
        # Acquire a connection and execute INSERT
        # ... (Your existing database insertion code) ...
            with db.engine.connect() as connection:
                with connection.begin():
                    # Your SQL insert using text() and parameter binding
                    sql_query = text(
                        "INSERT INTO facility(states, district, sdistrict, fname, ftype, programme, beneficiaries, amt_allotted, month, year) "
                        "VALUES (:states, :district, :sdistrict, :fname, :ftype, :programme, :beneficiaries, :amt_allotted, :month, :year)"
                    )
                    connection.execute(
                        sql_query,
                        {
                            "states": states, "district": district, "sdistrict": sdistrict, 
                            "fname": fname, "ftype": ftype, "programme": programme, 
                            "beneficiaries": beneficiaries, "amt_allotted": amt_allotted, 
                            "month": month, "year": year
                        }
                    )
            flash("Data submitted successfully!", "success")
            # Optionally reset selections after successful insertion
            selected_state = selected_district = selected_subdistrict = None
            district_list = subdistrict_list = []


    # --- Template Rendering ---
    return render_template(
        "index.html", 
        page="entry",
        states=india_data.keys(),
        districts=district_list,
        subdistricts=subdistrict_list,
        selected_state=selected_state,
        selected_district=selected_district,
        selected_subdistrict=selected_subdistrict,
    )
@app.route("/show_records",methods=["GET"])
@login_required
def show_records():
    em=current_user.email
    with db.engine.connect() as connection:
        with connection.begin():
            sql_query = text("SELECT * FROM facility ORDER BY states ASC")
            query = connection.execute(sql_query)
            return render_template("index.html", page="entry", query=query)
        
@app.route("/show_admin_records", methods=["GET"])
@login_required
def show_admin_records():
    
    
  # Helper function to correctly map empty string from HTML to 'All' for SQL
    def get_filter_value(param_name):
        # Get the value, or 'All' if parameter is missing
        value = request.args.get(param_name, 'All')
        # If the value is an empty string (from <option value="">), treat it as 'All'
        return 'All' if value == '' else value

    # 2. Get and clean filter values
    state_filter = get_filter_value('states')
    district_filter = get_filter_value('district')
    sdistrict_filter = get_filter_value('sdistrict')
    ftype_filter = get_filter_value('ftype')
    programme_filter = get_filter_value('programme')
    month_filter = get_filter_value('month')
    year_filter = get_filter_value('year')
    
    print(state_filter, district_filter, sdistrict_filter, ftype_filter, programme_filter, month_filter, year_filter)

    # 3. Construct the dynamic SQL query for the detailed records table
    #    The filter logic is: (column = :value OR :value = 'All')
    #    The user email filter is mandatory for security.
    sql_query_text = """
        SELECT
            states,
            district,
            sdistrict,
            ftype,
            programme,
            beneficiaries ,
            amt_allotted ,
            month,
            year
        FROM
            facility
        WHERE
           
            
            
            (states = :state_filter OR :state_filter = 'All') AND
            (district = :district_filter OR :district_filter = 'All') AND
            (sdistrict = :sdistrict_filter OR :sdistrict_filter = 'All') AND
            (ftype = :ftype_filter OR :ftype_filter = 'All') AND
            (programme = :programme_filter OR :programme_filter = 'All') AND
            (month = :month_filter OR :month_filter = 'All') AND
            (year = :year_filter OR :year_filter = 'All')
        
    """
    
    # Define the parameters to pass to the query
    params = {
        'state_filter': state_filter,
        'district_filter': district_filter,
        'sdistrict_filter': sdistrict_filter,
        'ftype_filter': ftype_filter,
        'programme_filter': programme_filter,
        'month_filter': month_filter,
        'year_filter': year_filter
    }

    with db.engine.connect() as connection:
        with connection.begin():
            sql_query = text(sql_query_text)
            # Execute the query with the parameters
            query = connection.execute(sql_query, params)
            
            # Note: You would typically run a separate aggregate query here for the top four boxes
            # But for simplicity, we'll just return the detailed query for now.
            
            return render_template(
                "admin.html", 
                page="admin", 
                query=query
            )
    
# --------------------------
# MAIN DRIVER
# --------------------------
if __name__ == "__main__":
    with app.app_context():
        # ENSURE ALL TABLES ARE CREATED IN YOUR DATABASE
        db.create_all()
    app.run(debug=True,port=8000)
