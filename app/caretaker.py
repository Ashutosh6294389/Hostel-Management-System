from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from app.models import CustomUser, Caretaker, InternshipApplication, Room, Hostel, db, Batch, Student
from flask_mail import Message
from app import mail

caretaker_bp = Blueprint("caretaker", __name__)

@caretaker_bp.route("/caretaker", methods=["GET"])
def profile():
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = CustomUser.query.get(user_id)
    caretaker = Caretaker.query.filter_by(user_id=user_id).first()

    if user is None or caretaker is None:
        return redirect(url_for('auth.login'))

    hostel = Hostel.query.filter_by(hostel_no=caretaker.hostel_no).first()

    return render_template("caretaker/profile.html", user=user, caretaker=caretaker, hostel=hostel)

@caretaker_bp.route("/caretaker/pending_approvals", methods=["GET", "POST"])
def pending_approvals():
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    query = InternshipApplication.query.filter_by(status="Approved by Admin")

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

    return render_template("caretaker/pending_approvals.html", pending_applications=pending_applications, search_query=search_query, sort_by=sort_by, sort_order=sort_order)

@caretaker_bp.route("/caretaker/approve_application/<int:application_id>", methods=["POST"])
def approve_application(application_id):
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))

    room_no = request.form.get('room_no')
    application = InternshipApplication.query.get(application_id)

    if application:
        room = Room.query.filter_by(room_no=room_no).first()
        if room:
            application.status = "Approved by Caretaker"
            application.room_no = room_no
            db.session.commit()

            room.current_occupancy += 1
            db.session.commit()

            student_msg = Message(
                "Internship Application Approved and Room Allocated",
                sender="johnDoe18262117@gmail.com",
                recipients=[application.email]
            )
            student_msg.body = (
                f"Dear {application.name},\n\n"
                f"Your internship application has been approved by the caretaker.\n"
                f"You have been allocated room number {room_no} in hostel {room.hostel_no}.\n\n"
                f"Thank you!"
            )
            mail.send(student_msg)

            flash("Application approved and room allocated.", "success")
        else:
            flash("Room number does not exist.", "danger")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('caretaker.pending_approvals'))

@caretaker_bp.route("/caretaker/rooms", methods=["GET"])
def rooms():
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    caretaker = Caretaker.query.filter_by(user_id=user_id).first()

    if caretaker is None:
        return redirect(url_for('auth.login'))

    rooms = Room.query.filter_by(hostel_no=caretaker.hostel_no).all()

    return render_template("caretaker/rooms.html", rooms=rooms)

@caretaker_bp.route("/caretaker/vacant_rooms", methods=["GET"])
def vacant_rooms():
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    caretaker = Caretaker.query.filter_by(user_id=user_id).first()

    if caretaker is None:
        return redirect(url_for('auth.login'))

    vacant_rooms = Room.query.filter(Room.hostel_no == caretaker.hostel_no, Room.current_occupancy < Room.room_occupancy).all()

    return render_template("caretaker/vacant_rooms.html", vacant_rooms=vacant_rooms)

