"""
Search API Routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc

from backend.database.connection import get_db
from backend.models.models import Case, Judge, CaseJudge, Citation, Act, Party, CaseParty

router = APIRouter()


@router.get("")
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    search_type: str = Query("all", pattern="^(all|cases|judges|citations|acts)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Unified search across cases, judges, citations, and acts."""
    results = {}
    search_term = f"%{q}%"

    if search_type in ("all", "cases"):
        cases = (
            db.query(Case)
            .filter(
                or_(
                    Case.case_title.ilike(search_term),
                    Case.case_number.ilike(search_term),
                    Case.summary.ilike(search_term),
                )
            )
            .limit(limit)
            .all()
        )
        results["cases"] = [
            {
                "case_id": c.case_id,
                "case_title": c.case_title,
                "case_number": c.case_number,
                "case_type": c.case_type,
                "verdict": c.verdict,
                "judgment_date": str(c.judgment_date) if c.judgment_date else None,
            }
            for c in cases
        ]

    if search_type in ("all", "judges"):
        judges = (
            db.query(Judge)
            .filter(Judge.judge_name.ilike(search_term))
            .limit(limit)
            .all()
        )
        results["judges"] = [
            {"judge_id": j.judge_id, "judge_name": j.judge_name}
            for j in judges
        ]

    if search_type in ("all", "citations"):
        citations = (
            db.query(Citation)
            .filter(Citation.citation_text.ilike(search_term))
            .limit(limit)
            .all()
        )
        results["citations"] = [
            {
                "citation_id": c.citation_id,
                "citation_text": c.citation_text,
                "citation_type": c.citation_type,
                "case_id": c.case_id,
            }
            for c in citations
        ]

    if search_type in ("all", "acts"):
        acts = (
            db.query(Act)
            .filter(Act.act_name.ilike(search_term))
            .limit(limit)
            .all()
        )
        results["acts"] = [
            {"act_id": a.act_id, "act_name": a.act_name}
            for a in acts
        ]

    return {"query": q, "results": results}


@router.get("/cases/advanced")
def advanced_case_search(
    title: Optional[str] = None,
    judge: Optional[str] = None,
    act: Optional[str] = None,
    citation: Optional[str] = None,
    case_type: Optional[str] = None,
    verdict: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Advanced case search with multiple filters."""
    query = db.query(Case)

    if title:
        query = query.filter(Case.case_title.ilike(f"%{title}%"))
    if case_type:
        query = query.filter(Case.case_type == case_type)
    if verdict:
        query = query.filter(Case.verdict == verdict)
    if year_from:
        query = query.filter(func.extract('year', Case.judgment_date) >= year_from)
    if year_to:
        query = query.filter(func.extract('year', Case.judgment_date) <= year_to)
    if judge:
        query = (
            query.join(CaseJudge, Case.case_id == CaseJudge.case_id)
            .join(Judge, CaseJudge.judge_id == Judge.judge_id)
            .filter(Judge.judge_name.ilike(f"%{judge}%"))
        )
    if citation:
        query = (
            query.join(Citation, Case.case_id == Citation.case_id)
            .filter(Citation.citation_text.ilike(f"%{citation}%"))
        )

    total = query.count()
    cases = query.order_by(desc(Case.case_id)).limit(limit).all()

    return {
        "total": total,
        "data": [
            {
                "case_id": c.case_id,
                "case_title": c.case_title,
                "case_number": c.case_number,
                "case_type": c.case_type,
                "verdict": c.verdict,
                "judgment_date": str(c.judgment_date) if c.judgment_date else None,
                "word_count": c.word_count,
            }
            for c in cases
        ],
    }
