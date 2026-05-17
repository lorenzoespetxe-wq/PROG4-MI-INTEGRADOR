from typing import Generic, TypeVar, Any
from datetime import datetime, timezone
from sqlmodel import Session, select, func

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: Any) -> T | None:
        return self.session.get(self.model, id)

    def list_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        statement = select(self.model).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        statement = select(func.count()).select_from(self.model)
        return self.session.exec(statement).one()

    def create(self, obj_in: T) -> T:
        self.session.add(obj_in)
        self.session.flush()
        self.session.refresh(obj_in)
        return obj_in

    def update(self, db_obj: T, obj_in: dict[str, Any]) -> T:
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        self.session.add(db_obj)
        self.session.flush()
        self.session.refresh(db_obj)
        return db_obj

    def soft_delete(self, db_obj: T) -> T:
        if hasattr(db_obj, "deleted_at"):
            setattr(db_obj, "deleted_at", datetime.now(timezone.utc))
            # FIX: marcar como inactivo al hacer baja lógica para que el
            # login (y cualquier otro guard que evalúe `activo`) lo rechace
            # correctamente, incluso si la query no filtra por deleted_at.
            if hasattr(db_obj, "activo"):
                setattr(db_obj, "activo", False)
            self.session.add(db_obj)
            self.session.flush()
        return db_obj

    def hard_delete(self, db_obj: T) -> None:
        self.session.delete(db_obj)
        self.session.flush()
