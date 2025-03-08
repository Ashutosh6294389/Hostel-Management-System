from flask import Blueprint, render_template

index_bp = Blueprint("index", __name__)

@index_bp.route("/")
def home():
    return render_template("basic/index.html", title="Hostel Management System")

@index_bp.route("/about")
def about():
    return render_template("basic/about.html", title="About Us")

@index_bp.route("/contact")
def contact():
    return render_template("basic/contact.html", title="Contact Us")