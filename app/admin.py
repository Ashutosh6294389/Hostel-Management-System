from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import CustomUser, Admin, InternshipApplication, Student, Faculty, db
import csv
import io

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    admin = Admin.query.filter_by(admin_id=user_id).first()

    if user is None or admin is None:
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        if 'signature' in request.files:
            signature_file = request.files['signature']
            if signature_file:
                signature_blob = signature_file.read()
                admin.signature = signature_blob
                db.session.commit()
                flash("Signature updated successfully.", "success")
            else:
                flash("No file selected for uploading.", "danger")

    return render_template("admin/profile.html", user=user, admin=admin)

@admin_bp.route("/admin/signature/<int:admin_id>")
def get_signature(admin_id):
    admin = Admin.query.get(admin_id)
    if admin and admin.signature:
        return admin.signature, 200, {'Content-Type': 'image/png'}
    return '', 404

@admin_bp.route("/admin/pending_internship_applications", methods=["GET", "POST"])
def pending_internship_applications():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    query = InternshipApplication.query.filter(InternshipApplication.status == "Approved by HOD")

    if search_query:
        query = query.filter(
            InternshipApplication.name.ilike(f'%{search_query}%') |
            InternshipApplication.email.ilike(f'%{search_query}%')
        )

    if sort_by == 'name':
        if sort_order == 'asc':
            query = query.order_by(InternshipApplication.name.asc())
        else:
            query = query.order_by(InternshipApplication.name.desc())
    elif sort_by == 'email':
        if sort_order == 'asc':
            query = query.order_by(InternshipApplication.email.asc())
        else:
            query = query.order_by(InternshipApplication.email.desc())
    elif sort_by == 'status':
        if sort_order == 'asc':
            query = query.order_by(InternshipApplication.status.asc())
        else:
            query = query.order_by(InternshipApplication.status.desc())

    applications = query.all()

    return render_template("admin/pending_internship_applications.html", applications=applications, search_query=search_query, sort_by=sort_by, sort_order=sort_order)

@admin_bp.route("/admin/approve_internship_application/<int:application_id>", methods=["POST"])
def approve_internship_application(application_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    admin = Admin.query.filter_by(admin_id=user_id).first()

    action = request.form.get('action')
    application = InternshipApplication.query.get(application_id)

    if application:
        if application.status == "Approved by HOD":
            if action == 'approve':
                application.status = "Approved by Admin"
                application.admin_signature_id = admin.admin_id  # Store admin 
                flash("Application approved.", "success")
            elif action == 'disapprove':
                application.status = "Disapproved by Admin"
                flash("Application disapproved.", "danger")
            db.session.commit()
        else:
            flash("Application must be approved by HOD before admin approval.", "warning")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('admin.pending_internship_applications'))

@admin_bp.route("/admin/approved_applications", methods=["GET"])
def approved_applications():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    query = InternshipApplication.query.filter_by(status="Approved by Caretaker")

    if search_query:
        query = query.filter(
            InternshipApplication.name.ilike(f'%{search_query}%') |
            InternshipApplication.email.ilike(f'%{search_query}%')
        )

    if sort_by == 'name':
        if sort_order == 'asc':
            query = query.order_by(InternshipApplication.name.asc())
        else:
            query = query.order_by(InternshipApplication.name.desc())
    elif sort_by == 'email':
        if sort_order == 'asc':
            query = query.order_by(InternshipApplication.email.asc())
        else:
            query = query.order_by(InternshipApplication.email.desc())
    elif sort_by == 'status':
        if sort_order == 'asc':
            query = query.order_by(InternshipApplication.status.asc())
        else:
            query = query.order_by(InternshipApplication.status.desc())

    applications = query.all()

    return render_template("admin/approved_applications.html", applications=applications, search_query=search_query, sort_by=sort_by, sort_order=sort_order)

@admin_bp.route("/admin/add_users", methods=["GET"])
def add_users():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    return render_template("admin/add_users.html")

@admin_bp.route("/admin/upload_csv", methods=["POST"])
def upload_csv():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))

    csv_file = request.files['csv_file']
    user_type = request.form.get('user_type')

    if not csv_file or not user_type:
        flash("Please upload a CSV file and select a user type.", "danger")
        return redirect(url_for('admin.add_users'))

    stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    headers = next(csv_input)

    if user_type == "student":
        for row in csv_input:
            student_data = dict(zip(headers, row))
            custom_user = CustomUser(
                email=student_data['email'],
                name=student_data['name'],
                password=student_data['password'],
                is_staff=False,
                is_active=True,
                gender=student_data['gender']
            )
            db.session.add(custom_user)
            db.session.flush()  # Get the ID of the newly added CustomUser

            student = Student(
                student_id=custom_user.id,
                department=student_data['department'],
                student_phone=student_data['student_phone'],
                student_roll=student_data['student_roll'],
                student_year=student_data['student_year'],
                student_room_no=student_data['student_room_no'],
                student_batch=student_data['student_batch']
            )
            db.session.add(student)
        db.session.commit()
        flash("Students added successfully.", "success")

    elif user_type == "faculty":
        for row in csv_input:
            faculty_data = dict(zip(headers, row))
            custom_user = CustomUser(
                email=faculty_data['email'],
                name=faculty_data['name'],
                password=faculty_data['password'],
                is_staff=True,
                is_active=True,
                gender=faculty_data['gender']
            )
            db.session.add(custom_user)
            db.session.flush()  # Get the ID of the newly added CustomUser

            faculty = Faculty(
                faculty_id=custom_user.id,
                department=faculty_data['department'],
                faculty_phone=faculty_data['faculty_phone'],
                is_hod=faculty_data['is_hod'] == 'TRUE',
                signature=faculty_data['signature'].encode() if 'signature' in faculty_data else None
            )
            db.session.add(faculty)
        db.session.commit()
        flash("Faculties added successfully.", "success")

    return redirect(url_for('admin.add_users'))