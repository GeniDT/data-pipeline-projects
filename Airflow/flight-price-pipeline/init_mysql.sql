CREATE DATABASE IF NOT EXISTS flight_staging;
CREATE USER IF NOT EXISTS 'flight_user'@'%' IDENTIFIED BY 'flight_pass';
GRANT ALL PRIVILEGES ON flight_staging.* TO 'flight_user'@'%';
FLUSH PRIVILEGES;