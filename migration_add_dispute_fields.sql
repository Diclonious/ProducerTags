-- Database migration script to add new columns to orders table
-- Run this script in your MySQL database

ALTER TABLE orders 
ADD COLUMN request_type VARCHAR(50) NULL,
ADD COLUMN request_message TEXT NULL,
ADD COLUMN cancellation_reason VARCHAR(100) NULL,
ADD COLUMN cancellation_message TEXT NULL,
ADD COLUMN extension_days INT NULL,
ADD COLUMN extension_reason TEXT NULL,
ADD COLUMN requested_by_admin VARCHAR(10) NULL;
