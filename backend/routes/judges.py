"""
Judges API Routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database.connection import get_db
from backend.models.models import Judge, CaseJudge, Case, Citation

router = APIRouter()


@router.get("")
def list_judges(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List judges with case counts."""
    query = (
        db.query(
            Judge.judge_id,
            Judge.judge_name,
            func.count(CaseJudge.case_id).label('case_count'),
        )
        .outerjoin(CaseJudge, Judge.judge_id == CaseJudge.judge_id)
        .group_by(Judge.judge_id, Judge.judge_name)
    )

    if search:
        query = query.filter(Judge.judge_name.ilike(f'%{search}%'))

    total = query.count()
    judges = query.order_by(desc('case_count')).offset(skip).limit(limit).all()

    return {
        "total": total,
        "data": [
            {"judge_id": j.judge_id, "judge_name": j.judge_name, "case_count": j.case_count}
            for j in judges
        ],
    }


@router.get("/{judge_id}")
def get_judge(judge_id: int, db: Session = Depends(get_db)):
    """Get judge details."""
    judge = db.query(Judge).filter(Judge.judge_id == judge_id).first()
    if not judge:
        raise HTTPException(status_code=404, detail="Judge not found")

    # Get case stats
    stats = (
        db.query(
            func.count(CaseJudge.case_id).label('total_cases'),
            func.count(Case.case_id).filter(Case.verdict == 'Accepted').label('accepted'),
            func.count(Case.case_id).filter(Case.verdict == 'Rejected').label('rejected'),
            func.avg(Case.word_count).label('avg_word_count'),
        )
        .join(Case, CaseJudge.case_id == Case.case_id)
        .filter(CaseJudge.judge_id == judge_id)
        .first()
    )

    return {
        "judge_id": judge.judge_id,
        "judge_name": judge.judge_name,
        "total_cases": stats.total_cases if stats else 0,
        "accepted_cases": stats.accepted if stats else 0,
        "rejected_cases": stats.rejected if stats else 0,
        "avg_word_count": round(float(stats.avg_word_count or 0)),
    }


@router.get("/{judge_id}/analytics")
def judge_analytics(judge_id: int, db: Session = Depends(get_db)):
    """Get comprehensive judge analytics."""
    judge = db.query(Judge).filter(Judge.judge_id == judge_id).first()
    if not judge:
        raise HTTPException(status_code=404, detail="Judge not found")

    # Case type breakdown
    type_breakdown = (
        db.query(Case.case_type, func.count(Case.case_id).label('count'))
        .join(CaseJudge, Case.case_id == CaseJudge.case_id)
        .filter(CaseJudge.judge_id == judge_id)
        .group_by(Case.case_type)
        .all()
    )

    # Verdict breakdown
    verdict_breakdown = (
        db.query(Case.verdict, func.count(Case.case_id).label('count'))
        .join(CaseJudge, Case.case_id == CaseJudge.case_id)
        .filter(CaseJudge.judge_id == judge_id)
        .group_by(Case.verdict)
        .all()
    )

    # Citations count
    citation_count = (
        db.query(func.count(Citation.citation_id))
        .join(Case, Citation.case_id == Case.case_id)
        .join(CaseJudge, Case.case_id == CaseJudge.case_id)
        .filter(CaseJudge.judge_id == judge_id)
        .scalar()
    )

    return {
        "judge_id": judge.judge_id,
        "judge_name": judge.judge_name,
        "case_type_breakdown": [{"type": t.case_type, "count": t.count} for t in type_breakdown],
        "verdict_breakdown": [{"verdict": v.verdict, "count": v.count} for v in verdict_breakdown],
        "total_citations": citation_count or 0,
    }
