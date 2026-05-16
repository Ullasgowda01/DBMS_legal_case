"""
Citations API Routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database.connection import get_db
from backend.models.models import Citation, Case, CaseCitation

router = APIRouter()


@router.get("")
def list_citations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    citation_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List citations with filtering."""
    query = db.query(Citation)
    if citation_type:
        query = query.filter(Citation.citation_type == citation_type)

    total = query.count()
    citations = query.order_by(Citation.citation_id).offset(skip).limit(limit).all()

    return {
        "total": total,
        "data": [
            {
                "citation_id": c.citation_id,
                "citation_text": c.citation_text,
                "citation_type": c.citation_type,
                "case_id": c.case_id,
            }
            for c in citations
        ],
    }


@router.get("/graph")
def citation_graph(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get citation graph data for visualization."""
    links = (
        db.query(CaseCitation)
        .order_by(desc(CaseCitation.citation_strength))
        .limit(limit)
        .all()
    )

    # Get unique case IDs
    case_ids = set()
    for link in links:
        case_ids.add(link.source_case_id)
        case_ids.add(link.target_case_id)

    # Get case info for nodes
    cases = db.query(Case).filter(Case.case_id.in_(case_ids)).all()
    nodes = [
        {
            "id": c.case_id,
            "title": c.case_title or c.case_number or f"Case #{c.case_id}",
            "verdict": c.verdict,
            "case_type": c.case_type,
        }
        for c in cases
    ]

    edges = [
        {
            "source": l.source_case_id,
            "target": l.target_case_id,
            "strength": l.citation_strength,
        }
        for l in links
    ]

    return {"nodes": nodes, "edges": edges}


@router.get("/cases/{case_id}")
def case_citations(case_id: int, db: Session = Depends(get_db)):
    """Get all citations for a specific case."""
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Direct citations
    citations = db.query(Citation).filter(Citation.case_id == case_id).all()

    # Cases this case cites
    citing = (
        db.query(CaseCitation, Case)
        .join(Case, CaseCitation.target_case_id == Case.case_id)
        .filter(CaseCitation.source_case_id == case_id)
        .all()
    )

    # Cases that cite this case
    cited_by = (
        db.query(CaseCitation, Case)
        .join(Case, CaseCitation.source_case_id == Case.case_id)
        .filter(CaseCitation.target_case_id == case_id)
        .all()
    )

    return {
        "case_id": case_id,
        "citations": [
            {"citation_text": c.citation_text, "citation_type": c.citation_type}
            for c in citations
        ],
        "cites": [
            {"case_id": c.case_id, "case_title": c.case_title, "strength": cc.citation_strength}
            for cc, c in citing
        ],
        "cited_by": [
            {"case_id": c.case_id, "case_title": c.case_title, "strength": cc.citation_strength}
            for cc, c in cited_by
        ],
    }
