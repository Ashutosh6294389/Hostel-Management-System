from app.database import db

class CustomUser(db.Model):
    __tablename__ = 'custom_user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    gender = db.Column(db.String(20), default='Not Specified')

    student = db.relationship('Student', backref='user', uselist=False, cascade="all, delete")
    caretaker = db.relationship('Caretaker', backref='user', uselist=False, cascade="all, delete")
    faculty = db.relationship('Faculty', backref='user', uselist=False, cascade="all, delete")
    admin = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete")

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, db.ForeignKey('custom_user.id', ondelete='CASCADE'), primary_key=True)
    department = db.Column(db.String(100))
    student_phone = db.Column(db.String(10))
    student_roll = db.Column(db.String(15), unique=True)
    student_year = db.Column(db.Integer)
    student_room_no = db.Column(db.String(20))
    student_batch = db.Column(db.String(20))

    applications = db.relationship('Application', backref='student', cascade="all, delete")

class Faculty(db.Model):
    __tablename__ = 'faculty'
    faculty_id = db.Column(db.Integer, db.ForeignKey('custom_user.id', ondelete='CASCADE'), primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    faculty_phone = db.Column(db.String(10), unique=True, nullable=False)
    is_hod = db.Column(db.Boolean, default=False)

    warden = db.relationship('Warden', backref='faculty', uselist=False, cascade="all, delete")

class Caretaker(db.Model):
    __tablename__ = 'caretaker'
    caretaker_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('custom_user.id', ondelete='CASCADE'), unique=True, nullable=False)
    hostel_no = db.Column(db.String(20), db.ForeignKey('hostel.hostel_no', ondelete='CASCADE'), nullable=False)

class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, db.ForeignKey('custom_user.id', ondelete='CASCADE'), primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)

class Hostel(db.Model):
    __tablename__ = 'hostel'
    hostel_no = db.Column(db.String(20), primary_key=True)
    hostel_name = db.Column(db.String(100))
    hostel_type = db.Column(db.String(50))
    num_floors = db.Column(db.Integer)
    capacity = db.Column(db.Integer)

    caretakers = db.relationship('Caretaker', backref='hostel', cascade="all, delete")
    wardens = db.relationship('Warden', backref='hostel', cascade="all, delete")
    rooms = db.relationship('Room', backref='hostel', cascade="all, delete")

class Room(db.Model):
    __tablename__ = 'room'
    room_no = db.Column(db.String(20), primary_key=True)
    floor = db.Column(db.Integer)
    hostel_no = db.Column(db.String(20), db.ForeignKey('hostel.hostel_no', ondelete='CASCADE'))
    room_occupancy = db.Column(db.Integer)
    current_occupancy = db.Column(db.Integer, default=0)

class Warden(db.Model):
    __tablename__ = 'warden'
    warden_id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id', ondelete='CASCADE'), unique=True, nullable=False)
    hostel_no = db.Column(db.String(20), db.ForeignKey('hostel.hostel_no', ondelete='CASCADE'), nullable=False)
    is_chief = db.Column(db.Boolean, default=False)

class Batch(db.Model):
    __tablename__ = 'batch'
    batch_no = db.Column(db.String(20), primary_key=True)
    number_of_students = db.Column(db.Integer)
    number_of_girls = db.Column(db.Integer)
    number_of_boys = db.Column(db.Integer)

class Application(db.Model):
    __tablename__ = 'application'
    application_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id', ondelete='CASCADE'), nullable=False)
    affiliation = db.Column(db.String(100))
    address = db.Column(db.String(100))
    phone = db.Column(db.String(10))
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id', ondelete='CASCADE'))
    arrival = db.Column(db.Date)
    departure = db.Column(db.Date)
    instid = db.Column(db.String(100))
    letter = db.Column(db.String(100))
    payment_proof = db.Column(db.String(100))
    status = db.Column(db.String(100), default="Pending")
    comments = db.Column(db.String(300))

    final_application = db.relationship('ApplicationFinal', backref='application', uselist=False, cascade="all, delete")

class ApplicationFinal(db.Model):
    __tablename__ = 'application_final'
    application_id = db.Column(db.Integer, db.ForeignKey('application.application_id', ondelete='CASCADE'), primary_key=True)
    hostel_no = db.Column(db.String(20), db.ForeignKey('hostel.hostel_no', ondelete='CASCADE'))
    room_no = db.Column(db.String(20), db.ForeignKey('room.room_no', ondelete='CASCADE'))

class InternshipApplication(db.Model):
    __tablename__ = 'internship_application'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    affiliation = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    faculty_mentor = db.Column(db.String(100), nullable=False)
    faculty_email = db.Column(db.String(100), nullable=False)
    arrival_date = db.Column(db.Date, nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    id_card = db.Column(db.String(100), nullable=False)
    official_letter = db.Column(db.String(100), nullable=False)
    remarks = db.Column(db.String(300))
    status = db.Column(db.String(50), default="Pending Faculty Approval", nullable=False)