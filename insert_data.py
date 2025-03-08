from app import create_app
from app.database import db
from app.models import CustomUser, Student, Faculty, Caretaker, Admin, Hostel, Room, Warden, Batch, InternshipApplication, CaretakerHistory
from datetime import datetime

app = create_app()

with app.app_context():
    db.create_all()

    # Increase the capacity of Bhramaputra hostel by 100
    bhramaputra_hostel = Hostel.query.filter_by(hostel_no='BR').first()
    if bhramaputra_hostel:
        bhramaputra_hostel.capacity += 100
        db.session.commit()

    # Add new rooms to Bhramaputra hostel based on the increased capacity
    new_rooms = [
        Room(room_no=f'BR-{floor}-{room}', floor=floor, hostel_no='BR', room_occupancy=2, current_occupancy=0)
        for floor in range(1, 7)  # Assuming 6 floors
        for room in range(101, 118)  # Adding 17 rooms per floor
    ]
    db.session.bulk_save_objects(new_rooms)
    db.session.commit()

   