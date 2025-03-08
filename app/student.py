from flask import Blueprint, render_template, session, redirect, url_for, request, flash, send_file
from app.models import CustomUser, Student, InternshipApplication, Faculty, Admin, db
from werkzeug.utils import secure_filename
from flask_mail import Message
from app import mail  
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile

student_bp = Blueprint("student", __name__)

@student_bp.route("/student", methods=["GET"])
def profile():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    student = Student.query.filter_by(student_id=user_id).first()

    if user is None or student is None:
        return redirect(url_for('auth.login'))

    internship_application = InternshipApplication.query.filter_by(email=user.email).first()

    return render_template("student/profile.html", user=user, student=student, internship_application=internship_application)

@student_bp.route("/student/internship_form", methods=["GET"])
def internship_form():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('auth.login'))

    return render_template("student/internship_form.html")

@student_bp.route("/student/submit_internship_form", methods=["POST"])
def submit_internship_form():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return redirect(url_for('auth.login'))

    name = request.form.get('name')
    gender = request.form.get('gender')
    affiliation = request.form.get('affiliation')
    address = request.form.get('address')
    contact_number = request.form.get('contact_number')
    email = request.form.get('email')
    faculty_mentor = request.form.get('faculty_mentor')
    faculty_email = request.form.get('faculty_email')
    arrival_date = request.form.get('arrival_date')
    departure_date = request.form.get('departure_date')
    remarks = request.form.get('remarks')

    id_card = request.files['id_card']
    official_letter = request.files['official_letter']

    if id_card and official_letter:
        # Ensure the uploads directory exists
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        id_card_filename = secure_filename(id_card.filename)
        official_letter_filename = secure_filename(official_letter.filename)

        id_card.save(os.path.join(uploads_dir, id_card_filename))
        official_letter.save(os.path.join(uploads_dir, official_letter_filename))

        # Convert date strings to Python date objects
        arrival_date = datetime.strptime(arrival_date, '%Y-%m-%d').date()
        departure_date = datetime.strptime(departure_date, '%Y-%m-%d').date()

        internship_application = InternshipApplication(
            name=name,
            gender=gender,
            affiliation=affiliation,
            address=address,
            contact_number=contact_number,
            email=email,
            faculty_mentor=faculty_mentor,
            faculty_email=faculty_email,
            arrival_date=arrival_date,
            departure_date=departure_date,
            id_card=id_card_filename,
            official_letter=official_letter_filename,
            remarks=remarks
        )

        db.session.add(internship_application)
        db.session.commit()

        # Send email to student
        student_msg = Message(
            "Internship Application Submitted",
            sender="johnDoe18262117@gmail.com",
            recipients=[email]
        )
        student_msg.body = f"Dear {name},\n\nYour internship application has been submitted successfully.\n\nThank you!"
        mail.send(student_msg)

        # Send email to faculty
        faculty_msg = Message(
            "New Internship Application for Approval",
            sender="johnDoe18262117@gmail.com",
            recipients=[faculty_email]
        )
        faculty_msg.body = (
            f"Dear {faculty_mentor},\n\n"
            f"A new internship application has been submitted by {name}.\n\n"
            f"Please review and approve the application.\n\n"
            f"Thank you!"
        )
        mail.send(faculty_msg)

        # Send email to HOD
        hod_email = "2022csb1071+hod@iitrpr.ac.in"  # Replace with actual HOD email
        hod_msg = Message(
            "New Internship Application for HOD Approval",
            sender="johnDoe18262117@gmail.com",
            recipients=[hod_email]
        )
        hod_msg.body = (
            f"Dear HOD,\n\n"
            f"A new internship application has been submitted by {name} and approved by {faculty_mentor}.\n\n"
            f"Please review and approve the application.\n\n"
            f"Thank you!"
        )
        mail.send(hod_msg)

        # Send email to admin
        admin_email = "2022csb1071+admin@iitrpr.ac.in"  # Replace with actual admin email
        admin_msg = Message(
            "New Internship Application Submitted",
            sender="johnDoe18262117@gmail.com",
            recipients=[admin_email]
        )
        admin_msg.body = (
            f"Dear Admin,\n\n"
            f"A new internship application has been submitted by {name}.\n\n"
            f"Details:\n"
            f"Name: {name}\n"
            f"Gender: {gender}\n"
            f"Affiliation: {affiliation}\n"
            f"Address: {address}\n"
            f"Contact Number: {contact_number}\n"
            f"Email: {email}\n"
            f"Faculty Mentor: {faculty_mentor}\n"
            f"Faculty Email: {faculty_email}\n"
            f"Arrival Date: {arrival_date}\n"
            f"Departure Date: {departure_date}\n"
            f"Remarks: {remarks}\n\n"
            f"Thank you!"
        )
        mail.send(admin_msg)

        flash("Internship application submitted successfully.", "success")
    else:
        flash("Please upload the required documents.", "danger")

    return redirect(url_for('student.internship_form'))

@student_bp.route("/student/download_application_pdf", methods=["GET"])
def download_application_pdf():
    user_id = session.get('user_id')
    if not user_id or session.get('user_role') != 'student':
        return redirect(url_for('auth.login'))

    user = CustomUser.query.get(user_id)
    application = InternshipApplication.query.filter_by(email=user.email, status="Approved by Caretaker").first()

    if not application:
        flash("Application not found or not approved by caretaker.", "danger")
        return redirect(url_for('student.profile'))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.drawString(100, height - 100, f"Internship Application Approval")
    c.drawString(100, height - 120, f"Name: {application.name}")
    c.drawString(100, height - 140, f"Gender: {application.gender}")
    c.drawString(100, height - 160, f"Affiliation: {application.affiliation}")
    c.drawString(100, height - 180, f"Address: {application.address}")
    c.drawString(100, height - 200, f"Contact Number: {application.contact_number}")
    c.drawString(100, height - 220, f"Email: {application.email}")
    c.drawString(100, height - 240, f"Faculty Mentor: {application.faculty_mentor}")
    c.drawString(100, height - 260, f"Faculty Email: {application.faculty_email}")
    c.drawString(100, height - 280, f"Arrival Date: {application.arrival_date}")
    c.drawString(100, height - 300, f"Departure Date: {application.departure_date}")
    c.drawString(100, height - 320, f"Remarks: {application.remarks}")

    c.drawString(100, height - 360, f"Signatures:")

    def draw_signature(signature_data, x, y, label):
        if signature_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                tmpfile.write(signature_data)
                tmpfile.flush()
                c.drawImage(tmpfile.name, x, y, width=100, height=50)
            c.drawString(x, y - 20, label)

    faculty = Faculty.query.get(application.faculty_signature_id)
    if faculty and faculty.signature:
        draw_signature(faculty.signature, 100, height - 400, "Faculty Signature")

    hod = Faculty.query.get(application.hod_signature_id)
    if hod and hod.signature:
        draw_signature(hod.signature, 100, height - 480, "HOD Signature")

    admin = Admin.query.get(application.admin_signature_id)
    if admin and admin.signature:
        draw_signature(admin.signature, 100, height - 560, "Admin Signature")

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f'internship_approval_{application.id}.pdf', mimetype='application/pdf')