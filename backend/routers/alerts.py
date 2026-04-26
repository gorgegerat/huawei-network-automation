from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db, Alert

router = APIRouter()

class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int]
    alert_type: str
    severity: str
    title: str
    message: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    return alert

@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "告警已解决"}

@router.get("/stats/summary")
async def get_alert_stats(db: Session = Depends(get_db)):
    """获取告警统计"""
    total = db.query(Alert).count()
    resolved = db.query(Alert).filter(Alert.is_resolved == True).count()
    unresolved = total - resolved
    
    critical = db.query(Alert).filter(
        Alert.severity == "critical",
        Alert.is_resolved == False
    ).count()
    
    warning = db.query(Alert).filter(
        Alert.severity == "warning",
        Alert.is_resolved == False
    ).count()
    
    return {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "critical": critical,
        "warning": warning
    }
