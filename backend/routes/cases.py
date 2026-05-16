"""
Cases API Routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from backend.database.connection import get_db
from backend.models.models import (
    Case, Court, CaseJudge, Judge, Citation,
    CaseParty, Party, CaseLawyer, Lawyer, CaseAct, Act
)

router = APIRouter()


@router.get("")
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    case_type: Optional[str] = None,
    case_category: Optional[str] = None,
    verdict: Optional[str] = None,
    sort_by: str = Query("case_id", pattern="^(case_id|judgment_date|word_count|case_title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """List cases with filtering, pagination, and sorting."""
    query = db.query(Case).options(joinedload(Case.court))

    if case_type:
        query = query.filter(Case.case_type == case_type)
    if case_category:
        query = query.filter(Case.case_category == case_category)
    if verdict:
        query = query.filter(Case.verdict == verdict)

    sort_col = getattr(Case, sort_by)
    query = query.order_by(desc(sort_col) if order == "desc" else sort_col)

    total = query.count()
    cases = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [
            {
                "case_id": c.case_id,
                "case_number": c.case_number,
                "case_title": c.case_title,
                "court_name": c.court.court_name if c.court else None,
                "judgment_date": str(c.judgment_date) if c.judgment_date else None,
                "case_type": c.case_type,
                "case_category": c.case_category,
                "verdict": c.verdict,
                "bench_strength": c.bench_strength,
                "word_count": c.word_count,
            }
            for c in cases
        ],
    }


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    """Get detailed case information with all relationships."""
    case = (
        db.query(Case)
        .options(
            joinedload(Case.court),
            joinedload(Case.judges).joinedload(CaseJudge.judge),
            joinedload(Case.parties).joinedload(CaseParty.party),
            joinedload(Case.lawyers_rel).joinedload(CaseLawyer.lawyer),
            joinedload(Case.citations),
        )
        .filter(Case.case_id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "case_id": case.case_id,
        "case_number": case.case_number,
        "case_title": case.case_title,
        "court_name": case.court.court_name if case.court else None,
        "judgment_date": str(case.judgment_date) if case.judgment_date else None,
        "case_type": case.case_type,
        "case_category": case.case_category,
        "verdict": case.verdict,
        "bench_strength": case.bench_strength,
        "bench_type": case.bench_type,
        "word_count": case.word_count,
        "summary": case.summary,
        "judges": [
            {"judge_id": cj.judge.judge_id, "judge_name": cj.judge.judge_name, "role": cj.role}
            for cj in case.judges
        ],
        "parties": [
            {"party_id": cp.party.party_id, "party_name": cp.party.party_name, "role": cp.role}
            for cp in case.parties
        ],
        "lawyers": [
            {"lawyer_id": cl.lawyer.lawyer_id, "lawyer_name": cl.lawyer.lawyer_name,
             "role": cl.role, "side": cl.side}
            for cl in case.lawyers_rel
        ],
        "citations": [
            {"citation_id": ct.citation_id, "citation_text": ct.citation_text, "citation_type": ct.citation_type}
            for ct in case.citations
        ],
    }


@router.post("")
def create_case(
    case_number: str,
    case_title: str,
    court_name: str = "Supreme Court of India",
    case_type: str = "",
    case_category: str = "",
    verdict: str = "",
    summary: str = "",
    db: Session = Depends(get_db),
):
    """Add a new case using transaction."""
    court = db.query(Court).filter(Court.court_name == court_name).first()
    if not court:
        court = Court(court_name=court_name)
        db.add(court)
        db.flush()

    case = Case(
        case_number=case_number,
        case_title=case_title,
        court_id=court.court_id,
        case_type=case_type,
        case_category=case_category,
        verdict=verdict,
        summary=summary,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"case_id": case.case_id, "message": "Case created successfully"}
