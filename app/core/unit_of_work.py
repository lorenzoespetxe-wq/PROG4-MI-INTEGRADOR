from sqlmodel import Session
from types import TracebackType


class UnitOfWork:
    def __init__(self, session: Session):
        self.session = session

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> False:
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        # Retornar False permite que la excepción se relance si ocurrió una
        return False

    def flush(self) -> None:
        self.session.flush()
