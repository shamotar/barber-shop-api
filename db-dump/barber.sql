USE barbershop;

-- User Table
CREATE TABLE user (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    phoneNumber VARCHAR(10) UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Barber Table
CREATE TABLE barber (
    barber_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Appointment Table
CREATE TABLE appointment (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    barber_id INT NOT NULL,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (barber_id) REFERENCES barber(barber_id) ON DELETE CASCADE
);

-- Service Table
CREATE TABLE service (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    duration TIME NOT NULL,
    price DOUBLE(5,2) NOT NULL
);

-- Appointment_Service Table (Many-to-Many Relationship)
CREATE TABLE appointment_service (
    service_id INT,
    appointment_id INT,
    PRIMARY KEY (service_id, appointment_id),
    FOREIGN KEY (service_id) REFERENCES service(service_id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointment(appointment_id) ON DELETE CASCADE
);

-- Schedule Table
CREATE TABLE schedule (
    schedule_id INT PRIMARY KEY AUTO_INCREMENT,
    barber_id INT NOT NULL,
    appointment_id INT,
    date VARCHAR(10) NOT NULL,
    startTime TIME NOT NULL,
    endTime TIME NOT NULL,
    FOREIGN KEY (barber_id) REFERENCES barber(barber_id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointment(appointment_id) ON DELETE SET NULL
);

-- Thread Table (Messaging)
CREATE TABLE thread (
    thread_id INT PRIMARY KEY AUTO_INCREMENT,
    receivingUser INT NOT NULL,
    sendingUser INT NOT NULL,
    FOREIGN KEY (receivingUser) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (sendingUser) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Message Table
CREATE TABLE message (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    thread_id INT NOT NULL,
    hasActiveMessage BOOLEAN,
    text TEXT NOT NULL,
    timeStamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES thread(thread_id) ON DELETE CASCADE
);


-- Insert sample users (customers and barbers)
INSERT INTO user (firstName, lastName, email, password, phoneNumber, is_admin) VALUES
('John', 'Doe', 'john.doe@example.com', 'hashedpassword1', '1234567890', TRUE),  -- Barber
('Jane', 'Smith', 'jane.smith@example.com', 'hashedpassword2', '0987654321', FALSE), -- Customer
('Mike', 'Johnson', 'mike.johnson@example.com', 'hashedpassword3', '1122334455', TRUE), -- Barber
('Sarah', 'Brown', 'sarah.brown@example.com', 'hashedpassword4', '6677889900', FALSE); -- Customer

-- Insert sample barbers (linking them to existing users)
INSERT INTO barber (user_id) VALUES
(1), -- John Doe is a barber
(3); -- Mike Johnson is a barber

-- Insert sample appointments (one for each barber)
INSERT INTO appointment (user_id, barber_id, status) VALUES
(2, 1, 'confirmed'),  -- Jane Smith books an appointment with John Doe
(4, 2, 'confirmed'); -- Sarah Brown books an appointment with Mike Johnson

-- Insert sample services
INSERT INTO service (name, duration, price) VALUES
('Haircut', '00:30:00', 20.00),
('Beard Trim', '00:15:00', 10.00),
('Shave', '00:20:00', 15.00),
('Hair Coloring', '01:00:00', 50.00);

-- Insert appointment services (services linked to each appointment)
INSERT INTO appointment_service (service_id, appointment_id) VALUES
(1, 1), -- Haircut for appointment 1 (Jane -> John)
(3, 2); -- Shave for appointment 2 (Sarah -> Mike)

-- Insert weekly schedule for John Doe (Barber ID 1)
INSERT INTO schedule (barber_id, appointment_id, date, startTime, endTime) VALUES
(1, 1, '2025-02-17', '09:00:00', '09:30:00'), -- Linked to Jane's appointment
(1, NULL, '2025-02-17', '09:30:00', '10:00:00'),
(1, NULL, '2025-02-17', '10:00:00', '10:30:00'),
(1, NULL, '2025-02-17', '10:30:00', '11:00:00'),
(1, NULL, '2025-02-17', '11:00:00', '11:30:00'),
(1, NULL, '2025-02-17', '11:30:00', '12:00:00'),
(1, NULL, '2025-02-17', '12:30:00', '13:00:00'),
(1, NULL, '2025-02-17', '13:00:00', '13:30:00'),
(1, NULL, '2025-02-17', '13:30:00', '14:00:00'),
(1, NULL, '2025-02-17', '14:00:00', '14:30:00'),
(1, NULL, '2025-02-17', '14:30:00', '15:00:00'),
(1, NULL, '2025-02-17', '15:00:00', '15:30:00'),
(1, NULL, '2025-02-17', '15:30:00', '16:00:00'),
(1, NULL, '2025-02-17', '16:00:00', '16:30:00'),
(1, NULL, '2025-02-17', '16:30:00', '17:00:00');

-- Insert weekly schedule for Mike Johnson (Barber ID 3)
INSERT INTO schedule (barber_id, appointment_id, date, startTime, endTime) VALUES
(2, 2, '2025-02-17', '09:00:00', '09:30:00'), -- Linked to Sarah's appointment
(2, NULL, '2025-02-17', '09:30:00', '10:00:00'),
(2, NULL, '2025-02-17', '10:00:00', '10:30:00'),
(2, NULL, '2025-02-17', '10:30:00', '11:00:00'),
(2, NULL, '2025-02-17', '11:00:00', '11:30:00'),
(2, NULL, '2025-02-17', '11:30:00', '12:00:00'),
(2, NULL, '2025-02-17', '12:30:00', '13:00:00'),
(2, NULL, '2025-02-17', '13:00:00', '13:30:00'),
(2, NULL, '2025-02-17', '13:30:00', '14:00:00'),
(2, NULL, '2025-02-17', '14:00:00', '14:30:00'),
(2, NULL, '2025-02-17', '14:30:00', '15:00:00'),
(2, NULL, '2025-02-17', '15:00:00', '15:30:00'),
(2, NULL, '2025-02-17', '15:30:00', '16:00:00'),
(2, NULL, '2025-02-17', '16:00:00', '16:30:00'),
(2, NULL, '2025-02-17', '16:30:00', '17:00:00');