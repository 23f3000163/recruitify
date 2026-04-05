"""
models.py — SQLAlchemy ORM Models for Recruitify Placement Portal

Table creation order (dependency-safe for SQLite):
    User -> Admin / Student / Company -> PlacementDrive ->
    Application -> Interview / PlacementOffer -> ActivityLog / Notification

Key design decisions:
    • SQLite PRAGMA foreign_keys=ON enforced via engine-level event listener
    • All ENUMs carry explicit `name=` to avoid unnamed CHECK constraints on SQLite
    • 1:1 relationships use lazy='joined' to eliminate N+1 queries
    • Every model exposes a to_dict() helper for JSON serialisation
    • Passwords are hashed with werkzeug (scrypt / pbkdf2)
    • All timestamps are timezone-aware via datetime.now(timezone.utc)
"""

from datetime import date, datetime, timezone
from uuid import uuid4

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.engine import Engine
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# SQLite foreign-key enforcement
# ---------------------------------------------------------------------------
# SQLite ignores ON DELETE CASCADE unless PRAGMA foreign_keys is turned on
# for every single connection.  The listener below guarantees that.
@event.listens_for(Engine, "connect")
def _enable_sqlite_fks(dbapi_connection, connection_record):
    """Enable foreign-key constraint enforcement for every SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# =========================================================================
# Helper — timezone-aware "now" default
# =========================================================================
def _utcnow():
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _new_job_id():
    """Return a UUID string used as background job primary key."""
    return str(uuid4())


# =========================================================================
# 1. USER  (base authentication table)
# =========================================================================
class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.Enum("admin", "company", "student", name="role_enum"),
        nullable=False,
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
    last_login = db.Column(db.DateTime, nullable=True)

    # --- 1:1 relationships (lazy='joined' avoids N+1) ---
    admin = db.relationship(
        "Admin", back_populates="user", uselist=False, lazy="joined"
    )
    student = db.relationship(
        "Student",
        back_populates="user",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )
    company = db.relationship(
        "Company",
        back_populates="user",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )

    # --- 1:N relationships ---
    activity_logs = db.relationship(
        "ActivityLog", back_populates="user", lazy="dynamic"
    )
    notifications_received = db.relationship(
        "Notification",
        foreign_keys="Notification.recipient_id",
        back_populates="recipient",
        lazy="dynamic",
    )
    notifications_sent = db.relationship(
        "Notification",
        foreign_keys="Notification.sender_id",
        back_populates="sender",
        lazy="dynamic",
    )

    # --- Password helpers ---
    def set_password(self, password: str) -> None:
        """Hash *password* and store it in ``password_hash``."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return ``True`` if *password* matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    # --- Serialisation ---
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            # password_hash intentionally excluded
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username!r} ({self.role})>"


