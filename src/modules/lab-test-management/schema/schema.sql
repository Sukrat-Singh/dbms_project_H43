-- schema/schema.sql
-- Schema for Module 43: Lab Test Management
-- Run: mysql> SOURCE schema.sql;

-- Drop in reverse order to avoid FK problems (useful when re-running)
DROP TABLE IF EXISTS Alerts;
DROP TABLE IF EXISTS Turnaround;
DROP TABLE IF EXISTS LabResult;
DROP TABLE IF EXISTS OrderTest;
DROP TABLE IF EXISTS LabOrder;
DROP TABLE IF EXISTS LabTest;
DROP TABLE IF EXISTS Preparation;
DROP TABLE IF EXISTS Patient;

-- Patients
CREATE TABLE Patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    date_of_birth DATE,
    gender ENUM('Male','Female','Other') DEFAULT 'Other',
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Preparation instructions for tests
CREATE TABLE Preparation (
    preparation_id INT AUTO_INCREMENT PRIMARY KEY,
    instructions TEXT,
    fasting_required BOOLEAN DEFAULT FALSE,
    special_handling VARCHAR(200)
);

-- Lab test catalog
CREATE TABLE LabTest (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    test_name VARCHAR(150) NOT NULL,
    category VARCHAR(80),
    cost DECIMAL(10,2) DEFAULT 0.00,
    normal_range VARCHAR(80),
    is_numeric BOOLEAN DEFAULT TRUE,
    expected_turnaround_minutes INT DEFAULT 1440, -- default 24 hours
    preparation_id INT,
    FOREIGN KEY (preparation_id) REFERENCES Preparation(preparation_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- A lab order (placed for a patient)
CREATE TABLE LabOrder (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    ordered_by VARCHAR(120),    -- doctor or department
    status ENUM('Ordered','Collected','In Progress','Completed','Cancelled') DEFAULT 'Ordered',
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Link table: which tests are included in an order
CREATE TABLE OrderTest (
    order_test_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    test_id INT NOT NULL,
    sample_collected BOOLEAN DEFAULT FALSE,
    sample_collected_at DATETIME,
    result_status ENUM('Pending','Reported','Cancelled') DEFAULT 'Pending',
    CONSTRAINT fk_ot_order FOREIGN KEY (order_id) REFERENCES LabOrder(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ot_test FOREIGN KEY (test_id) REFERENCES LabTest(test_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Results for each ordered test (one-to-one with order_test_id, can have multiple revisions if you want;
-- this implementation keeps one result record per order_test by convention)
CREATE TABLE LabResult (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    order_test_id INT NOT NULL,
    result_value VARCHAR(255),
    numeric_value DOUBLE NULL,   -- store numeric representation when available
    unit VARCHAR(30),
    flag ENUM('Normal','High','Low','Critical','Unknown') DEFAULT 'Unknown',
    result_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    reported_by VARCHAR(120),
    remarks TEXT,
    CONSTRAINT fk_lr_ot FOREIGN KEY (order_test_id) REFERENCES OrderTest(order_test_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Turnaround tracking
CREATE TABLE Turnaround (
    turnaround_id INT AUTO_INCREMENT PRIMARY KEY,
    order_test_id INT NOT NULL,
    collection_time DATETIME NOT NULL,
    report_time DATETIME NOT NULL,
    time_taken_minutes INT, -- to be computed by trigger
    CONSTRAINT fk_ta_ot FOREIGN KEY (order_test_id) REFERENCES OrderTest(order_test_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Alerts table for critical events (used by triggers)
CREATE TABLE Alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    order_test_id INT,
    alert_type VARCHAR(80),
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_alert_ot FOREIGN KEY (order_test_id) REFERENCES OrderTest(order_test_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Indexes to speed queries
CREATE INDEX idx_order_patient ON LabOrder(patient_id);
CREATE INDEX idx_ot_order ON OrderTest(order_id);
CREATE INDEX idx_ot_test ON OrderTest(test_id);
CREATE INDEX idx_result_ot ON LabResult(order_test_id);
CREATE INDEX idx_turnaround_ot ON Turnaround(order_test_id);

-- SAMPLE DATA (optional quick dataset to test queries)
INSERT INTO Patient (name, date_of_birth, gender, phone)
VALUES
('Rahul Sharma', '1981-04-12', 'Male', '9876543210'),
('Anita Verma', '1995-07-03', 'Female', '9123456780');

INSERT INTO Preparation (instructions, fasting_required, special_handling)
VALUES
('No food 8 hours prior; water allowed', TRUE, 'Store sample at 4C'),
('No restrictions', FALSE, NULL);

INSERT INTO LabTest (test_name, category, cost, normal_range, is_numeric, expected_turnaround_minutes, preparation_id)
VALUES
('Complete Blood Count (CBC)', 'Hematology', 250.00, 'WBC:4-11 x10^3/uL', TRUE, 180, 2),
('Fasting Blood Sugar', 'Biochemistry', 150.00, '70-100 mg/dL', TRUE, 240, 1),
('Liver Function Test (LFT) Panel', 'Biochemistry', 500.00, 'AST:10-40 U/L', TRUE, 720, 2);

-- Example order + order tests to try things quickly
INSERT INTO LabOrder (patient_id, ordered_by, status, notes) VALUES
(1,'Dr. Gupta','Ordered','Routine check'),
(2,'Dr. Mehra','Ordered','Suspected infection');

INSERT INTO OrderTest (order_id, test_id) VALUES
(1,1),(1,2),(2,1);

-- You can insert a LabResult and Turnaround later with the provided triggers/procedures.