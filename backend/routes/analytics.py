"""
Analytics API Routes — MySQL compatible
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract, case as sql_case, text

from backend.database.connection import get_db
from backend.models.models import (
    Case, Judge, CaseJudge, Citation, Act, CaseAct,
    LegalSection, CaseSection, Court, Party, CaseParty,
    Lawyer, CaseLawyer
)

router = APIRouter()


@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary statistics."""
    return {
        "total_cases": db.query(func.count(Case.case_id)).scalar(),
        "total_judges": db.query(func.count(Judge.judge_id)).scalar(),
        "total_citations": db.query(func.count(Citation.citation_id)).scalar(),
        "total_acts": db.query(func.count(Act.act_id)).scalar(),
        "total_parties": db.query(func.count(Party.party_id)).scalar(),
        "total_courts": db.query(func.count(Court.court_id)).scalar(),
        "total_lawyers": db.query(func.count(Lawyer.lawyer_id)).scalar(),
        "accepted_cases": db.query(func.count(Case.case_id)).filter(Case.verdict == 'Accepted').scalar(),
        "rejected_cases": db.query(func.count(Case.case_id)).filter(Case.verdict == 'Rejected').scalar(),
        "other_cases": db.query(func.count(Case.case_id)).filter(
            Case.verdict != 'Accepted', Case.verdict != 'Rejected',
            Case.verdict.isnot(None), Case.verdict != ''
        ).scalar(),
    }


@router.get("/judges")
def judge_analytics(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Top judges by case count with verdict breakdown."""
    results = (
        db.query(
            Judge.judge_id,
            Judge.judge_name,
            func.count(CaseJudge.case_id).label('total_cases'),
            func.sum(sql_case((Case.verdict == 'Accepted', 1), else_=0)).label('accepted'),
            func.sum(sql_case((Case.verdict == 'Rejected', 1), else_=0)).label('rejected'),
            func.round(func.avg(Case.word_count)).label('avg_length'),
        )
        .join(CaseJudge, Judge.judge_id == CaseJudge.judge_id)
        .join(Case, CaseJudge.case_id == Case.case_id)
        .group_by(Judge.judge_id, Judge.judge_name)
        .order_by(desc('total_cases'))
        .limit(limit)
        .all()
    )

    return {
        "data": [
            {
                "judge_id": r.judge_id,
                "judge_name": r.judge_name,
                "total_cases": r.total_cases,
                "accepted": int(r.accepted or 0),
                "rejected": int(r.rejected or 0),
                "avg_judgment_length": int(r.avg_length or 0),
            }
            for r in results
        ]
    }


@router.get("/acts")
def act_analytics(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Most referenced acts via case_acts junction."""
    results = (
        db.query(
            Act.act_id,
            Act.act_name,
            func.count(CaseAct.case_id).label('case_count'),
        )
        .join(CaseAct, Act.act_id == CaseAct.act_id)
        .group_by(Act.act_id, Act.act_name)
        .order_by(desc('case_count'))
        .limit(limit)
        .all()
    )

    return {
        "data": [
            {"act_id": r.act_id, "act_name": r.act_name, "case_count": r.case_count}
            for r in results
        ]
    }


@router.get("/citations")
def citation_analytics(db: Session = Depends(get_db)):
    """Citation type distribution and stats."""
    type_dist = (
        db.query(
            Citation.citation_type,
            func.count(Citation.citation_id).label('total'),
            func.count(func.distinct(Citation.case_id)).label('unique_cases'),
        )
        .group_by(Citation.citation_type)
        .order_by(desc('total'))
        .all()
    )

    return {
        "citation_types": [
            {"type": t.citation_type, "total": t.total, "unique_cases": t.unique_cases}
            for t in type_dist
        ],
        "total_citations": db.query(func.count(Citation.citation_id)).scalar(),
    }


@router.get("/verdicts")
def verdict_analytics(db: Session = Depends(get_db)):
    """Verdict distribution by case type."""
    results = (
        db.query(
            Case.case_type,
            Case.verdict,
            func.count(Case.case_id).label('count'),
        )
        .filter(Case.verdict.isnot(None), Case.verdict != '')
        .group_by(Case.case_type, Case.verdict)
        .order_by(Case.case_type, desc('count'))
        .all()
    )

    return {
        "data": [
            {"case_type": r.case_type, "verdict": r.verdict, "count": r.count}
            for r in results
        ]
    }


@router.get("/timeline")
def timeline_analytics(db: Session = Depends(get_db)):
    """Cases per year with verdict breakdown."""
    results = (
        db.query(
            extract('year', Case.judgment_date).label('year'),
            func.count(Case.case_id).label('total'),
            func.sum(sql_case((Case.verdict == 'Accepted', 1), else_=0)).label('accepted'),
            func.sum(sql_case((Case.verdict == 'Rejected', 1), else_=0)).label('rejected'),
            func.round(func.avg(Case.word_count)).label('avg_length'),
        )
        .filter(Case.judgment_date.isnot(None))
        .group_by('year')
        .order_by('year')
        .all()
    )

    return {
        "data": [
            {
                "year": int(r.year) if r.year else None,
                "total": r.total,
                "accepted": int(r.accepted or 0),
                "rejected": int(r.rejected or 0),
                "avg_length": int(r.avg_length or 0),
            }
            for r in results
        ]
    }


@router.get("/case-types")
def case_type_analytics(db: Session = Depends(get_db)):
    """Case type distribution."""
    results = (
        db.query(
            Case.case_type,
            Case.case_category,
            func.count(Case.case_id).label('total'),
            func.round(func.avg(Case.word_count)).label('avg_length'),
        )
        .group_by(Case.case_type, Case.case_category)
        .order_by(desc('total'))
        .all()
    )

    return {
        "data": [
            {
                "case_type": r.case_type,
                "case_category": r.case_category,
                "total": r.total,
                "avg_length": int(r.avg_length or 0),
            }
            for r in results
        ]
    }


@router.get("/lawyers")
def lawyer_analytics(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Top lawyers by case count."""
    results = (
        db.query(
            Lawyer.lawyer_id,
            Lawyer.lawyer_name,
            Lawyer.designation,
            func.count(CaseLawyer.case_id).label('total_cases'),
        )
        .join(CaseLawyer, Lawyer.lawyer_id == CaseLawyer.lawyer_id)
        .group_by(Lawyer.lawyer_id, Lawyer.lawyer_name, Lawyer.designation)
        .order_by(desc('total_cases'))
        .limit(limit)
        .all()
    )

    return {
        "data": [
            {
                "lawyer_id": r.lawyer_id,
                "lawyer_name": r.lawyer_name,
                "designation": r.designation,
                "total_cases": r.total_cases,
            }
            for r in results
        ]
    }
