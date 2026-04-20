from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://awesome:awesome@localhost:5432/awesome_ranked")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    html_url = Column(String, nullable=False)
    github_default_branch = Column(String, nullable=True)
    repo_created_at = Column(DateTime(timezone=True), nullable=True)
    tracked = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('owner', 'name', name='uix_owner_name'),
    )
    
    snapshots = relationship("RepositorySnapshot", back_populates="repository", order_by="desc(RepositorySnapshot.scraped_at)")


class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    contributors_count_approx = Column(Integer, nullable=True)
    contributors_sample_size = Column(Integer, nullable=True)
    commit_count_default_branch = Column(Integer, nullable=True)
    last_commit_date = Column(DateTime(timezone=True), nullable=True)
    last_commit_sha = Column(String, nullable=True)
    
    __table_args__ = (
        Index('idx_repo_scraped_at', 'repository_id', 'scraped_at'),
        Index('idx_scraped_at', 'scraped_at'),
    )
    
    repository = relationship("Repository", back_populates="snapshots")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    # For local/dev deployments we create tables automatically.
    # If you later want migrations, replace this with Alembic.
    Base.metadata.create_all(bind=engine)
