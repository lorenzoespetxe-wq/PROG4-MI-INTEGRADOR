from datetime import datetime, timezone
from sqlmodel import Session, select, delete

from app.core.repository import BaseRepository
from app.modules.refreshtokens.model import RefreshToken


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: Session):
        super().__init__(RefreshToken, session)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.session.exec(statement).first()

    def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        self.session.flush()

    def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        statement = delete(RefreshToken).where(RefreshToken.expires_at < now)
        result = self.session.exec(statement)
        self.session.flush()
        return result.rowcount
