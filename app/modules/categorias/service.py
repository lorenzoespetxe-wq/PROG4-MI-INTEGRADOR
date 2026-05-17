# app/modules/categorias/service.py
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import (
    http_error,
    NOT_FOUND,
    ALREADY_EXISTS,
    INVALID_TRANSITION,
)
from app.modules.categorias.model import Categoria
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaRead,
    CategoriaTree,
)
from app.modules.categorias.repository import CategoriaRepository


class CategoriaService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _map_to_read(self, categoria: Categoria) -> CategoriaRead:
        return CategoriaRead.model_validate(categoria)

    def _get_active_categoria(self, repo: CategoriaRepository, id: int) -> Categoria:
        categoria = repo.get_by_id(id)
        if not categoria or categoria.deleted_at is not None:
            raise http_error(404, "Categoría no encontrada", NOT_FOUND)
        return categoria

    def crear(self, data: CategoriaCreate) -> CategoriaRead:
        with self.uow:
            repo = CategoriaRepository(self.uow.session)

            if repo.get_by_nombre(data.nombre):
                raise http_error(
                    409, "Ya existe una categoría con este nombre", ALREADY_EXISTS
                )

            if data.parent_id is not None:
                self._get_active_categoria(repo, data.parent_id)

            nueva_categoria = Categoria(
                nombre=data.nombre,
                descripcion=data.descripcion,
                parent_id=data.parent_id,
                imagen_url=data.imagen_url,
            )

            self.uow.session.add(nueva_categoria)
            self.uow.session.flush()
            self.uow.session.refresh(nueva_categoria)

            return self._map_to_read(nueva_categoria)

    def listar(self) -> list[CategoriaRead]:
        with self.uow:
            repo = CategoriaRepository(self.uow.session)
            categorias = repo.get_todos_activos()
            return [self._map_to_read(c) for c in categorias]

    def listar_arbol(self) -> list[CategoriaTree]:
        with self.uow:
            repo = CategoriaRepository(self.uow.session)
            categorias = repo.get_todos_activos()

            # Construcción del árbol en memoria a partir de lista plana
            nodos = {
                c.id: CategoriaTree(
                    id=c.id, nombre=c.nombre, imagen_url=c.imagen_url, hijos=[]
                )
                for c in categorias
                if c.id is not None
            }

            arbol = []
            for c in categorias:
                if c.id is None:
                    continue
                nodo = nodos[c.id]
                if c.parent_id is None:
                    arbol.append(nodo)
                elif c.parent_id in nodos:
                    nodos[c.parent_id].hijos.append(nodo)

            return arbol

    def get_categoria(self, id: int) -> CategoriaRead:
        with self.uow:
            repo = CategoriaRepository(self.uow.session)
            categoria = self._get_active_categoria(repo, id)
            return self._map_to_read(categoria)

    def actualizar(self, id: int, data: CategoriaUpdate) -> CategoriaRead:
        with self.uow:
            repo = CategoriaRepository(self.uow.session)
            categoria = self._get_active_categoria(repo, id)

            update_data = data.model_dump(exclude_unset=True)

            if "nombre" in update_data and update_data["nombre"] != categoria.nombre:
                if repo.get_by_nombre(update_data["nombre"]):
                    raise http_error(
                        409, "Ya existe una categoría con este nombre", ALREADY_EXISTS
                    )

            if (
                "parent_id" in update_data
                and update_data["parent_id"] != categoria.parent_id
            ):
                nuevo_parent_id = update_data["parent_id"]
                if nuevo_parent_id is not None:
                    self._get_active_categoria(repo, nuevo_parent_id)
                    # Validación para prevenir referencias circulares
                    if repo.es_ancestro(
                        posible_ancestro_id=id, nodo_id=nuevo_parent_id
                    ):
                        raise http_error(
                            422,
                            "Operación crearía un ciclo en la jerarquía",
                            INVALID_TRANSITION,
                        )

            categoria = repo.update(categoria, update_data)
            return self._map_to_read(categoria)

    def eliminar(self, id: int) -> None:
        with self.uow:
            repo = CategoriaRepository(self.uow.session)
            categoria = self._get_active_categoria(repo, id)

            if repo.get_hijos_activos(id):
                raise http_error(
                    409, "La categoría tiene subcategorías activas", ALREADY_EXISTS
                )

            if repo.tiene_productos_asociados(id):
                raise http_error(
                    409, "La categoría tiene productos asociados", ALREADY_EXISTS
                )

            repo.soft_delete(categoria)
