from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os

localserver = True
app = Flask(__name__)


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


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    usertype = db.Column(db.String(50), nullable=False)

@app.route("/")
def home():
    return render_template("home.html", page="home")


# --------------------------
# LOGIN PAGE (Home Route)
# --------------------------
@app.route("/login",methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        usertype = request.form.get("usertype")
        print(username, password, usertype)
        users = Users.query.filter_by(username=username, password=password, usertype=usertype).first()

        if users:
            if users.usertype == "SUPER ADMIN":
                return redirect(url_for("admin"))
            elif users.usertype == "FACILITY DATA ENTRY OPERATOR":
                return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials. Please try again.")

    # GET request → Show login page
    return render_template("login.html")


# --------------------------
# ADMIN DASHBOARD
# --------------------------
@app.route("/admin")
def admin():
    return render_template("admin.html", page="admin")


# --------------------------
# DATA ENTRY PAGE
# --------------------------
@app.route("/data_entry")
def index():
    return render_template("index.html", page="entry")


# --------------------------
# MAIN DRIVER
# --------------------------
if __name__ == "__main__":
    app.run(debug=True,port=8000)
