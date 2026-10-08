-- Student Result Analysis - MySQL schema
-- Run:  mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS student_result_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE student_result_db;

CREATE TABLE IF NOT EXISTS students (
    student_id  INT AUTO_INCREMENT PRIMARY KEY,
    roll_no     VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(120) NULL UNIQUE,
    department  VARCHAR(100) NOT NULL,
    year        TINYINT      NOT NULL DEFAULT 1,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subjects (
    subject_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    max_marks   INT          NOT NULL DEFAULT 100
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS marks (
    mark_id     INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    subject_id  INT NOT NULL,
    marks       DECIMAL(5,2) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_marks_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id)
        REFERENCES subjects(subject_id) ON DELETE CASCADE,
    -- one mark per student per subject (re-entering updates it)
    CONSTRAINT uq_student_subject UNIQUE (student_id, subject_id),
    CONSTRAINT chk_marks_nonneg CHECK (marks >= 0)
) ENGINE=InnoDB;

-- Default subjects (edit freely)
INSERT IGNORE INTO subjects (name, max_marks) VALUES
    ('Python Programming', 100),
    ('Database Management Systems', 100),
    ('Data Structures', 100),
    ('Web Technologies', 100),
    ('Mathematics', 100);