# =========================================================================
# 2. ADMIN
# =========================================================================
class Admin(db.Model):
    __tablename__ = "admin"

    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    can_approve_companies = db.Column(db.Boolean, default=True, nullable=False)
    can_approve_drives = db.Column(db.Boolean, default=True, nullable=False)
    can_manage_students = db.Column(db.Boolean, default=True, nullable=False)
    can_manage_companies = db.Column(db.Boolean, default=True, nullable=False)
    can_view_reports = db.Column(db.Boolean, default=True, nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    # --- relationship back to User ---
    user = db.relationship("User", back_populates="admin", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "admin_id": self.admin_id,
            "user_id": self.user_id,
            "can_approve_companies": self.can_approve_companies,
            "can_approve_drives": self.can_approve_drives,
            "can_manage_students": self.can_manage_students,
            "can_manage_companies": self.can_manage_companies,
            "can_view_reports": self.can_view_reports,
            "designation": self.designation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Admin {self.admin_id} user_id={self.user_id}>"


# =========================================================================
# 3. STUDENT
# =========================================================================
class Student(db.Model):
    __tablename__ = "student"

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    roll_number = db.Column(db.String(30), unique=True, nullable=True)
    college_name = db.Column(db.String(200), nullable=True)
    branch = db.Column(
        db.Enum("CSE", "ECE", "MECH", "EE", "OTHER", name="branch_enum"),
        nullable=True,
    )
    year = db.Column(db.Integer, nullable=True)  # 1-4
    cgpa = db.Column(db.Float, nullable=True)
    profile_completed = db.Column(db.Boolean, default=False, nullable=False)
    resume_url = db.Column(db.String(500), nullable=True)
    resume_uploaded_at = db.Column(db.DateTime, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    experience_summary = db.Column(db.Text, nullable=True)
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    blacklist_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # --- relationships ---
    user = db.relationship("User", back_populates="student", lazy="joined")
    applications = db.relationship(
        "Application",
        back_populates="student",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "user_id": self.user_id,
            "roll_number": self.roll_number,
            "college_name": self.college_name,
            "branch": self.branch,
            "year": self.year,
            "cgpa": self.cgpa,
            "profile_completed": self.profile_completed,
            "resume_url": self.resume_url,
            "resume_uploaded_at": (
                self.resume_uploaded_at.isoformat()
                if self.resume_uploaded_at
                else None
            ),
            "phone": self.phone,
            "skills": self.skills,
            "experience_summary": self.experience_summary,
            "is_blacklisted": self.is_blacklisted,
            "blacklist_reason": self.blacklist_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Student user_id={self.user_id}>"


# =========================================================================
# 4. COMPANY
# =========================================================================
class Company(db.Model):
    __tablename__ = "company"

    company_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    company_name = db.Column(db.String(200), unique=True, nullable=False)
    industry = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(160), nullable=True)
    website = db.Column(db.String(300), nullable=True)
    hr_contact_name = db.Column(db.String(120), nullable=False)
    hr_contact_email = db.Column(db.String(120), unique=True, nullable=False)
    hr_contact_phone = db.Column(db.String(20), nullable=False)
    company_description = db.Column(db.Text, nullable=True)
    approval_status = db.Column(
        db.Enum("pending", "approved", "rejected", name="approval_status_enum"),
        default="pending",
        nullable=False,
    )
    approval_date = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(
        db.Integer,
        db.ForeignKey("admin.admin_id"),
        nullable=True,
    )
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    blacklist_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # --- relationships ---
    user = db.relationship("User", back_populates="company", lazy="joined")
    approver = db.relationship("Admin", foreign_keys=[approved_by], lazy="joined")
    placement_drives = db.relationship(
        "PlacementDrive",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "user_id": self.user_id,
            "company_name": self.company_name,
            "industry": self.industry,
            "location": self.location,
            "website": self.website,
            "hr_contact_name": self.hr_contact_name,
            "hr_contact_email": self.hr_contact_email,
            "hr_contact_phone": self.hr_contact_phone,
            "company_description": self.company_description,
            "approval_status": self.approval_status,
            "approval_date": (
                self.approval_date.isoformat() if self.approval_date else None
            ),
            "approved_by": self.approved_by,
            "is_blacklisted": self.is_blacklisted,
            "blacklist_reason": self.blacklist_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Company {self.company_name!r}>"


# =========================================================================
# 5. PLACEMENT_DRIVE
# =========================================================================
# Represents a job/placement drive created by company

class PlacementDrive(db.Model):
    __tablename__ = "placement_drive"

    drive_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=True)
    experience_required = db.Column(db.String(120), nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    min_cgpa = db.Column(db.Float, nullable=False)
    eligible_branches = db.Column(db.JSON, nullable=False)   # e.g. ["CSE","ECE"]
    eligible_years = db.Column(db.JSON, nullable=False)       # e.g. [3, 4]
    salary_lpa = db.Column(db.Float, nullable=True)
    job_location = db.Column(db.String(200), nullable=True)
    application_deadline = db.Column(db.DateTime, nullable=False)
    interview_mode = db.Column(
        db.Enum("online", "offline", "both", name="drive_interview_mode_enum"),
        nullable=False,
    )
    status = db.Column(
        db.Enum("pending", "approved", "closed", name="drive_status_enum"),
        default="pending",
        nullable=False,
    )
    approval_date = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(
        db.Integer,
        db.ForeignKey("admin.admin_id"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # --- relationships ---
    company = db.relationship("Company", back_populates="placement_drives")
    approver = db.relationship("Admin", foreign_keys=[approved_by], lazy="joined")
    applications = db.relationship(
        "Application",
        back_populates="drive",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    interviews = db.relationship(
        "Interview", back_populates="drive", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "drive_id": self.drive_id,
            "company_id": self.company_id,
            "job_title": self.job_title,
            "job_description": self.job_description,
            "required_skills": self.required_skills,
            "experience_required": self.experience_required,
            "benefits": self.benefits,
            "min_cgpa": self.min_cgpa,
            "eligible_branches": self.eligible_branches,
            "eligible_years": self.eligible_years,
            "salary_lpa": self.salary_lpa,
            "job_location": self.job_location,
            "application_deadline": (
                self.application_deadline.isoformat()
                if self.application_deadline
                else None
            ),
            "interview_mode": self.interview_mode,
            "status": self.status,
            "approval_date": (
                self.approval_date.isoformat() if self.approval_date else None
            ),
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<PlacementDrive {self.job_title!r} drive_id={self.drive_id}>"


# =========================================================================
# 6. APPLICATION
# =========================================================================
class Application(db.Model):
    __tablename__ = "application"
    __table_args__ = (
        UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    application_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.student_id", ondelete="CASCADE"),
        nullable=False,
    )
    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drive.drive_id", ondelete="CASCADE"),
        nullable=False,
    )
    status = db.Column(
        db.Enum(
            "applied",
            "shortlisted",
            "selected",
            "interviewed",
            "rejected",
            "waitlisted",
            name="application_status_enum",
        ),
        default="applied",
        nullable=False,
    )
    application_date = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )
    rejection_reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    # --- relationships ---
    student = db.relationship("Student", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")
    interviews = db.relationship(
        "Interview",
        back_populates="application",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    placement_offer = db.relationship(
        "PlacementOffer",
        back_populates="application",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        company_id = self.drive.company_id if self.drive else None
        applied_at = self.application_date.isoformat() if self.application_date else None
        return {
            "id": self.application_id,
            "application_id": self.application_id,
            "student_id": self.student_id,
            "job_id": self.drive_id,
            "drive_id": self.drive_id,
            "company_id": company_id,
            "status": self.status,
            "applied_at": applied_at,
            "application_date": (
                self.application_date.isoformat()
                if self.application_date
                else None
            ),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "rejection_reason": self.rejection_reason,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<Application {self.application_id} "
            f"student={self.student_id} drive={self.drive_id}>"
        )


# =========================================================================
# 7. INTERVIEW
# =========================================================================
class Interview(db.Model):
    __tablename__ = "interview"

    interview_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    application_id = db.Column(
        db.Integer,
        db.ForeignKey("application.application_id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.company_id"),
        nullable=False,
    )
    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drive.drive_id", ondelete="CASCADE"),
        nullable=False,
    )
    interview_date = db.Column(db.DateTime, nullable=False)
    interview_mode = db.Column(
        db.Enum("online", "offline", name="interview_mode_enum"),
        nullable=False,
    )
    interview_link = db.Column(db.String(500), nullable=True)
    interview_location = db.Column(db.String(300), nullable=True)
    interviewer_name = db.Column(db.String(120), nullable=True)
    result = db.Column(
        db.Enum("pending", "pass", "fail", name="interview_result_enum"),
        default="pending",
        nullable=False,
    )
    feedback = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # --- relationships ---
    application = db.relationship("Application", back_populates="interviews")
    drive = db.relationship("PlacementDrive", back_populates="interviews")
    company = db.relationship("Company", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "interview_id": self.interview_id,
            "application_id": self.application_id,
            "company_id": self.company_id,
            "drive_id": self.drive_id,
            "interview_date": (
                self.interview_date.isoformat() if self.interview_date else None
            ),
            "interview_mode": self.interview_mode,
            "interview_link": self.interview_link,
            "interview_location": self.interview_location,
            "interviewer_name": self.interviewer_name,
            "result": self.result,
            "feedback": self.feedback,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Interview {self.interview_id} result={self.result}>"


# =========================================================================
# 8. PLACEMENT_OFFER
# =========================================================================
class PlacementOffer(db.Model):
    __tablename__ = "placement_offer"

    offer_id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("application.application_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.student_id"),
        nullable=False,
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.company_id"),
        nullable=False,
    )

    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drive.drive_id"),
        nullable=False,
    )

    # --- CORE REQUIRED FIELDS ONLY ---
    salary = db.Column(db.Float, nullable=False)
    position = db.Column(db.String(200), nullable=False)
    joining_date = db.Column(db.Date, nullable=True)

    # --- SIMPLIFIED STATUS ---
    status = db.Column(
        db.Enum("offered", "accepted", "rejected", name="offer_status_enum"),
        default="offered",
        nullable=False,
    )

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    # --- relationships ---
    application = db.relationship("Application", back_populates="placement_offer")
    student = db.relationship("Student", lazy="joined")
    company = db.relationship("Company", lazy="joined")
    drive = db.relationship("PlacementDrive", lazy="joined")

    def to_dict(self):
        return {
            "offer_id": self.offer_id,
            "application_id": self.application_id,
            "student_id": self.student_id,
            "company_id": self.company_id,
            "drive_id": self.drive_id,
            "salary": self.salary,
            "position": self.position,
            "joining_date": (
                self.joining_date.isoformat() if self.joining_date else None
            ),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<PlacementOffer {self.offer_id} student={self.student_id}>"
    

# =========================================================================
# 9. PLACEMENT
# =========================================================================    
class Placement(db.Model):
    __tablename__ = "placement"

    placement_id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.student_id"),
        nullable=False
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.company_id"),
        nullable=False
    )

    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drive.drive_id"),
        nullable=False
    )

    position = db.Column(db.String(200), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    joining_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=_utcnow)

    # relationships
    student = db.relationship("Student", lazy="joined")
    company = db.relationship("Company", lazy="joined")
    drive = db.relationship("PlacementDrive", lazy="joined")

    def to_dict(self):
        return {
            "placement_id": self.placement_id,
            "student_id": self.student_id,
            "company_id": self.company_id,
            "drive_id": self.drive_id,
            "position": self.position,
            "salary": self.salary,
            "joining_date": (
                self.joining_date.isoformat() if self.joining_date else None
            ),
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<Placement id={self.placement_id}, student={self.student_id}, company={self.company_id}>"


# =========================================================================
# 10. ACTIVITY_LOG
# =========================================================================
class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    # --- Basic log table to track user actions in the system ---
    # This helps in understanding what actions users performed
    # (e.g., student applied for a job, admin approved a company)

    log_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=False
    )

    action = db.Column(
        db.String(200),
        nullable=False
    )  
    # Example: "Applied for drive", "Approved company", "Rejected application"

    target = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="info",
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=_utcnow,
        nullable=False
    )

    # --- relationship ---
    user = db.relationship("User", back_populates="activity_logs")

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "actor": self.user.username if self.user else None,
            "action": self.action,
            "target": self.target,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<ActivityLog {self.log_id} user={self.user_id}>"

# =========================================================================
# 11. NOTIFICATION
# =========================================================================
class Notification(db.Model):
    __tablename__ = "notification"

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=False,
    )
    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=True,
    )
    notification_type = db.Column(
        db.Enum("email", "sms", "in_app", name="notification_type_enum"),
        nullable=False,
    )
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_resource_type = db.Column(db.String(100), nullable=True)
    related_resource_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    delivery_status = db.Column(
        db.Enum("pending", "sent", "failed", name="delivery_status_enum"),
        default="pending",
        nullable=False,
    )
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    # --- relationships ---
    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="notifications_received",
    )
    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="notifications_sent",
    )

    def to_dict(self) -> dict:
        return {
            "notification_id": self.notification_id,
            "recipient_id": self.recipient_id,
            "sender_id": self.sender_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "related_resource_type": self.related_resource_type,
            "related_resource_id": self.related_resource_id,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivery_status": self.delivery_status,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Notification {self.notification_id} to={self.recipient_id}>"


# =========================================================================
# 12. BACKGROUND_JOB
# =========================================================================
class BackgroundJob(db.Model):
    __tablename__ = "background_job"

    job_id = db.Column(db.String(36), primary_key=True, default=_new_job_id)
    job_type = db.Column(
        db.Enum(
            "daily_reminder",
            "monthly_report",
            "export_csv",
            "maintenance",
            name="job_type_enum",
        ),
        nullable=False,
    )
    status = db.Column(
        db.Enum(
            "queued",
            "running",
            "completed",
            "failed",
            "cancelled",
            name="job_status_enum",
        ),
        default="queued",
        nullable=False,
    )
    requested_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=True,
    )
    idempotency_key = db.Column(db.String(120), unique=True, nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    result_meta = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    requested_by = db.relationship("User", lazy="joined")
    export_artifacts = db.relationship(
        "ExportArtifact",
        back_populates="job",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "requested_by_user_id": self.requested_by_user_id,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
            "result_meta": self.result_meta,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<BackgroundJob {self.job_id} type={self.job_type} status={self.status}>"


# =========================================================================
# 13. EXPORT_ARTIFACT
# =========================================================================
class ExportArtifact(db.Model):
    __tablename__ = "export_artifact"

    artifact_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(
        db.String(36),
        db.ForeignKey("background_job.job_id", ondelete="CASCADE"),
        nullable=False,
    )
    requested_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=False,
    )
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    content_type = db.Column(db.String(120), nullable=False, default="text/csv")
    file_size_bytes = db.Column(db.Integer, nullable=True)
    status = db.Column(
        db.Enum("pending", "ready", "failed", "expired", name="artifact_status_enum"),
        default="pending",
        nullable=False,
    )
    checksum = db.Column(db.String(128), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    job = db.relationship("BackgroundJob", back_populates="export_artifacts", lazy="joined")
    requested_by = db.relationship("User", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "job_id": self.job_id,
            "requested_by_user_id": self.requested_by_user_id,
            "filename": self.filename,
            "storage_path": self.storage_path,
            "content_type": self.content_type,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "checksum": self.checksum,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ExportArtifact {self.artifact_id} job={self.job_id} status={self.status}>"
