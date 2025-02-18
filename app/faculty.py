from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import CustomUser, Faculty, InternshipApplication, db
from flask_mail import Message
from app import mail  # Import the mail object

faculty_bp = Blueprint("faculty", __name__)

@faculty_bp.route("/faculty", methods=["GET"])
def profile():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if user is None or faculty is None:
        return redirect(url_for('auth.login'))

    return render_template("faculty/profile.html", user=user, faculty=faculty)

@faculty_bp.route("/faculty/pending_approvals", methods=["GET"])
def pending_approvals():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if faculty is None:
        return redirect(url_for('auth.login'))

    pending_applications = InternshipApplication.query.filter_by(faculty_email=user.email, status="Pending Faculty Approval").all()

    return render_template("faculty/pending_approval.html", pending_applications=pending_applications)

@faculty_bp.route("/faculty/approve_application/<int:application_id>", methods=["POST"])
def approve_application(application_id):
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    action = request.form.get('action')
    application = InternshipApplication.query.get(application_id)

    if application:
        if action == 'approve':
            application.status = "Pending HOD Approval"
            db.session.commit()

            # Send email to HOD
            hod_email = "2022csb1071+hod@iitrpr.ac.in"  # Replace with actual HOD email
            hod_msg = Message(
                "New Internship Application for HOD Approval",
                sender="johnDoe18262117@gmail.com",
                recipients=[hod_email]
            )
            hod_msg.body = (
                f"Dear HOD,\n\n"
                f"A new internship application has been submitted by {application.name} and approved by {application.faculty_mentor}.\n\n"
                f"Please review and approve the application.\n\n"
                f"Thank you!"
            )
            mail.send(hod_msg)

            flash("Application approved and forwarded to HOD for approval.", "success")
        elif action == 'reject':
            application.status = "Rejected by Faculty"
            db.session.commit()
            flash("Application rejected.", "danger")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('faculty.pending_approvals'))

@faculty_bp.route("/faculty/hod_pending_approvals", methods=["GET"])
def hod_pending_approvals():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if faculty is None or not faculty.is_hod:
        return redirect(url_for('auth.login'))

    pending_applications = InternshipApplication.query.filter_by(status="Pending HOD Approval").all()

    return render_template("faculty/hod_pending_approval.html", pending_applications=pending_applications)

@faculty_bp.route("/faculty/hod_approve_application/<int:application_id>", methods=["POST"])
def hod_approve_application(application_id):
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if faculty is None or not faculty.is_hod:
        return redirect(url_for('auth.login'))

    action = request.form.get('action')
    application = InternshipApplication.query.get(application_id)

    if application:
        if action == 'approve':
            application.status = "Approved by HOD"
            db.session.commit()

            # Send email to student
            student_msg = Message(
                "Internship Application Approved by HOD",
                sender="johnDoe18262117@gmail.com",
                recipients=[application.email]
            )
            student_msg.body = f"Dear {application.name},\n\nYour internship application has been approved by the HOD.\n\nThank you!"
            mail.send(student_msg)

            flash("Application approved by HOD.", "success")
        elif action == 'reject':
            application.status = "Rejected by HOD"
            db.session.commit()

            # Send email to student
            student_msg = Message(
                "Internship Application Rejected by HOD",
                sender="johnDoe18262117@gmail.com",
                recipients=[application.email]
            )
            student_msg.body = f"Dear {application.name},\n\nYour internship application has been rejected by the HOD.\n\nThank you!"
            mail.send(student_msg)

            flash("Application rejected by HOD.", "danger")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('faculty.hod_pending_approvals'))