@caretaker_bp.route("/caretaker/sandbox", methods=["GET", "POST"])
def sandbox():
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    caretaker = Caretaker.query.filter_by(user_id=user_id).first()

    if caretaker is None:
        return redirect(url_for('auth.login'))

    # Get the hostel assigned to the caretaker
    assigned_hostel = Hostel.query.filter_by(hostel_no=caretaker.hostel_no).first()

    # Calculate the number of unoccupied rooms for the assigned hostel
    unoccupied_rooms = sum(room.room_occupancy - room.current_occupancy for room in assigned_hostel.rooms)
    hostel_data = [{
        'hostel_no': assigned_hostel.hostel_no,
        'hostel_name': assigned_hostel.hostel_name,
        'hostel_type': assigned_hostel.hostel_type,
        'unoccupied_rooms': unoccupied_rooms
    }]

    # Get unallocated students for each batch
    batches = Batch.query.all()
    batch_data = []
    for batch in batches:
        unallocated_students = Student.query.filter_by(student_batch=batch.batch_no, student_room_no=None).all()
        batch_data.append({
            'batch_no': batch.batch_no,
            'number_of_students': batch.number_of_students,
            'unallocated_students': [{'id': student.student_id, 'name': student.user.name, 'gender': student.user.gender} for student in unallocated_students]
        })

    # Get unallocated internship students
    unallocated_internship_students = InternshipApplication.query.filter_by(status="Approved by Admin").all()
    internship_students_data = [{'id': student.id, 'name': student.name, 'gender': student.gender} for student in unallocated_internship_students]

    # Get internship students with pending approvals
    pending_internship_students = InternshipApplication.query.filter_by(status="Approved by Admin").all()
    pending_internship_students_data = [{'id': student.id, 'name': student.name, 'gender': student.gender} for student in pending_internship_students]

    num_unallocated_internship_students = len(unallocated_internship_students)
    return render_template("caretaker/sandbox.html", caretaker=caretaker, batches=batch_data, hostels=hostel_data, internship_students=internship_students_data, num_unallocated_internship_students=num_unallocated_internship_students, csrf_token=session.get('_csrf_token'))

@caretaker_bp.route("/caretaker/get_unallocated_students", methods=["POST"])
def get_unallocated_students():
    data = request.get_json()
    batch_id = data.get('batch_id')

    unallocated_students = Student.query.filter_by(student_batch=batch_id, student_room_no=None).all()
    students_to_display = [{'id': student.student_id, 'name': student.user.name, 'gender': student.user.gender} for student in unallocated_students]

    return jsonify(success=True, unallocated_students=students_to_display)

@caretaker_bp.route("/caretaker/allocate_room", methods=["POST"])
def allocate_room():
    data = request.get_json()
    student_type = data.get('student_type')
    if student_type == 'None':
        student_type = data.get('batch_id')
    hostel_no = data.get('hostel_no')
    hostel_type = data.get('hostel_type')

    print(f"Allocating rooms for student type: {student_type}, hostel: {hostel_no}, type: {hostel_type}")

    if student_type == 'internship':
        unallocated_students = InternshipApplication.query.filter_by(status="Approved by Admin", room_no=None).all()
    else:
        unallocated_students = Student.query.filter_by(student_batch=student_type, student_room_no=None).all()

    rooms = Room.query.filter_by(hostel_no=hostel_no).all()

    if unallocated_students and rooms:
        students_to_allocate = []

        for student in unallocated_students:
            if student_type == 'internship':
                student_gender = student.gender
            else:
                student_gender = student.user.gender

            if hostel_type == 'Mixed' or (hostel_type == 'Boys' and student_gender == 'Male') or (hostel_type == 'Girls' and student_gender == 'Female'):
                students_to_allocate.append(student)

        if not students_to_allocate:
            print("No students to allocate based on gender.")
            return jsonify(success=False, message="No students to allocate based on gender.")

        for room in rooms:
            if room.current_occupancy < room.room_occupancy:
                available_slots = room.room_occupancy - room.current_occupancy
                students_for_room = students_to_allocate[:available_slots]

                for student in students_for_room:
                    if student_type == 'internship':
                        student.room_no = room.room_no
                        student.status = "Approved by Caretaker"
                        # Check if the student exists in InternshipApplication and update the status
                        application = InternshipApplication.query.filter_by(name=student.name).first()
                        if application:
                            application.status = "Approved by Caretaker"
                    else:
                        student.student_room_no = room.room_no
                    room.current_occupancy += 1
                    students_to_allocate.remove(student)

                db.session.commit()

                if not students_to_allocate:
                    break

        print("Room allocation successful.")
        if student_type == 'internship':
            updated_students = [{'id': student.id, 'name': student.name, 'gender': student.gender} for student in unallocated_students]
        else:
            updated_students = [{'id': student.student_id, 'name': student.user.name, 'gender': student.user.gender} for student in unallocated_students]
        return jsonify(success=True, updated_students=updated_students)
    else:
        print("Failed to allocate rooms.")
        return jsonify(success=False, message="Failed to allocate rooms.")