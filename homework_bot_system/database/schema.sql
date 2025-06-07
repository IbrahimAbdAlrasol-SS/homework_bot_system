-- Create database with UTF-8 support
CREATE DATABASE homework_bot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE homework_bot_db;

-- Assignment files table
CREATE TABLE IF NOT EXISTS assignment_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    assignment_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    INDEX idx_assignment_id (assignment_id)
);

-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254),
    telegram_id BIGINT UNIQUE NOT NULL,
    section_id INT,
    role ENUM('super_admin', 'section_admin', 'student') DEFAULT 'student',
    personality ENUM('serious', 'friendly', 'motivator', 'sarcastic') DEFAULT 'friendly',
    points INT DEFAULT 0,
    penalty_counter INT DEFAULT 0,
    excellence_points INT DEFAULT 0,
    submission_streak INT DEFAULT 0,
    is_muted BOOLEAN DEFAULT FALSE,
    profile_photo_url VARCHAR(500),
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active',
    is_active BOOLEAN DEFAULT TRUE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_section_id (section_id),
    INDEX idx_role (role),
    INDEX idx_status (status),
    INDEX idx_points (points)
);

-- Sections table
CREATE TABLE sections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    study_type ENUM('morning', 'evening') NOT NULL,
    admin_id INT,
    telegram_group_id BIGINT,
    storage_group_id BIGINT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_study_type (study_type),
    INDEX idx_admin_id (admin_id),
    INDEX idx_active (is_active)
);

-- Assignments table
CREATE TABLE assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL,
    section_id INT NOT NULL,
    created_by INT NOT NULL,
    deadline TIMESTAMP NOT NULL,
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('draft', 'published', 'closed') DEFAULT 'draft',
    points_value INT NOT NULL DEFAULT 10,
    excellence_points INT DEFAULT 5,
    penalty_points INT DEFAULT 5,
    max_submissions INT NOT NULL DEFAULT 1,
    allow_late_submission BOOLEAN DEFAULT FALSE,
    late_penalty_percentage INT DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    telegram_message_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_section_status (section_id, status),
    INDEX idx_deadline (deadline),
    INDEX idx_priority (priority),
    INDEX idx_created_by (created_by),
    INDEX idx_subject (subject),
    
    CONSTRAINT chk_points_value_positive CHECK (points_value > 0),
    CONSTRAINT chk_max_submissions_positive CHECK (max_submissions > 0)
);

-- Submissions table
CREATE TABLE submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    telegram_message_id BIGINT,
    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    admin_review_notes TEXT,
    reviewed_by INT,
    review_date TIMESTAMP NULL,
    points_earned INT DEFAULT 0,
    is_late BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_submission (assignment_id, student_id),
    INDEX idx_student_status (student_id, status),
    INDEX idx_assignment_status (assignment_id, status)
);

-- Other tables remain unchanged...
-- Badges table
CREATE TABLE badges (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    points_value INT DEFAULT 0,
    type ENUM('speed', 'consistency', 'excellence', 'help', 'achievement') NOT NULL,
    requirements JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (type)
);

-- User badges table
CREATE TABLE user_badges (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    badge_id INT NOT NULL,
    earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assignment_id INT NULL,
    points_awarded INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE SET NULL,
    UNIQUE KEY unique_user_badge (user_id, badge_id, assignment_id),
    INDEX idx_user_earned (user_id, earned_date)
);

-- Competitions table
CREATE TABLE competitions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    type ENUM('individual', 'section', 'study_type', 'global') NOT NULL,
    period_type ENUM('weekly', 'monthly', 'semester') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('upcoming', 'active', 'completed', 'cancelled') DEFAULT 'upcoming',
    winner_id INT NULL,
    winner_type ENUM('user', 'section', 'study_type') NULL,
    prize_points INT DEFAULT 0,
    rules JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type_status (type, status),
    INDEX idx_dates (start_date, end_date)
);

-- Daily statistics table
CREATE TABLE daily_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    section_id INT,
    date DATE NOT NULL,
    assignments_submitted INT DEFAULT 0,
    assignments_late INT DEFAULT 0,
    assignments_missed INT DEFAULT 0,
    total_points_earned INT DEFAULT 0,
    average_submission_time DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (user_id, date),
    INDEX idx_section_date (section_id, date)
);

-- Complaints table
CREATE TABLE complaints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    assignment_id INT NULL,
    type ENUM('penalty', 'grade', 'technical', 'unfair_treatment', 'other') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('open', 'under_review', 'resolved', 'rejected') DEFAULT 'open',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    admin_response TEXT NULL,
    resolved_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE SET NULL,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_student_status (student_id, status),
    INDEX idx_type_priority (type, priority)
);

-- System settings table
CREATE TABLE system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    key_name VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50),
    data_type ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
    is_public BOOLEAN DEFAULT FALSE,
    updated_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_category (category)
);

-- Activity logs table
CREATE TABLE activity_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_action (user_id, action),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created_at (created_at)
);

-- Bot sessions table
CREATE TABLE bot_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_data JSON,
    current_state VARCHAR(100),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_expires (user_id, expires_at)
);

-- Notifications table
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    scheduled_at TIMESTAMP NULL,
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    extra_data JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_notification_type (notification_type),
    INDEX idx_scheduled_at (scheduled_at)
);

-- Rate limiting table
CREATE TABLE rate_limits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    identifier VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    count INT DEFAULT 1,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE KEY unique_identifier_action (identifier, action),
    INDEX idx_expires (expires_at)
);

-- Update constraints
ALTER TABLE users ADD CONSTRAINT chk_points_positive CHECK (points >= 0);
ALTER TABLE users ADD CONSTRAINT chk_penalty_positive CHECK (penalty_counter >= 0);

-- Set default values
UPDATE assignments SET subject = 'General' WHERE subject IS NULL OR subject = '';
UPDATE assignments SET max_submissions = 1 WHERE max_submissions IS NULL OR max_submissions = 0;
UPDATE assignments SET late_penalty_percentage = 50 WHERE late_penalty_percentage IS NULL;

COMMIT;