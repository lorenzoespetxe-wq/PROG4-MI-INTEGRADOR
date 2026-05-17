# app/modules/productos/service.py
import math
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import http_error, NOT_FOUND, ALREADY_EXISTS
from app.modules.productos.model import Producto, ProductoCategoria, ProductoIngrediente
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoUpdate,
    ProductoRead,
    ProductoDetail,
    PaginatedProductos,
    IngredienteEnProductoRead,
    IngredienteEnProductoRequest,
    StockUpdateRequest,
    DisponibilidadRequest,
    UnidadResumen,
)
from app.modules.productos.repository import (
    ProductoRepository,
    ProductoCategoriaRepository,
    ProductoIngredienteRepository,
)
from app.modules.categorias.model import Categoria
from app.modules.ingredientes.model import Ingrediente
from app.modules.unidades.model import UnidadMedida


class ProductoService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ──────────────────────────────────────────────────────────────────────
    # Helpers de mapeo
    # ──────────────────────────────────────────────────────────────────────

    def _map_to_read(self, producto: Producto) -> ProductoRead:
        unidad_venta = None
        if producto.unidad_venta:
            unidad_venta = UnidadResumen(
                id=producto.unidad_venta.id,
                nombre=producto.unidad_venta.nombre,
                simbolo=producto.unidad_venta.simbolo,
            )

        categorias = []
        for pc in producto.producto_categorias:
            # Accedemos a la categoría a través de la sesión (lazy load activo)
            cat = self.uow.session.get(Categoria, pc.categoria_id)
            if cat and cat.deleted_at is None:
                categorias.append(cat.nombre)

        return ProductoRead(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio_base=float(producto.precio_base),
            imagenes_url=producto.imagenes_url,
            stock_cantidad=producto.stock_cantidad,
            disponible=producto.disponible,
            unidad_venta=unidad_venta,
            categorias=categorias,
            created_at=producto.created_at,
        )

    def _map_to_detail(self, producto: Producto) -> ProductoDetail:
        read = self._map_to_read(producto)

        ingredientes = []
        for pi in producto.producto_ingredientes:
            ing = self.uow.session.get(Ingrediente, pi.ingrediente_id)
            unidad = self.uow.session.get(UnidadMedida, pi.unidad_medida_id)
            if ing and ing.deleted_at is None:
                ingredientes.append(
                    IngredienteEnProductoRead(
                        ingrediente_id=pi.ingrediente_id,
                        nombre=ing.nombre,
                        es_alergeno=ing.es_alergeno,
                        cantidad=float(pi.cantidad),
                        simbolo_unidad=unidad.simbolo if unidad else "",
                        es_removible=pi.es_removible,
                    )
                )

        return ProductoDetail(
            **read.model_dump(),
            ingredientes=ingredientes,
        )

    def _get_active_producto(self, repo: ProductoRepository, id: int) -> Producto:
        producto = repo.get_by_id(id)
        if not producto or producto.deleted_at is not None:
            raise http_error(404, "Producto no encontrado", NOT_FOUND)
        return producto

    def _validar_categorias(self, categoria_ids: list[int]) -> None:
        for cat_id in categoria_ids:
            cat = self.uow.session.get(Categoria, cat_id)
            if not cat or cat.deleted_at is not None:
                raise http_error(
                    404,
                    f"Categoría con id {cat_id} no encontrada o inactiva",
                    NOT_FOUND,
                )

    def _validar_ingredientes_y_unidades(
        self, ingredientes: list[IngredienteEnProductoRequest]
    ) -> None:
        for item in ingredientes:
            ing = self.uow.session.get(Ingrediente, item.ingrediente_id)
            if not ing or ing.deleted_at is not None:
                raise http_error(
                    404,
                    f"Ingrediente con id {item.ingrediente_id} no encontrado o inactivo",
                    NOT_FOUND,
                )
            unidad = self.uow.session.get(UnidadMedida, item.unidad_medida_id)
            if not unidad:
                raise http_error(
                    404,
                    f"Unidad de medida con id {item.unidad_medida_id} no encontrada",
                    NOT_FOUND,
                )

    def _crear_relaciones(
        self,
        producto_id: int,
        categoria_ids: list[int],
        ingredientes: list[IngredienteEnProductoRequest],
        cat_repo: ProductoCategoriaRepository,
        ing_repo: ProductoIngredienteRepository,
    ) -> None:
        for i, cat_id in enumerate(categoria_ids):
            self.uow.session.add(
                ProductoCategoria(
                    producto_id=producto_id,
                    categoria_id=cat_id,
                    es_principal=(i == 0),
                )
            )

        for item in ingredientes:
            self.uow.session.add(
                ProductoIngrediente(
                    producto_id=producto_id,
                    ingrediente_id=item.ingrediente_id,
                    cantidad=item.cantidad,
                    unidad_medida_id=item.unidad_medida_id,
                    es_removible=item.es_removible,
                )
            )

        self.uow.session.flush()

    # ──────────────────────────────────────────────────────────────────────
    # Operaciones públicas
    # ──────────────────────────────────────────────────────────────────────

    def crear(self, data: ProductoCreate) -> ProductoRead:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            cat_repo = ProductoCategoriaRepository(self.uow.session)
            ing_repo = ProductoIngredienteRepository(self.uow.session)

            if repo.get_by_nombre(data.nombre):
                raise http_error(
                    409, "Ya existe un producto con este nombre", ALREADY_EXISTS
                )

            self._validar_categorias(data.categoria_ids)
            self._validar_ingredientes_y_unidades(data.ingredientes)

            if data.unidad_venta_id is not None:
                unidad = self.uow.session.get(UnidadMedida, data.unidad_venta_id)
                if not unidad:
                    raise http_error(
                        404,
                        f"Unidad de venta con id {data.unidad_venta_id} no encontrada",
                        NOT_FOUND,
                    )

            nuevo_producto = Producto(
                nombre=data.nombre,
                descripcion=data.descripcion,
                precio_base=data.precio_base,
                imagenes_url=data.imagenes_url,
                stock_cantidad=data.stock_cantidad,
                disponible=data.disponible,
                unidad_venta_id=data.unidad_venta_id,
            )
            self.uow.session.add(nuevo_producto)
            self.uow.session.flush()
            self.uow.session.refresh(nuevo_producto)

            self._crear_relaciones(
                nuevo_producto.id,
                data.categoria_ids,
                data.ingredientes,
                cat_repo,
                ing_repo,
            )

            # Recargar relaciones
            self.uow.session.refresh(nuevo_producto)
            return self._map_to_read(nuevo_producto)

    def listar(
        self,
        search: str | None,
        categoria_id: int | None,
        disponible: bool | None,
        page: int,
        size: int,
    ) -> PaginatedProductos:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            skip = (page - 1) * size

            items = repo.list_with_filters(
                search=search,
                categoria_id=categoria_id,
                disponible=disponible,
                skip=skip,
                limit=size,
            )
            total = repo.count_with_filters(
                search=search,
                categoria_id=categoria_id,
                disponible=disponible,
            )
            pages = math.ceil(total / size) if size > 0 else 0

            return PaginatedProductos(
                items=[self._map_to_read(p) for p in items],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    def get_detalle(self, id: int) -> ProductoDetail:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            producto = repo.get_with_relations(id)
            if not producto:
                raise http_error(404, "Producto no encontrado", NOT_FOUND)
            return self._map_to_detail(producto)

    def actualizar(self, id: int, data: ProductoUpdate) -> ProductoRead:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            cat_repo = ProductoCategoriaRepository(self.uow.session)
            ing_repo = ProductoIngredienteRepository(self.uow.session)

            producto = self._get_active_producto(repo, id)

            update_data = data.model_dump(
                exclude_unset=True, exclude={"categoria_ids", "ingredientes"}
            )

            if "nombre" in update_data and update_data["nombre"] != producto.nombre:
                if repo.get_by_nombre(update_data["nombre"]):
                    raise http_error(
                        409, "Ya existe un producto con este nombre", ALREADY_EXISTS
                    )

            if (
                "unidad_venta_id" in update_data
                and update_data["unidad_venta_id"] is not None
            ):
                unidad = self.uow.session.get(
                    UnidadMedida, update_data["unidad_venta_id"]
                )
                if not unidad:
                    raise http_error(
                        404,
                        f"Unidad de venta con id {update_data['unidad_venta_id']} no encontrada",
                        NOT_FOUND,
                    )

            # Actualizar campos escalares
            for key, value in update_data.items():
                setattr(producto, key, value)
            self.uow.session.add(producto)
            self.uow.session.flush()

            # Reemplazar categorías si se proveyeron
            if data.categoria_ids is not None:
                self._validar_categorias(data.categoria_ids)
                cat_repo.delete_por_producto(producto.id)
                for i, cat_id in enumerate(data.categoria_ids):
                    self.uow.session.add(
                        ProductoCategoria(
                            producto_id=producto.id,
                            categoria_id=cat_id,
                            es_principal=(i == 0),
                        )
                    )
                self.uow.session.flush()

            # Reemplazar ingredientes si se proveyeron
            if data.ingredientes is not None:
                self._validar_ingredientes_y_unidades(data.ingredientes)
                ing_repo.delete_por_producto(producto.id)
                for item in data.ingredientes:
                    self.uow.session.add(
                        ProductoIngrediente(
                            producto_id=producto.id,
                            ingrediente_id=item.ingrediente_id,
                            cantidad=item.cantidad,
                            unidad_medida_id=item.unidad_medida_id,
                            es_removible=item.es_removible,
                        )
                    )
                self.uow.session.flush()

            self.uow.session.refresh(producto)
            return self._map_to_read(producto)

    def eliminar(self, id: int) -> None:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            producto = self._get_active_producto(repo, id)
            repo.soft_delete(producto)

    def cambiar_disponibilidad(
        self, id: int, data: DisponibilidadRequest
    ) -> ProductoRead:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            producto = self._get_active_producto(repo, id)
            producto.disponible = data.disponible
            self.uow.session.add(producto)
            self.uow.session.flush()
            self.uow.session.refresh(producto)
            return self._map_to_read(producto)

    def actualizar_stock(self, id: int, data: StockUpdateRequest) -> ProductoRead:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            self._get_active_producto(repo, id)
            producto = repo.update_stock_absoluto(id, data.stock_cantidad)
            return self._map_to_read(producto)

    def agregar_ingrediente(
        self, producto_id: int, data: IngredienteEnProductoRequest
    ) -> ProductoDetail:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            ing_repo = ProductoIngredienteRepository(self.uow.session)

            producto = repo.get_with_relations(producto_id)
            if not producto:
                raise http_error(404, "Producto no encontrado", NOT_FOUND)

            ing = self.uow.session.get(Ingrediente, data.ingrediente_id)
            if not ing or ing.deleted_at is not None:
                raise http_error(
                    404,
                    f"Ingrediente con id {data.ingrediente_id} no encontrado o inactivo",
                    NOT_FOUND,
                )

            unidad = self.uow.session.get(UnidadMedida, data.unidad_medida_id)
            if not unidad:
                raise http_error(
                    404,
                    f"Unidad de medida con id {data.unidad_medida_id} no encontrada",
                    NOT_FOUND,
                )

            existente = ing_repo.get_por_producto_e_ingrediente(
                producto_id, data.ingrediente_id
            )
            if existente:
                raise http_error(
                    409,
                    "El ingrediente ya está asociado a este producto",
                    ALREADY_EXISTS,
                )

            self.uow.session.add(
                ProductoIngrediente(
                    producto_id=producto_id,
                    ingrediente_id=data.ingrediente_id,
                    cantidad=data.cantidad,
                    unidad_medida_id=data.unidad_medida_id,
                    es_removible=data.es_removible,
                )
            )
            self.uow.session.flush()
            self.uow.session.refresh(producto)
            return self._map_to_detail(producto)

    def quitar_ingrediente(
        self, producto_id: int, ingrediente_id: int
    ) -> ProductoDetail:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            ing_repo = ProductoIngredienteRepository(self.uow.session)

            producto = repo.get_with_relations(producto_id)
            if not producto:
                raise http_error(404, "Producto no encontrado", NOT_FOUND)

            asociacion = ing_repo.get_por_producto_e_ingrediente(
                producto_id, ingrediente_id
            )
            if not asociacion:
                raise http_error(
                    404,
                    "El ingrediente no está asociado a este producto",
                    NOT_FOUND,
                )

            self.uow.session.delete(asociacion)
            self.uow.session.flush()
            self.uow.session.refresh(producto)
            return self._map_to_detail(producto)

    def get_ingredientes(self, producto_id: int) -> list[IngredienteEnProductoRead]:
        with self.uow:
            repo = ProductoRepository(self.uow.session)
            producto = repo.get_with_relations(producto_id)
            if not producto:
                raise http_error(404, "Producto no encontrado", NOT_FOUND)

            ingredientes = []
            for pi in producto.producto_ingredientes:
                ing = self.uow.session.get(Ingrediente, pi.ingrediente_id)
                unidad = self.uow.session.get(UnidadMedida, pi.unidad_medida_id)
                if ing and ing.deleted_at is None:
                    ingredientes.append(
                        IngredienteEnProductoRead(
                            ingrediente_id=pi.ingrediente_id,
                            nombre=ing.nombre,
                            es_alergeno=ing.es_alergeno,
                            cantidad=float(pi.cantidad),
                            simbolo_unidad=unidad.simbolo if unidad else "",
                            es_removible=pi.es_removible,
                        )
                    )
            return ingredientes
