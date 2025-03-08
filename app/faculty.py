from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from app.models import CustomUser, Faculty, InternshipApplication, db, Batch, Room, Student, Hostel  # Add Batch, Room, and Student imports
from flask_mail import Message
from app import mail  

faculty_bp = Blueprint("faculty", __name__)

@faculty_bp.route("/faculty", methods=["GET", "POST"])
def profile():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if user is None or faculty is None:
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        if 'signature' in request.files:
            signature_file = request.files['signature']
            if signature_file:
                signature_blob = signature_file.read()
                faculty.signature = signature_blob
                db.session.commit()
                flash("Signature updated successfully.", "success")
            else:
                flash("No file selected for uploading.", "danger")

    return render_template("faculty/profile.html", user=user, faculty=faculty)


@faculty_bp.route("/faculty/sandbox", methods=["GET", "POST"])
def sandbox():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if faculty is None or not faculty.warden:
        return redirect(url_for('auth.login'))

    batches = Batch.query.all()
    hostels = Hostel.query.all()

    # Calculate the number of unoccupied rooms for each hostel
    hostel_data = []
    for hostel in hostels:
        unoccupied_rooms = sum(room.room_occupancy - room.current_occupancy for room in hostel.rooms)
        if unoccupied_rooms > 0:
            hostel_data.append({
                'hostel_no': hostel.hostel_no,
                'hostel_name': hostel.hostel_name,
                'hostel_type': hostel.hostel_type,
                'unoccupied_rooms': unoccupied_rooms
            })

    # Get unallocated students for each batch
    batch_data = []
    for batch in batches:
        unallocated_students = Student.query.filter_by(student_batch=batch.batch_no, student_room_no=None).all()
        batch_data.append({
            'batch_no': batch.batch_no,
            'number_of_students': batch.number_of_students,
            'unallocated_students': [{'id': student.student_id, 'name': student.user.name, 'gender': student.user.gender} for student in unallocated_students]
        })

    return render_template("faculty/sandbox.html", faculty=faculty, batches=batch_data, hostels=hostel_data, csrf_token=session.get('_csrf_token'))

@faculty_bp.route("/faculty/allocate_room", methods=["POST"])
def allocate_room():
    data = request.get_json()
    batch_id = data.get('batch_id')
    hostel_no = data.get('hostel_no')
    hostel_type = data.get('hostel_type')

    print(f"Allocating rooms for batch: {batch_id}, hostel: {hostel_no}, type: {hostel_type}")

    batch = Batch.query.filter_by(batch_no=batch_id).first()
    rooms = Room.query.filter_by(hostel_no=hostel_no).all()

    if batch and rooms:
        unallocated_students = Student.query.filter_by(student_batch=batch_id, student_room_no=None).all()
        students_to_allocate = []

        for student in unallocated_students:
            if hostel_type == 'Mixed' or (hostel_type == 'Boys' and student.user.gender == 'Male') or (hostel_type == 'Girls' and student.user.gender == 'Female'):
                students_to_allocate.append(student)

        if not students_to_allocate:
            print("No students to allocate based on gender.")
            return jsonify(success=False, message="No students to allocate based on gender.")

        for room in rooms:
            if room.current_occupancy < room.room_occupancy:
                available_slots = room.room_occupancy - room.current_occupancy
                students_for_room = students_to_allocate[:available_slots]

                for student in students_for_room:
                    student.student_room_no = room.room_no
                    room.current_occupancy += 1
                    students_to_allocate.remove(student)

                db.session.commit()

                if not students_to_allocate:
                    break

        print("Room allocation successful.")
        return jsonify(success=True)
    else:
        print("Failed to allocate rooms.")
        return jsonify(success=False, message="Failed to allocate rooms.")
    
@faculty_bp.route("/faculty/signature/<int:faculty_id>")
def get_signature(faculty_id):
    faculty = Faculty.query.get(faculty_id)
    if faculty and faculty.signature:
        return faculty.signature, 200, {'Content-Type': 'image/png'}
    return '', 404

@faculty_bp.route("/faculty/pending_approvals", methods=["GET", "POST"])
def pending_approvals():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if faculty is None:
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    query = InternshipApplication.query.filter_by(faculty_email=user.email, status="Pending Faculty Approval")

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

    pending_applications = query.all()

    return render_template("faculty/pending_approval.html", faculty=faculty, pending_applications=pending_applications, search_query=search_query, sort_by=sort_by, sort_order=sort_order)
@faculty_bp.route("/faculty/approve_application/<int:application_id>", methods=["POST"])
def approve_application(application_id):
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    action = request.form.get('action')
    application = InternshipApplication.query.get(application_id)

    if application:
        if action == 'approve':
            application.status = "Pending HOD Approval"
            application.faculty_signature_id = faculty.faculty_id
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
            application.hod_signature_id = faculty.faculty_id
            db.session.commit()

            # Send email to admin
            admin_email = "2022csb1071+admin@iitrpr.ac.in"  # Replace with actual admin email
            admin_msg = Message(
                "New Internship Application for Admin Approval",
                sender="johnDoe18262117@gmail.com",
                recipients=[admin_email]
            )
            admin_msg.body = (
                f"Dear Admin,\n\n"
                f"A new internship application has been submitted by {application.name} and approved by {faculty.user.name}.\n\n"
                f"Please review and approve the application.\n\n"
                f"Thank you!"
            )
            mail.send(admin_msg)

            flash("Application approved and forwarded to Admin for approval.", "success")
        elif action == 'reject':
            application.status = "Rejected by HOD"
            db.session.commit()
            flash("Application rejected.", "danger")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('faculty.hod_pending_approvals'))

@faculty_bp.route("/faculty/hod_pending_approvals", methods=["GET", "POST"])
def hod_pending_approvals():
    if 'user_id' not in session or session.get('user_role') != 'faculty':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    faculty = Faculty.query.filter_by(faculty_id=user_id).first()

    if faculty is None or not faculty.is_hod:
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    query = InternshipApplication.query.filter_by(status="Pending HOD Approval")

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

    pending_applications = query.all()

    return render_template("faculty/hod_pending_approval.html", faculty=faculty, pending_applications=pending_applications, search_query=search_query, sort_by=sort_by, sort_order=sort_order)

@faculty_bp.route("/faculty/get_unallocated_students", methods=["POST"])
def get_unallocated_students():
    data = request.get_json()
    batch_id = data.get('batch_id')

    unallocated_students = Student.query.filter_by(student_batch=batch_id, student_room_no=None).all()
    students_to_display = [{'id': student.student_id, 'name': student.user.name, 'gender': student.user.gender} for student in unallocated_students]

    return jsonify(success=True, unallocated_students=students_to_display)