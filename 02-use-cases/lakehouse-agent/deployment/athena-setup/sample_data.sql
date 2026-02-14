-- Sample Health Lakehouse Data Data
-- This file contains realistic sample data for testing row-level access control

-- Sample data for claims table
-- Format: claim_id, user_id, adjuster_user_id, policyholder_name, policyholder_dob, claim_date, claim_amount, claim_type, claim_status, provider_name, provider_npi, diagnosis_code, procedure_code, submitted_date, processed_date, approved_amount, denial_reason, notes, created_by, last_modified_by, last_modified_date

-- Claims for policyholder001@example.com (policyholder: John Doe)
INSERT INTO lakehouse_db.claims VALUES
('CLM-2024-001', 'policyholder001@example.com', 'adjuster001@example.com', 'John Doe', DATE '1985-03-15', DATE '2024-01-10', 1250.00, 'medical', 'approved', 'City Medical Center', '1234567890', 'J06.9', '99213', TIMESTAMP '2024-01-11 09:30:00', TIMESTAMP '2024-01-15 14:20:00', 1000.00, NULL, 'Annual physical examination and lab work', 'policyholder001@example.com', 'adjuster001@example.com', TIMESTAMP '2024-01-15 14:20:00'),
('CLM-2024-002', 'policyholder001@example.com', 'adjuster001@example.com', 'John Doe', DATE '1985-03-15', DATE '2024-02-05', 85.50, 'prescription', 'approved', 'CVS Pharmacy', '9876543210', 'E11.9', '90670', TIMESTAMP '2024-02-05 16:45:00', TIMESTAMP '2024-02-06 10:15:00', 85.50, NULL, 'Diabetes medication - monthly refill', 'policyholder001@example.com', 'adjuster001@example.com', TIMESTAMP '2024-02-06 10:15:00'),
('CLM-2024-003', 'policyholder001@example.com', 'adjuster002@example.com', 'John Doe', DATE '1985-03-15', DATE '2024-02-20', 3500.00, 'hospital', 'in_review', 'General Hospital', '1122334455', 'M54.5', '22612', TIMESTAMP '2024-02-21 08:00:00', NULL, NULL, NULL, 'Emergency room visit for back pain including X-rays', 'policyholder001@example.com', 'adjuster002@example.com', TIMESTAMP '2024-02-21 08:00:00'),
('CLM-2024-004', 'policyholder001@example.com', 'adjuster001@example.com', 'John Doe', DATE '1985-03-15', DATE '2024-03-10', 450.00, 'medical', 'pending', 'Downtown Dental Clinic', '2233445566', 'K02.9', 'D0150', TIMESTAMP '2024-03-11 11:20:00', NULL, NULL, NULL, 'Dental examination and cleaning', 'policyholder001@example.com', 'adjuster001@example.com', TIMESTAMP '2024-03-11 11:20:00');

-- Claims for policyholder002@example.com (policyholder: Jane Smith)
INSERT INTO lakehouse_db.claims VALUES
('CLM-2024-005', 'policyholder002@example.com', 'adjuster002@example.com', 'Jane Smith', DATE '1990-07-22', DATE '2024-01-15', 850.00, 'medical', 'approved', 'Women''s Health Center', '5544332211', 'Z00.00', '99395', TIMESTAMP '2024-01-16 10:00:00', TIMESTAMP '2024-01-18 15:30:00', 680.00, NULL, 'Annual gynecological exam and preventive care', 'policyholder002@example.com', 'adjuster002@example.com', TIMESTAMP '2024-01-18 15:30:00'),
('CLM-2024-006', 'policyholder002@example.com', 'adjuster001@example.com', 'Jane Smith', DATE '1990-07-22', DATE '2024-02-10', 125.00, 'prescription', 'approved', 'Walgreens Pharmacy', '6655443322', 'H10.9', '90680', TIMESTAMP '2024-02-10 13:15:00', TIMESTAMP '2024-02-11 09:00:00', 125.00, NULL, 'Antibiotic prescription for eye infection', 'policyholder002@example.com', 'adjuster001@example.com', TIMESTAMP '2024-02-11 09:00:00'),
('CLM-2024-007', 'policyholder002@example.com', 'adjuster002@example.com', 'Jane Smith', DATE '1990-07-22', DATE '2024-02-25', 12500.00, 'hospital', 'approved', 'St. Mary''s Hospital', '7766554433', 'O80', '59400', TIMESTAMP '2024-02-26 07:30:00', TIMESTAMP '2024-03-05 16:00:00', 10000.00, NULL, 'Childbirth and postpartum care', 'policyholder002@example.com', 'adjuster002@example.com', TIMESTAMP '2024-03-05 16:00:00'),
('CLM-2024-008', 'policyholder002@example.com', 'adjuster001@example.com', 'Jane Smith', DATE '1990-07-22', DATE '2024-03-15', 200.00, 'medical', 'denied', 'Cosmetic Surgery Center', '8877665544', 'Z41.1', '15780', TIMESTAMP '2024-03-16 14:00:00', TIMESTAMP '2024-03-20 11:00:00', 0.00, 'Cosmetic procedures not covered by policy', 'Facial cosmetic procedure', 'policyholder002@example.com', 'adjuster001@example.com', TIMESTAMP '2024-03-20 11:00:00'),
('CLM-2024-009', 'policyholder002@example.com', 'adjuster002@example.com', 'Jane Smith', DATE '1990-07-22', DATE '2024-03-25', 75.00, 'prescription', 'pending', 'Target Pharmacy', '9988776655', 'Z79.890', '90715', TIMESTAMP '2024-03-26 09:45:00', NULL, NULL, NULL, 'Vitamin supplements and prenatal care', 'policyholder002@example.com', 'adjuster002@example.com', TIMESTAMP '2024-03-26 09:45:00');

-- Sample data for users table
INSERT INTO lakehouse_db.users VALUES
('policyholder001@example.com', 'John Doe', 'policyholder', 'Individual', TIMESTAMP '2023-01-15 00:00:00'),
('policyholder002@example.com', 'Jane Smith', 'policyholder', 'Individual', TIMESTAMP '2023-02-20 00:00:00'),
('adjuster001@example.com', 'Michael Johnson', 'adjuster', 'Claims Department', TIMESTAMP '2022-06-01 00:00:00'),
('adjuster002@example.com', 'Sarah Williams', 'adjuster', 'Claims Department', TIMESTAMP '2022-08-15 00:00:00'),
('admin@example.com', 'Admin User', 'admin', 'IT Department', TIMESTAMP '2022-01-01 00:00:00');

-- Note: The actual data insertion for Athena requires CSV files in S3
-- This SQL is for reference and documentation purposes
-- The setup_athena.py script will create proper CSV files and upload them to S3
