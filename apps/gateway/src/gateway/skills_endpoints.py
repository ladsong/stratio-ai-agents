"""Skills management API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.skills.loader import SkillsManager
from gateway.dependencies import get_db, get_request_id, verify_auth

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("", dependencies=[Depends(verify_auth)])
def list_skills(
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[dict]:
    """List all available skills."""
    manager = SkillsManager()
    skills = manager.list_available_skills()
    
    # Transform to match expected format
    result = []
    for skill in skills:
        skill_data = {
            "name": skill.get("name", ""),
            "description": skill.get("description", ""),
            "emoji": skill.get("metadata", {}).get("nanobot", {}).get("emoji", "📦"),
            "requires": skill.get("metadata", {}).get("nanobot", {}).get("requires", {}),
            "install": skill.get("metadata", {}).get("nanobot", {}).get("install", []),
            "enabled": True  # Default to enabled for now
        }
        result.append(skill_data)
    
    return result


@router.get("/{skill_name}", dependencies=[Depends(verify_auth)])
def get_skill(
    skill_name: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> dict:
    """Get skill details including full content."""
    manager = SkillsManager()
    
    # Get metadata
    metadata = manager.get_skill_metadata(skill_name)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    
    # Get full content
    content = manager.load_skill(skill_name)
    
    return {
        "name": skill_name,
        "metadata": metadata,
        "content": content
    }
