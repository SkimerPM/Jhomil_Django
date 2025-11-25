from django.db import models
from django.utils import timezone
import uuid
# -----------------------------
# 1) Usuarios y Roles
# -----------------------------
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    # NOTA: Este modelo NO extiende de AbstractBaseUser ni necesita configuraciones
    # especiales de autenticación de Django, ya que será gestionado por Spring Boot.
    METODOS_REGISTRO = [
        ('local', 'Local'),
        ('google', 'Google'),
    ]

    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios')
    nombre = models.CharField(max_length=100, null=True, blank=True)
    apellido = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    direccion = models.CharField(max_length=50, null=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    documento = models.CharField(max_length=20, null=True, blank=True)
    metodo_registro = models.CharField(max_length=10, choices=METODOS_REGISTRO, default='local')
    google_id = models.CharField(max_length=255, null=True, blank=True)
    foto_perfil = models.URLField(max_length=512, null=True, blank=True)
    email_verificado = models.BooleanField(default=False) #nuevo campo para intento de verificar email ;)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class RefreshToken(models.Model):
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='refresh_tokens')
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    def is_expired(self):
        return self.expires < timezone.now() or self.revoked

    def __str__(self):
        return f'{self.user.email} - {self.token}'

class EmailVerificationToken(models.Model):
    token = models.CharField(
        max_length=128,
        unique=True,
        default=uuid.uuid4
    )
    user = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='email_verification_tokens'
    )
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'core_email_verification_token'

    def is_expired(self):
        return self.expires < timezone.now() or self.used

    def __str__(self):
        return f'{self.user.email} - {self.token}'

# -----------------------------
# 2) Catálogo de productos
# -----------------------------
class Categoria(models.Model):
    nombre = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    id_padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategorias')
    descripcion = models.TextField(null=True, blank=True)
    imagen_url_base = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    imagen_logo = models.CharField(max_length=500, null=True, blank=True)
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    sku_base = models.CharField(max_length=100, unique=True, null=True, blank=True)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    volumen_m3 = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre


class Atributo(models.Model):
    TIPOS = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('decimal', 'Decimal'),
        ('booleano', 'Booleano'),
        ('lista', 'Lista'),
    ]
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    unidad = models.CharField(max_length=50, null=True, blank=True)
    es_variacion = models.BooleanField(default=False)
    orden_visual = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class CategoriaAtributo(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE)
    requerido = models.BooleanField(default=False)

    class Meta:
        unique_together = ('categoria', 'atributo')


class ProductoAtributo(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE)
    valor_text = models.TextField(null=True, blank=True)
    valor_num = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('producto', 'atributo')


class ProductoVariante(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    sku = models.CharField(max_length=150, unique=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    peso_kg = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.producto.nombre} - {self.sku}"


class VarianteAtributo(models.Model):
    variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE)
    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE)
    valor_text = models.TextField(null=True, blank=True)
    valor_num = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('variante', 'atributo')


class Imagen(models.Model):
    producto = models.ForeignKey(Producto, null=True, blank=True, on_delete=models.CASCADE)
    variante = models.ForeignKey(ProductoVariante, null=True, blank=True, on_delete=models.CASCADE)
    url = models.URLField(max_length=1024)
    es_principal = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)


# -----------------------------
# 3) Proveedores y Compras
# -----------------------------
class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    ruc = models.CharField(max_length=20, null=True, blank=True)
    contacto = models.CharField(max_length=200, null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('recibido', 'Recibido'),
        ('cancelado', 'Cancelado'),
    ]
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=100, unique=True, null=True, blank=True)
    fecha_compra = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    nota = models.TextField(null=True, blank=True)


