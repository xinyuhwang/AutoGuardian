-- Runs once, when the database volume is first created.
-- Separate database for automated tests so they never touch development data.
CREATE DATABASE autoguardian_test OWNER autoguardian;
