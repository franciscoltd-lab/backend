from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import Event, Profile, User
from app.routes.media import public_media_url, save_base64_image
from app.schemas import EventCreate, EventOut, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


def serialize_event(event: Event) -> EventOut:
    profile = event.establishment.profile if event.establishment else None
    return EventOut(
        id=event.id,
        establishment_id=event.establishment_id,
        establishment_name=profile.display_name if profile else None,
        establishment_image_url=public_media_url(profile.profile_image_url) if profile else None,
        title=event.title,
        description=event.description,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        location=event.location,
        image_url=public_media_url(event.image_url),
    )


def event_image_url(image_base64: str | None, image_url: str | None) -> str | None:
    if image_base64:
        return save_base64_image(image_base64)
    return image_url


@router.post("", response_model=EventOut)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "establishment":
        raise HTTPException(403, "Only establishments can create events")

    row = Event(
        establishment_id=user.id,
        title=payload.title,
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        location=payload.location,
        image_url=event_image_url(payload.image_base64, payload.image_url),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_event(row)


@router.get("", response_model=list[EventOut])
def list_my_events(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "establishment":
        raise HTTPException(403, "Only establishments can manage events")

    rows = (
        db.query(Event)
        .filter(Event.establishment_id == user.id)
        .order_by(Event.starts_at.asc())
        .all()
    )
    return [serialize_event(row) for row in rows]


@router.get("/{event_id}", response_model=EventOut)
def get_my_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(Event).filter(Event.id == event_id, Event.establishment_id == user.id).first()
    if not row:
        raise HTTPException(404, "Event not found")
    return serialize_event(row)


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "establishment":
        raise HTTPException(403, "Only establishments can manage events")

    row = db.query(Event).filter(Event.id == event_id, Event.establishment_id == user.id).first()
    if not row:
        raise HTTPException(404, "Event not found")

    data = payload.model_dump(exclude_unset=True)
    if "image_base64" in data or "image_url" in data:
        row.image_url = event_image_url(data.pop("image_base64", None), data.pop("image_url", row.image_url))

    for key, value in data.items():
        setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return serialize_event(row)


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "establishment":
        raise HTTPException(403, "Only establishments can manage events")

    row = db.query(Event).filter(Event.id == event_id, Event.establishment_id == user.id).first()
    if not row:
        raise HTTPException(404, "Event not found")

    db.delete(row)
    db.commit()
    return {"ok": True}
