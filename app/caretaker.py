from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import CustomUser, Caretaker, InternshipApplication, Room, Hostel, db
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

@caretaker_bp.route("/caretaker/pending_approvals", methods=["GET"])
def pending_approvals():
    if 'user_id' not in session or session.get('user_role') != 'caretaker':
        return redirect(url_for('auth.login'))

    pending_applications = InternshipApplication.query.filter_by(status="Approved by Admin").all()

    return render_template("caretaker/pending_approvals.html", pending_applications=pending_applications)

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
            db.session.commit()

            # Allocate room
            room.current_occupancy += 1
            db.session.commit()

            # Send email to student
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