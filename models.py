from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    """Modelo para la tabla Usuarios"""
    __tablename__ = 'usuarios'
    
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Roles: 'administrador', 'laboral', 'cliente'
    rol = db.Column(db.String(20), default='laboral', nullable=False)
    nombre_completo = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    planos = db.relationship('Plano', backref='usuario', lazy=True)
    ventas = db.relationship('Venta', backref='usuario', lazy=True)
    
    # Método requerido por Flask-Login para obtener el ID
    def get_id(self):
        return str(self.id_usuario)
    
    def set_password(self, password):
        """Encriptar contraseña"""
        self.contraseña = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.contraseña, password)
    
    @property
    def es_administrador(self):
        return self.rol == 'administrador'
    
    @property
    def es_laboral(self):
        return self.rol == 'laboral'
    
    @property
    def es_cliente(self):
        return self.rol == 'cliente'
    
    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'

class Cliente(db.Model):
    """Modelo para la tabla Clientes"""
    __tablename__ = 'clientes'
    
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.Text, nullable=False)
    
    # Relaciones
    proyectos = db.relationship('Proyecto', backref='cliente', lazy=True)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def __repr__(self):
        return f'<Cliente {self.nombre_completo}>'

class Proyecto(db.Model):
    """Modelo para la tabla Proyectos"""
    __tablename__ = 'proyectos'
    
    id_proyecto = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    nombre_proyecto = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='planificacion')
    
    # Relaciones
    planos = db.relationship('Plano', backref='proyecto', lazy=True)
    
    def __repr__(self):
        return f'<Proyecto {self.nombre_proyecto}>'

class TipoPlano(db.Model):
    """Modelo para la tabla Tipos_Plano"""
    __tablename__ = 'tipos_plano'
    
    id_tipo_plano = db.Column(db.Integer, primary_key=True)
    nombre_tipo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    
    # Relaciones
    planos = db.relationship('Plano', backref='tipo_plano', lazy=True)
    
    def __repr__(self):
        return f'<TipoPlano {self.nombre_tipo}>'

class Plano(db.Model):
    """Modelo para la tabla Planos"""
    __tablename__ = 'planos'
    
    id_plano = db.Column(db.Integer, primary_key=True)
    id_proyecto = db.Column(db.Integer, db.ForeignKey('proyectos.id_proyecto'), nullable=False)
    id_tipo_plano = db.Column(db.Integer, db.ForeignKey('tipos_plano.id_tipo_plano'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    nombre_plano = db.Column(db.String(100), nullable=False)
    archivo = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    detalle_ventas = db.relationship('DetalleVenta', backref='plano', lazy=True)
    
    def __repr__(self):
        return f'<Plano {self.nombre_plano}>'

class Material(db.Model):
    """Modelo para la tabla Materiales"""
    __tablename__ = 'materiales'
    
    id_material = db.Column(db.Integer, primary_key=True)
    nombre_material = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    # Categorías: 'papel', 'tinta', 'herramienta', 'otro'
    categoria = db.Column(db.String(50), default='otro')
    # Subcategoría para papeles: 'A0', 'A1', 'A2', 'A3', 'A4'
    # Subcategoría para tintas: 'negro', 'color', 'cyan', 'magenta', 'amarillo'
    subcategoria = db.Column(db.String(50))
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    precio_compra = db.Column(db.Numeric(10, 2), default=0.0)
    unidad_medida = db.Column(db.String(20), default='unidad')
    stock_minimo = db.Column(db.Integer, default=10)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    inventarios = db.relationship('Inventario', backref='material', lazy=True)
    detalle_ventas = db.relationship('DetalleVenta', backref='material', lazy=True)
    
    def __repr__(self):
        return f'<Material {self.nombre_material}>'

class Inventario(db.Model):
    """Modelo para la tabla Inventario"""
    __tablename__ = 'inventario'
    
    id_inventario = db.Column(db.Integer, primary_key=True)
    id_material = db.Column(db.Integer, db.ForeignKey('materiales.id_material'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ubicacion = db.Column(db.String(100))
    
    @property
    def necesita_reposicion(self):
        """Verifica si el inventario está por debajo del stock mínimo"""
        return self.cantidad <= self.material.stock_minimo
    
    @property
    def valor_total(self):
        """Calcula el valor total del inventario"""
        return float(self.cantidad * self.material.precio_unitario)
    
    def __repr__(self):
        return f'<Inventario {self.material.nombre_material}: {self.cantidad}>'

class Venta(db.Model):
    """Modelo para la tabla Ventas"""
    __tablename__ = 'ventas'
    
    id_venta = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2), default=0.0)
    impuesto = db.Column(db.Numeric(10, 2), default=0.0)
    descuento = db.Column(db.Numeric(10, 2), default=0.0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default='completada')  # completada, pendiente, cancelada
    metodo_pago = db.Column(db.String(50))  # efectivo, tarjeta, transferencia
    notas = db.Column(db.Text)
    
    # Relaciones
    detalle_ventas = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade='all, delete-orphan')
    
    def calcular_total(self):
        """Calcula el total de la venta basado en los detalles"""
        self.subtotal = sum(detalle.subtotal for detalle in self.detalle_ventas)
        self.total = float(self.subtotal + self.impuesto - self.descuento)
        return self.total
    
    def __repr__(self):
        return f'<Venta {self.id_venta}>'

class DetalleVenta(db.Model):
    """Modelo para la tabla Detalle_Ventas"""
    __tablename__ = 'detalle_ventas'
    
    id_detalle_venta = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), nullable=False)
    id_plano = db.Column(db.Integer, db.ForeignKey('planos.id_plano'), nullable=True)
    id_material = db.Column(db.Integer, db.ForeignKey('materiales.id_material'), nullable=True)
    descripcion = db.Column(db.String(200))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    descuento = db.Column(db.Numeric(10, 2), default=0.0)
    
    @property
    def subtotal(self):
        """Calcula el subtotal del detalle"""
        return float(self.cantidad * self.precio_unitario - self.descuento)
    
    def __repr__(self):
        return f'<DetalleVenta {self.id_detalle_venta}>'