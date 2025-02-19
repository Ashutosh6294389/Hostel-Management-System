-- Insert a new hostel if not already present
INSERT INTO hostel (hostel_no, hostel_name, hostel_type, num_floors, capacity)
VALUES ('H-101', 'Boys Hostel', 'Residential', 5, 200)
ON CONFLICT (hostel_no) DO NOTHING;

-- Insert a new user into custom_user if not already present (Student)
INSERT INTO custom_user (email, name, password)
VALUES ('2022csb1132+student@iitrpr.ac.in', 'Ashutosh Singh', 'yourpassword')
ON CONFLICT (email) DO NOTHING;

-- Get the ID of the inserted or existing user
WITH user_id_cte AS (
    SELECT id FROM custom_user WHERE email = '2022csb1132+student@iitrpr.ac.in'
)
-- Insert the student record using the retrieved ID
INSERT INTO student (student_id, department, student_phone, student_roll, student_year, student_room_no, student_batch)
SELECT id, 'CSE', '9876543210', '2022CSB1132', 3, 'A-101', 'Batch-2022'
FROM user_id_cte
ON CONFLICT (student_id) DO NOTHING;

-- Insert a new user into custom_user if not already present (HOD Faculty)
INSERT INTO custom_user (email, name, password, is_staff)
VALUES ('2022csb1132+hod@iitrpr.ac.in', 'Dr. Rajesh Kumar', 'securepassword', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Get the ID of the inserted or existing user
WITH hod_user_cte AS (
    SELECT id FROM custom_user WHERE email = '2022csb1132+hod@iitrpr.ac.in'
)
-- Insert the HOD faculty record using the retrieved ID
INSERT INTO faculty (faculty_id, department, faculty_phone, is_hod)
SELECT id, 'CSE', '9998887776', TRUE
FROM hod_user_cte
ON CONFLICT (faculty_id) DO NOTHING;

-- Insert a new user into custom_user if not already present (Non-HOD Faculty)
INSERT INTO custom_user (email, name, password, is_staff)
VALUES ('2022csb1132+faculty@iitrpr.ac.in', 'Dr. Sandeep Verma', 'securepassword', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Get the ID of the inserted or existing user
WITH faculty_user_cte AS (
    SELECT id FROM custom_user WHERE email = '2022csb1132+faculty@iitrpr.ac.in'
)
-- Insert the Non-HOD faculty record using the retrieved ID
INSERT INTO faculty (faculty_id, department, faculty_phone, is_hod)
SELECT id, 'CSE', '9998887775', FALSE
FROM faculty_user_cte
ON CONFLICT (faculty_id) DO NOTHING;

-- Insert a new user into custom_user if not already present (Admin)
INSERT INTO custom_user (email, name, password, is_staff)
VALUES ('2022csb1132+admin@iitrpr.ac.in', 'Admin User', 'adminpassword', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Get the ID of the inserted or existing user
WITH admin_user_cte AS (
    SELECT id FROM custom_user WHERE email = '2022csb1132+admin@iitrpr.ac.in'
)
-- Insert the Admin record using the retrieved ID
INSERT INTO admin (admin_id, phone)
SELECT id, '9998887774'
FROM admin_user_cte
ON CONFLICT (admin_id) DO NOTHING;

-- Insert a new user into custom_user if not already present (Caretaker)
INSERT INTO custom_user (email, name, password, is_staff)
VALUES ('2022csb1132+caretaker@iitrpr.ac.in', 'Ramesh Sharma', 'caretakerpassword', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Get the ID of the inserted or existing user
WITH caretaker_user_cte AS (
    SELECT id FROM custom_user WHERE email = '2022csb1132+caretaker@iitrpr.ac.in'
)
-- Insert the Caretaker record using the retrieved ID
INSERT INTO caretaker (user_id, hostel_no)
SELECT id, 'H-101'
FROM caretaker_user_cte
ON CONFLICT (user_id) DO NOTHING;