"""
SQLAlchemy ORM Models — MySQL 8.0
==================================
All entities: courts, cases, judges, parties, lawyers, acts, hearings,
citations, legal_sections, judgments, audit_log
Junction tables: case_judges, case_parties, case_lawyers, case_acts,
case_citations (self-referencing), case_sections
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, ForeignKey,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Court(Base):
    __tablename__ = 'courts'
    court_id = Column(Integer, primary_key=True, autoincrement=True)
    court_name = Column(String(255), nullable=False, unique=True)
    court_level = Column(String(50))
    state = Column(String(100))
    country = Column(String(100), default='India')
    created_at = Column(DateTime, default=datetime.utcnow)
    cases = relationship('Case', back_populates='court')


class Case(Base):
    __tablename__ = 'cases'
    case_id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(100))
    case_title = Column(String(500))
    court_id = Column(Integer, ForeignKey('courts.court_id', ondelete='SET NULL'))
    judgment_date = Column(Date)
    case_type = Column(String(100))
    case_category = Column(String(50))
    verdict = Column(String(50))
    bench_strength = Column(Integer)
    bench_type = Column(String(50))
    word_count = Column(Integer)
    summary = Column(Text)
    raw_text = Column(Text)
    file_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    court = relationship('Court', back_populates='cases')
    judges = relationship('CaseJudge', back_populates='case', cascade='all, delete-orphan')
    parties = relationship('CaseParty', back_populates='case', cascade='all, delete-orphan')
    lawyers_rel = relationship('CaseLawyer', back_populates='case', cascade='all, delete-orphan')
    acts_rel = relationship('CaseAct', back_populates='case', cascade='all, delete-orphan')
    sections = relationship('CaseSection', back_populates='case', cascade='all, delete-orphan')
    citations = relationship('Citation', back_populates='case')
    hearings = relationship('Hearing', back_populates='case', cascade='all, delete-orphan')
    judgment = relationship('Judgment', back_populates='case', uselist=False, cascade='all, delete-orphan')
    citing = relationship('CaseCitation', foreign_keys='CaseCitation.source_case_id', back_populates='source_case')
    cited_by = relationship('CaseCitation', foreign_keys='CaseCitation.target_case_id', back_populates='target_case')


class Judge(Base):
    __tablename__ = 'judges'
    judge_id = Column(Integer, primary_key=True, autoincrement=True)
    judge_name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cases = relationship('CaseJudge', back_populates='judge')


class CaseJudge(Base):
    __tablename__ = 'case_judges'
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), primary_key=True)
    judge_id = Column(Integer, ForeignKey('judges.judge_id', ondelete='CASCADE'), primary_key=True)
    role = Column(String(50), default='bench')
    case = relationship('Case', back_populates='judges')
    judge = relationship('Judge', back_populates='cases')


class Party(Base):
    __tablename__ = 'parties'
    party_id = Column(Integer, primary_key=True, autoincrement=True)
    party_name = Column(String(500), nullable=False)
    party_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    cases = relationship('CaseParty', back_populates='party')


class CaseParty(Base):
    __tablename__ = 'case_parties'
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.party_id', ondelete='CASCADE'), primary_key=True)
    role = Column(String(50), nullable=False, primary_key=True)
    case = relationship('Case', back_populates='parties')
    party = relationship('Party', back_populates='cases')


class Lawyer(Base):
    __tablename__ = 'lawyers'
    lawyer_id = Column(Integer, primary_key=True, autoincrement=True)
    lawyer_name = Column(String(255), nullable=False, unique=True)
    designation = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    cases = relationship('CaseLawyer', back_populates='lawyer')


class CaseLawyer(Base):
    __tablename__ = 'case_lawyers'
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), primary_key=True)
    lawyer_id = Column(Integer, ForeignKey('lawyers.lawyer_id', ondelete='CASCADE'), primary_key=True)
    role = Column(String(50), default='counsel')
    side = Column(String(50))
    case = relationship('Case', back_populates='lawyers_rel')
    lawyer = relationship('Lawyer', back_populates='cases')


class Act(Base):
    __tablename__ = 'acts'
    act_id = Column(Integer, primary_key=True, autoincrement=True)
    act_name = Column(String(500), nullable=False, unique=True)
    act_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    sections = relationship('LegalSection', back_populates='act')
    cases = relationship('CaseAct', back_populates='act')


class CaseAct(Base):
    __tablename__ = 'case_acts'
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), primary_key=True)
    act_id = Column(Integer, ForeignKey('acts.act_id', ondelete='CASCADE'), primary_key=True)
    section_ref = Column(String(255))
    case = relationship('Case', back_populates='acts_rel')
    act = relationship('Act', back_populates='cases')


class LegalSection(Base):
    __tablename__ = 'legal_sections'
    section_id = Column(Integer, primary_key=True, autoincrement=True)
    act_id = Column(Integer, ForeignKey('acts.act_id', ondelete='SET NULL'))
    section_name = Column(String(255), nullable=False)
    description = Column(Text)
    __table_args__ = (UniqueConstraint('act_id', 'section_name', name='uq_section'),)
    act = relationship('Act', back_populates='sections')
    cases = relationship('CaseSection', back_populates='section')


class CaseSection(Base):
    __tablename__ = 'case_sections'
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), primary_key=True)
    section_id = Column(Integer, ForeignKey('legal_sections.section_id', ondelete='CASCADE'), primary_key=True)
    case = relationship('Case', back_populates='sections')
    section = relationship('LegalSection', back_populates='cases')


class Citation(Base):
    __tablename__ = 'citations'
    citation_id = Column(Integer, primary_key=True, autoincrement=True)
    citation_text = Column(String(255), nullable=False)
    citation_type = Column(String(20))
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='SET NULL'))
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship('Case', back_populates='citations')


class CaseCitation(Base):
    """Self-referencing many-to-many for citation graph."""
    __tablename__ = 'case_citations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False)
    target_case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False)
    citation_strength = Column(Integer, default=1)
    __table_args__ = (UniqueConstraint('source_case_id', 'target_case_id', name='uq_case_citation'),)
    source_case = relationship('Case', foreign_keys=[source_case_id], back_populates='citing')
    target_case = relationship('Case', foreign_keys=[target_case_id], back_populates='cited_by')


class Hearing(Base):
    __tablename__ = 'hearings'
    hearing_id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False)
    hearing_date = Column(Date)
    hearing_type = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship('Case', back_populates='hearings')


class Judgment(Base):
    __tablename__ = 'judgments'
    judgment_id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False)
    judgment_text = Column(Text)
    final_decision = Column(String(100))
    word_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship('Case', back_populates='judgment')


class AuditLog(Base):
    __tablename__ = 'audit_log'
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100))
    record_id = Column(Integer)
    action = Column(String(20))
    old_value = Column(Text)
    new_value = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(100))