class CompraItem(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    variante = models.ForeignKey(ProductoVariante, null=True, blank=True, on_delete=models.PROTECT)
    presentacion = models.CharField(max_length=100, null=True, blank=True)
    unidades_por_presentacion = models.IntegerField(default=1)
    cantidad_presentaciones = models.IntegerField()
    cantidad_unidades = models.IntegerField()
    precio_unitario_presentacion = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario_unidad = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


class Lote(models.Model):
    compra = models.ForeignKey(Compra, null=True, blank=True, on_delete=models.SET_NULL)
    proveedor = models.ForeignKey(Proveedor, null=True, blank=True, on_delete=models.SET_NULL)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    variante = models.ForeignKey(ProductoVariante, null=True, blank=True, on_delete=models.SET_NULL)
    codigo_lote = models.CharField(max_length=150, null=True, blank=True)
    presentacion = models.CharField(max_length=100, null=True, blank=True)
    unidades_por_presentacion = models.IntegerField(default=1)
    cantidad_inicial = models.IntegerField()
    cantidad_disponible = models.IntegerField()
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    id_almacen = models.IntegerField(null=True, blank=True)


class MovimientoInventario(models.Model):
    TIPOS = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('reserva', 'Reserva'),
        ('devolucion', 'Devolución'),
    ]
    lote = models.ForeignKey(Lote, null=True, blank=True, on_delete=models.SET_NULL)
    variante = models.ForeignKey(ProductoVariante, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cantidad = models.IntegerField()
    saldo_despues = models.IntegerField(null=True, blank=True)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    total_costo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    motivo = models.CharField(max_length=255, null=True, blank=True)
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateTimeField(default=timezone.now)


# -----------------------------
# 7) Promociones y Descuentos (Nueva Sección)
# -----------------------------
class Promocion(models.Model):
    TIPOS_DESCUENTO = [
        ('porcentaje', 'Porcentaje'),
        ('monto_fijo', 'Monto Fijo'),
        ('x_por_y', '(2x1, 3x2, etc.)'), # Nnuevo nombre
    ]
    
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, unique=True, null=True, blank=True) # Código de cupón
    tipo_descuento = models.CharField(max_length=20, choices=TIPOS_DESCUENTO)
    
    # Campo usado para Porcentaje (ej. 15.00) o Monto Fijo (ej. 10.00)
    # No usado para 2x1, pero se mantiene como campo obligatorio
    valor_descuento = models.DecimalField(max_digits=8, decimal_places=2, default=0.00) 
    
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    # Reglas
    min_compra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_usos = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.nombre

class PromocionProducto(models.Model):
    # Relación M:M para especificar a qué productos o variantes aplica la promoción
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE)

    # Puedes aplicar la promoción a un producto o a una variante específica
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True)
    variante = models.ForeignKey(ProductoVariante, on_delete=models.CASCADE, null=True, blank=True)
    # Producto o variante de regalo (para 2x1 u ofertas cruzadas)
    producto_gratis = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promociones_gratis"
    )
    variante_gratis = models.ForeignKey(
        ProductoVariante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promociones_gratis_variante"
    )

    cantidad_requerida = models.IntegerField(default=1)  # ej: “compra 2”
    cantidad_gratis = models.IntegerField(default=1)     # ej: “lleva 1”

    class Meta:
        verbose_name_plural = "Productos en Promoción"

    def __str__(self):
        target = self.variante or self.producto
        return f"{self.promocion.nombre} → {target}"


# -----------------------------
# 4) Carritos, Pedidos y Pagos (Sección Modificada)
# -----------------------------
class Carrito(models.Model):
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    # --- AGREGA ESTO ---
    # Para persistir el cupón entre recargas de página
    cupon_codigo = models.CharField(max_length=50, null=True, blank=True)
    # Para saber cuánto descontar al final sin recalcular todo cada vez
    descuento_global_aplicado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)


