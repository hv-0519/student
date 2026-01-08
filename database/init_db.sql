-- Enable foreign key enforcement (MANDATORY in SQLite)
PRAGMA foreign_keys = ON;

--------------------------------------------------
-- USERS
--------------------------------------------------
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'admin')),
    email TEXT,
    contact_no TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users ADD COLUMN is_temp_password INTEGER DEFAULT 1;


--------------------------------------------------
-- EXAMS
--------------------------------------------------
CREATE TABLE exams (
    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    total_marks INTEGER NOT NULL CHECK (total_marks > 0),
    max_attempts INTEGER NOT NULL DEFAULT 3 CHECK (max_attempts > 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--------------------------------------------------
-- QUESTIONS
--------------------------------------------------
CREATE TABLE questions (
    que_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
    wrong_answer_explanation TEXT,
    marks INTEGER NOT NULL CHECK (marks > 0),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

--------------------------------------------------
-- EXAM ATTEMPTS
--------------------------------------------------
CREATE TABLE exam_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 3),
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

--------------------------------------------------
-- RESPONSES
--------------------------------------------------
CREATE TABLE responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    que_id INTEGER NOT NULL,
    selected_option TEXT CHECK (selected_option IN ('A', 'B', 'C', 'D')),
    is_correct INTEGER CHECK (is_correct IN (0, 1)),
    time_spent_secs INTEGER CHECK (time_spent_secs >= 0),
    ans_changed_cnt INTEGER NOT NULL DEFAULT 0 CHECK (ans_changed_cnt >= 0),
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(attempt_id),
    FOREIGN KEY (que_id) REFERENCES questions(que_id)
);

--------------------------------------------------
-- BEHAVIOR LOGS
--------------------------------------------------
CREATE TABLE behavior_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'tab_switch',
            'question_navigation',
            'visibility_hidden',
            'idle',
            'other'
        )
    ),
    event_value TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(attempt_id)
);

--------------------------------------------------
-- RISK ANALYSIS (ML OUTPUT)
--------------------------------------------------
CREATE TABLE risk_analysis (
    risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    explanation TEXT NOT NULL,
    model_version TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(attempt_id)
);

--------------------------------------------------
-- STUDENT_PROFILES
--------------------------------------------------

CREATE TABLE student_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    contact_no TEXT,

    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    date_of_birth DATE,

    address TEXT,
    photo_path TEXT,

    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


--------------------------------------------------
-- INDEXES (Performance + Analytics + ML)
--------------------------------------------------
CREATE INDEX idx_exam_attempts_user_exam
ON exam_attempts(user_id, exam_id);

CREATE INDEX idx_responses_attempt
ON responses(attempt_id);

CREATE INDEX idx_behavior_attempt
ON behavior_logs(attempt_id);

CREATE INDEX idx_behavior_event
ON behavior_logs(event_type);

CREATE INDEX idx_risk_attempt
ON risk_analysis(attempt_id);
