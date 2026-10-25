"""app/models.py
Flask-SQLAlchemy database models for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (section 8):
- users: id (PK), name, email (unique, lowercase), password_hash, created_at.
- ads: ad_id (PK, 64-character hash), snippet (first 200 characters), full_text,
       ai_label, ai_probability, model_used, first_checked_at, check_count.
- votes: id (PK), user_id (FK), ad_id (FK), vote ("fake" or "genuine"),
         created_at, updated_at, UNIQUE(user_id, ad_id).
- ratings: id (PK), user_id (FK), ad_id (FK), stars (1 to 5), comment (max 200, optional),
           approved (boolean, default false), created_at, UNIQUE(user_id, ad_id).
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """User account model for DAR."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    votes = db.relationship("Vote", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    ratings = db.relationship("Rating", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Ad(db.Model):
    """Analyzed job advertisement storage."""
    __tablename__ = "ads"

    # ad_id is the 64-character SHA-256 hash of normalized ad text
    ad_id = db.Column(db.String(64), primary_key=True)
    snippet = db.Column(db.String(200), nullable=False)
    full_text = db.Column(db.Text, nullable=False)
    ai_label = db.Column(db.String(20), nullable=False)
    ai_probability = db.Column(db.Float, nullable=False)
    model_used = db.Column(db.String(20), nullable=False, default="lr")
    first_checked_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    check_count = db.Column(db.Integer, default=1, nullable=False)

    # Relationships
    votes = db.relationship("Vote", backref="ad", cascade="all, delete-orphan", lazy="dynamic")
    ratings = db.relationship("Rating", backref="ad", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Ad {self.ad_id[:12]} check_count={self.check_count}>"


class Vote(db.Model):
    """Community authenticity vote (fake or genuine)."""
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ad_id = db.Column(db.String(64), db.ForeignKey("ads.ad_id", ondelete="CASCADE"), nullable=False, index=True)
    vote = db.Column(db.String(10), nullable=False)  # "fake" or "genuine"
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "ad_id", name="uq_user_ad_vote"),
    )

    def __repr__(self) -> str:
        return f"<Vote user={self.user_id} ad={self.ad_id[:12]} vote={self.vote}>"


class Rating(db.Model):
    """User rating and review of DAR analysis quality."""
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ad_id = db.Column(db.String(64), db.ForeignKey("ads.ad_id", ondelete="CASCADE"), nullable=False, index=True)
    stars = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.String(200), nullable=True)  # optional, max 200
    approved = db.Column(db.Boolean, default=False, nullable=False)  # owner approved for home page
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "ad_id", name="uq_user_ad_rating"),
    )

    def __repr__(self) -> str:
        return f"<Rating user={self.user_id} ad={self.ad_id[:12]} stars={self.stars} approved={self.approved}>"
