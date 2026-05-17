# app/modules/direcciones/service.py
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import http_error, NOT_FOUND
from app.modules.direcciones.model import DireccionEntrega
from app.modules.direcciones.schemas import (
    DireccionCreate,
    DireccionUpdate,
    DireccionRead,
)
from app.modules.direcciones.repository import DireccionRepository


class DireccionService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _map_to_read(self, direccion: DireccionEntrega) -> DireccionRead:
        return DireccionRead.model_validate(direccion)

    def _get_direccion_propia(
        self, repo: DireccionRepository, usuario_id: int, direccion_id: int
    ) -> DireccionEntrega:
        direccion = repo.get_por_usuario_y_id(usuario_id, direccion_id)
        if not direccion:
            raise http_error(404, "Dirección no encontrada", NOT_FOUND)
        return direccion

    def crear(self, usuario_id: int, data: DireccionCreate) -> DireccionRead:
        with self.uow:
            repo = DireccionRepository(self.uow.session)

            es_primera = repo.count_activas(usuario_id) == 0

            nueva_direccion = DireccionEntrega(
                usuario_id=usuario_id,
                alias=data.alias,
                linea1=data.linea1,
                linea2=data.linea2,
                ciudad=data.ciudad,
                provincia=data.provincia,
                codigo_postal=data.codigo_postal,
                latitud=data.latitud,
                longitud=data.longitud,
                es_principal=es_primera,
            )

            self.uow.session.add(nueva_direccion)
            self.uow.session.flush()
            self.uow.session.refresh(nueva_direccion)

            return self._map_to_read(nueva_direccion)

    def listar(self, usuario_id: int) -> list[DireccionRead]:
        with self.uow:
            repo = DireccionRepository(self.uow.session)
            direcciones = repo.list_por_usuario(usuario_id)
            return [self._map_to_read(d) for d in direcciones]

    def actualizar(
        self, usuario_id: int, direccion_id: int, data: DireccionUpdate
    ) -> DireccionRead:
        with self.uow:
            repo = DireccionRepository(self.uow.session)
            direccion = self._get_direccion_propia(repo, usuario_id, direccion_id)

            update_data = data.model_dump(exclude_unset=True)
            if update_data:
                direccion = repo.update(direccion, update_data)

            return self._map_to_read(direccion)

    def eliminar(self, usuario_id: int, direccion_id: int) -> None:
        with self.uow:
            repo = DireccionRepository(self.uow.session)
            direccion = self._get_direccion_propia(repo, usuario_id, direccion_id)

            era_principal = direccion.es_principal
            repo.soft_delete(direccion)

            if era_principal:
                mas_antigua = repo.get_mas_antigua_activa(usuario_id)
                if mas_antigua:
                    mas_antigua.es_principal = True
                    self.uow.session.add(mas_antigua)
                    self.uow.session.flush()

    def establecer_principal(self, usuario_id: int, direccion_id: int) -> DireccionRead:
        with self.uow:
            repo = DireccionRepository(self.uow.session)
            direccion = self._get_direccion_propia(repo, usuario_id, direccion_id)

            if not direccion.es_principal:
                repo.desmarcar_principal(usuario_id)
                direccion.es_principal = True
                self.uow.session.add(direccion)
                self.uow.session.flush()
                self.uow.session.refresh(direccion)

            return self._map_to_read(direccion)