class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    variante = models.ForeignKey(ProductoVariante, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario_snapshot = models.DecimalField(max_digits=12, decimal_places=2)


class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('preparando', 'Preparando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=100, unique=True)
    fecha_pedido = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # El descuento TOTAL del pedido
    impuestos = models.DecimalField(max_digits=12, decimal_places=2)
    costo_envio = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, null=True, blank=True)
    direccion_envio = models.TextField(null=True, blank=True)
    nota = models.TextField(null=True, blank=True)


class PromocionAplicada(models.Model):
    # Tabla para registrar qué promociones se aplicaron al pedido completo (cupón principal)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='promociones_aplicadas')
    promocion = models.ForeignKey(Promocion, on_delete=models.PROTECT, null=True, blank=True)
    nombre_snapshot = models.CharField(max_length=150) 
    valor_descuento_aplicado = models.DecimalField(max_digits=12, decimal_places=2) # Descuento total monetario que aportó esta promoción
    
    class Meta:
        verbose_name_plural = "Promociones Aplicadas al Pedido"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    variante = models.ForeignKey(ProductoVariante, on_delete=models.PROTECT)
    lote_origen = models.ForeignKey(Lote, null=True, blank=True, on_delete=models.SET_NULL)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    # NUEVOS CAMPOS para trazabilidad de descuentos a nivel de item
    descuento_item = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Descuento monetario aplicado a esta línea
    promocion_aplicada = models.ForeignKey(Promocion, on_delete=models.SET_NULL, null=True, blank=True) # Qué promo específica causó este descuento
    total_neto = models.DecimalField(max_digits=12, decimal_places=2) # subtotal - descuento_item


class Pago(models.Model):
    METODOS = [
        ('yape', 'Yape'),
        ('plin', 'Plin'),
        ('transferencia', 'Transferencia'),
        ('contraentrega', 'Contra Entrega'),
        ('pos', 'POS'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('rechazado', 'Rechazado'),
    ]
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    metodo = models.CharField(max_length=20, choices=METODOS)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    comprobante_url = models.URLField(max_length=1024, null=True, blank=True)
    referencia_externa = models.CharField(max_length=255, null=True, blank=True)
    usuario_verificador = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='pagos_validados')
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    

# -----------------------------
# 5) Envíos y comprobantes
# -----------------------------
class EmpresaEnvio(models.Model):
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    api_endpoint = models.URLField(null=True, blank=True)


class Region(models.Model):
    nombre = models.CharField(max_length=255)


class Ciudad(models.Model):
    nombre = models.CharField(max_length=255)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)


class TarifaEnvio(models.Model):
    ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE)
    empresa = models.ForeignKey(EmpresaEnvio, on_delete=models.CASCADE)
    peso_min_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    peso_max_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)


class Envio(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En tránsito'),
        ('entregado', 'Entregado'),
        ('devuelto', 'Devuelto'),
    ]
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    empresa = models.ForeignKey(EmpresaEnvio, null=True, blank=True, on_delete=models.SET_NULL)
    ciudad = models.ForeignKey(Ciudad, null=True, blank=True, on_delete=models.SET_NULL)
    direccion = models.TextField()
    tracking = models.CharField(max_length=255, null=True, blank=True)
    costo_envio = models.DecimalField(max_digits=12, decimal_places=2)
    estado_envio = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega_estimada = models.DateTimeField(null=True, blank=True)
    fecha_entrega_real = models.DateTimeField(null=True, blank=True)


class Comprobante(models.Model):
    TIPOS = [
        ('boleta', 'Boleta'),
        ('factura', 'Factura'),
    ]
    ESTADOS = [
        ('emitida', 'Emitida'),
        ('anulada', 'Anulada'),
    ]
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    numero = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2)
    pdf_url = models.URLField(max_length=1024, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='emitida')


# -----------------------------
# 6) Logs y Jobs
# -----------------------------
class ImportJob(models.Model):
    TIPOS = [
        ('productos', 'Productos'),
        ('lotes', 'Lotes'),
        ('compras', 'Compras'),
        ('clientes', 'Clientes'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=50, choices=TIPOS)
    archivo_url = models.URLField()
    status = models.CharField(max_length=50)
    errores = models.TextField(null=True, blank=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)


class ExportJob(models.Model):
    TIPOS = [
        ('ventas', 'Ventas'),
        ('stock', 'Stock'),
        ('productos', 'Productos'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=50, choices=TIPOS)
    parametros = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50)
    url_archivo = models.URLField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_completado = models.DateTimeField(null=True, blank=True)


class LogAccion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255)
    detalle = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)