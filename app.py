from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from models import db, Usuario, Cliente, Proyecto, TipoPlano, Plano, Material, Inventario, Venta, DetalleVenta
from config import config
import os
from datetime import datetime, date
from fpdf import FPDF
import io

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object(config['development'])
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Crear tablas de la base de datos
    with app.app_context():
        db.create_all()
        # Crear usuario administrador por defecto
        if not Usuario.query.filter_by(email='admin@asplot.com').first():
            admin = Usuario(
                nombre_usuario='admin',
                email='admin@asplot.com',
                rol='administrador',
                nombre_completo='Administrador del Sistema',
                activo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Crear tipos de plano por defecto
            tipos_plano = [
                TipoPlano(nombre_tipo='Arquitectónico', descripcion='Planos arquitectónicos'),
                TipoPlano(nombre_tipo='Estructural', descripcion='Planos estructurales'),
                TipoPlano(nombre_tipo='Eléctrico', descripcion='Planos eléctricos'),
                TipoPlano(nombre_tipo='Plomería', descripcion='Planos de plomería'),
                TipoPlano(nombre_tipo='Mecánico', descripcion='Planos mecánicos'),
                TipoPlano(nombre_tipo='HVAC', descripcion='Planos de climatización'),
                TipoPlano(nombre_tipo='Topográfico', descripcion='Planos topográficos')
            ]
            
            for tipo in tipos_plano:
                db.session.add(tipo)
            
            # Crear cliente y proyecto de ejemplo para poder subir planos
            cliente_ejemplo = Cliente(
                nombre='Cliente',
                apellido='Ejemplo',
                email='ejemplo.sistema@asplot.com',
                telefono='555-0000',
                direccion='Dirección de ejemplo'
            )
            db.session.add(cliente_ejemplo)
            db.session.flush()
            
            proyecto_ejemplo = Proyecto(
                id_cliente=cliente_ejemplo.id_cliente,
                nombre_proyecto='Proyecto de Prueba',
                descripcion='Proyecto de ejemplo para subir planos de prueba',
                fecha_inicio=datetime.now().date(),
                fecha_fin=datetime.now().date(),
                estado='activo'
            )
            db.session.add(proyecto_ejemplo)
            
            db.session.commit()
    
    # Rutas de autenticación
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = Usuario.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciales inválidas', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    # Dashboard
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Obtener estadísticas para las tarjetas KPI
        total_clientes = Cliente.query.count()
        total_proyectos = Proyecto.query.count()
        total_planos = Plano.query.count()
        total_ventas = Venta.query.count()
        
        # Calcular existencia total
        existencia_total = db.session.query(db.func.sum(Inventario.cantidad)).scalar() or 0
        
        # Calcular importe vendido
        importe_vendido = db.session.query(db.func.sum(Venta.total)).scalar() or 0
        
        # Obtener proyectos recientes
        proyectos_recientes = Proyecto.query.order_by(Proyecto.fecha_inicio.desc()).limit(5).all()
        
        # Obtener ventas recientes
        ventas_recientes = Venta.query.order_by(Venta.fecha_venta.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                             total_clientes=total_clientes,
                             total_proyectos=total_proyectos,
                             total_planos=total_planos,
                             total_ventas=total_ventas,
                             existencia_total=existencia_total,
                             importe_vendido=importe_vendido,
                             proyectos_recientes=proyectos_recientes,
                             ventas_recientes=ventas_recientes)
    
    # Gestión de Clientes
    @app.route('/clientes')
    @login_required
    def clientes():
        search = request.args.get('search', '')
        if search:
            clientes = Cliente.query.filter(
                db.or_(
                    Cliente.nombre.contains(search),
                    Cliente.apellido.contains(search),
                    Cliente.email.contains(search)
                )
            ).all()
        else:
            clientes = Cliente.query.all()
        
        return render_template('clientes.html', clientes=clientes, search=search)
    
    @app.route('/clientes/crear', methods=['GET', 'POST'])
    @login_required
    def crear_cliente():
        if request.method == 'POST':
            cliente = Cliente(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                email=request.form['email'],
                telefono=request.form['telefono'],
                direccion=request.form['direccion']
            )
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente creado exitosamente', 'success')
            return redirect(url_for('clientes'))
        
        return render_template('crear_cliente.html')
    
    @app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_cliente(id):
        cliente = Cliente.query.get_or_404(id)
        
        if request.method == 'POST':
            cliente.nombre = request.form['nombre']
            cliente.apellido = request.form['apellido']
            cliente.email = request.form['email']
            cliente.telefono = request.form['telefono']
            cliente.direccion = request.form['direccion']
            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(url_for('clientes'))
        
        return render_template('editar_cliente.html', cliente=cliente)
    
    @app.route('/clientes/eliminar/<int:id>')
    @login_required
    def eliminar_cliente(id):
        cliente = Cliente.query.get_or_404(id)
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente eliminado exitosamente', 'success')
        return redirect(url_for('clientes'))
    
    # Gestión de Proyectos
    @app.route('/proyectos')
    @login_required
    def proyectos():
        search = request.args.get('search', '')
        estado = request.args.get('estado', '')
        
        query = Proyecto.query
        
        if search:
            query = query.filter(Proyecto.nombre_proyecto.contains(search))
        
        if estado:
            query = query.filter(Proyecto.estado == estado)
        
        proyectos = query.all()
        
        return render_template('proyectos.html', proyectos=proyectos, search=search, estado=estado)
    
    @app.route('/proyectos/crear', methods=['GET', 'POST'])
    @login_required
    def crear_proyecto():
        if request.method == 'POST':
            proyecto = Proyecto(
                id_cliente=request.form['id_cliente'],
                nombre_proyecto=request.form['nombre_proyecto'],
                descripcion=request.form['descripcion'],
                fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date(),
                fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date(),
                estado=request.form['estado']
            )
            db.session.add(proyecto)
            db.session.commit()
            flash('Proyecto creado exitosamente', 'success')
            return redirect(url_for('proyectos'))
        
        clientes = Cliente.query.all()
        return render_template('crear_proyecto.html', clientes=clientes)
    
    @app.route('/proyectos/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_proyecto(id):
        proyecto = Proyecto.query.get_or_404(id)
        
        if request.method == 'POST':
            proyecto.id_cliente = request.form['id_cliente']
            proyecto.nombre_proyecto = request.form['nombre_proyecto']
            proyecto.descripcion = request.form['descripcion']
            proyecto.fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date()
            proyecto.fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date()
            proyecto.estado = request.form['estado']
            db.session.commit()
            flash('Proyecto actualizado exitosamente', 'success')
            return redirect(url_for('proyectos'))
        
        clientes = Cliente.query.all()
        return render_template('editar_proyecto.html', proyecto=proyecto, clientes=clientes)
    
    @app.route('/proyectos/eliminar/<int:id>')
    @login_required
    def eliminar_proyecto(id):
        proyecto = Proyecto.query.get_or_404(id)
        db.session.delete(proyecto)
        db.session.commit()
        flash('Proyecto eliminado exitosamente', 'success')
        return redirect(url_for('proyectos'))
    
    # Gestión de Planos
    @app.route('/planos')
    @login_required
    def planos():
        search = request.args.get('search', '')
        tipo = request.args.get('tipo', '')
        
        query = Plano.query.join(Proyecto).join(Cliente)
        
        if search:
            query = query.filter(
                db.or_(
                    Plano.nombre_plano.contains(search),
                    Proyecto.nombre_proyecto.contains(search),
                    Cliente.nombre.contains(search)
                )
            )
        
        if tipo:
            query = query.join(TipoPlano).filter(TipoPlano.id_tipo_plano == tipo)
        
        planos = query.all()
        tipos_plano = TipoPlano.query.all()
        
        return render_template('planos.html', planos=planos, tipos_plano=tipos_plano, search=search, tipo=tipo)
    
    @app.route('/planos/subir', methods=['GET', 'POST'])
    @login_required
    def subir_plano():
        if request.method == 'POST':
            try:
                # Validar que se haya enviado un archivo
                if 'archivo' not in request.files:
                    flash('No se seleccionó ningún archivo', 'error')
                    proyectos = Proyecto.query.all()
                    tipos_plano = TipoPlano.query.all()
                    return render_template('subir_plano.html', proyectos=proyectos, tipos_plano=tipos_plano)
                
                archivo = request.files['archivo']
                if archivo.filename == '':
                    flash('No se seleccionó ningún archivo', 'error')
                    proyectos = Proyecto.query.all()
                    tipos_plano = TipoPlano.query.all()
                    return render_template('subir_plano.html', proyectos=proyectos, tipos_plano=tipos_plano)
                
                # Validar tipo de archivo
                if archivo and allowed_file(archivo.filename):
                    filename = secure_filename(archivo.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    
                    # Crear directorio si no existe (usar ruta absoluta)
                    upload_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_path, exist_ok=True)
                    
                    # Guardar archivo
                    file_path = os.path.join(upload_path, filename)
                    archivo.save(file_path)
                    
                    # Crear registro en base de datos
                    plano = Plano(
                        id_proyecto=int(request.form['id_proyecto']),
                        id_tipo_plano=int(request.form['id_tipo_plano']),
                        id_usuario=current_user.id_usuario,
                        nombre_plano=request.form['nombre_plano'],
                        archivo=filename
                    )
                    db.session.add(plano)
                    db.session.commit()
                    
                    flash('Plano subido exitosamente', 'success')
                    return redirect(url_for('planos'))
                else:
                    flash('Tipo de archivo no permitido. Formatos válidos: PDF, DWG, DXF, JPG, PNG', 'error')
                    proyectos = Proyecto.query.all()
                    tipos_plano = TipoPlano.query.all()
                    return render_template('subir_plano.html', proyectos=proyectos, tipos_plano=tipos_plano)
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Error al subir el plano: {str(e)}', 'error')
                proyectos = Proyecto.query.all()
                tipos_plano = TipoPlano.query.all()
                return render_template('subir_plano.html', proyectos=proyectos, tipos_plano=tipos_plano)
        
        proyectos = Proyecto.query.all()
        tipos_plano = TipoPlano.query.all()
        return render_template('subir_plano.html', proyectos=proyectos, tipos_plano=tipos_plano)
    
    @app.route('/planos/ver/<int:id>')
    @login_required
    def ver_plano(id):
        plano = Plano.query.get_or_404(id)
        archivo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], plano.archivo))
        
        if os.path.exists(archivo_path):
            return send_file(archivo_path, as_attachment=False)
        else:
            flash('Archivo no encontrado', 'error')
            return redirect(url_for('planos'))
    
    @app.route('/planos/descargar/<int:id>')
    @login_required
    def descargar_plano(id):
        plano = Plano.query.get_or_404(id)
        archivo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], plano.archivo))
        
        if os.path.exists(archivo_path):
            return send_file(archivo_path, as_attachment=True, download_name=plano.nombre_plano)
        else:
            flash('Archivo no encontrado', 'error')
            return redirect(url_for('planos'))
    
    @app.route('/planos/eliminar/<int:id>')
    @login_required
    def eliminar_plano(id):
        plano = Plano.query.get_or_404(id)
        archivo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], plano.archivo))
        
        # Eliminar archivo físico
        if os.path.exists(archivo_path):
            os.remove(archivo_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(plano)
        db.session.commit()
        flash('Plano eliminado exitosamente', 'success')
        return redirect(url_for('planos'))
    
    @app.route('/planos/detalle/<int:id>')
    @login_required
    def detalle_plano(id):
        plano = Plano.query.get_or_404(id)
        return render_template('detalle_plano.html', plano=plano)
    
    @app.route('/planos/buscar')
    @login_required
    def buscar_planos():
        # Búsqueda avanzada
        nombre = request.args.get('nombre', '')
        proyecto = request.args.get('proyecto', '')
        tipo = request.args.get('tipo', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        
        query = Plano.query.join(Proyecto).join(Cliente)
        
        if nombre:
            query = query.filter(Plano.nombre_plano.contains(nombre))
        
        if proyecto:
            query = query.filter(Proyecto.nombre_proyecto.contains(proyecto))
        
        if tipo:
            query = query.join(TipoPlano).filter(TipoPlano.id_tipo_plano == tipo)
        
        if fecha_desde:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Plano.fecha_subida >= fecha_desde_obj)
        
        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            query = query.filter(Plano.fecha_subida <= fecha_hasta_obj)
        
        planos = query.all()
        tipos_plano = TipoPlano.query.all()
        
        return render_template('buscar_planos.html', 
                             planos=planos, 
                             tipos_plano=tipos_plano,
                             nombre=nombre,
                             proyecto=proyecto,
                             tipo=tipo,
                             fecha_desde=fecha_desde,
                             fecha_hasta=fecha_hasta)
    
    # Gestión de Inventario
    @app.route('/inventario')
    @login_required
    def inventario():
        search = request.args.get('search', '')
        categoria = request.args.get('categoria', '')
        
        query = Inventario.query.join(Material)
        
        if search:
            query = query.filter(
                db.or_(
                    Material.nombre_material.contains(search),
                    Material.descripcion.contains(search)
                )
            )
        
        if categoria:
            query = query.filter(Material.categoria == categoria)
        
        inventarios = query.all()
        
        # Obtener materiales con stock bajo
        materiales_bajo_stock = Inventario.query.join(Material).filter(
            Inventario.cantidad <= Material.stock_minimo
        ).all()
        
        return render_template('inventario.html', 
                             inventarios=inventarios, 
                             materiales_bajo_stock=materiales_bajo_stock,
                             search=search,
                             categoria=categoria)
    
    @app.route('/inventario/materiales')
    @login_required
    def materiales():
        search = request.args.get('search', '')
        categoria = request.args.get('categoria', '')
        
        query = Material.query
        
        if search:
            query = query.filter(
                db.or_(
                    Material.nombre_material.contains(search),
                    Material.descripcion.contains(search)
                )
            )
        
        if categoria:
            query = query.filter(Material.categoria == categoria)
        
        materiales = query.filter(Material.activo == True).all()
        
        return render_template('materiales.html', materiales=materiales, search=search, categoria=categoria)
    
    @app.route('/inventario/materiales/crear', methods=['GET', 'POST'])
    @login_required
    def crear_material():
        if request.method == 'POST':
            material = Material(
                nombre_material=request.form['nombre_material'],
                descripcion=request.form['descripcion'],
                categoria=request.form['categoria'],
                subcategoria=request.form.get('subcategoria', ''),
                precio_unitario=float(request.form['precio_unitario']),
                precio_compra=float(request.form.get('precio_compra', 0)),
                unidad_medida=request.form['unidad_medida'],
                stock_minimo=int(request.form['stock_minimo'])
            )
            db.session.add(material)
            db.session.flush()
            
            # Crear registro de inventario inicial
            inventario = Inventario(
                id_material=material.id_material,
                cantidad=int(request.form.get('cantidad_inicial', 0)),
                ubicacion=request.form.get('ubicacion', '')
            )
            db.session.add(inventario)
            db.session.commit()
            
            flash('Material creado exitosamente', 'success')
            return redirect(url_for('materiales'))
        
        return render_template('crear_material.html')
    
    @app.route('/inventario/materiales/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_material(id):
        material = Material.query.get_or_404(id)
        
        if request.method == 'POST':
            material.nombre_material = request.form['nombre_material']
            material.descripcion = request.form['descripcion']
            material.categoria = request.form['categoria']
            material.subcategoria = request.form.get('subcategoria', '')
            material.precio_unitario = float(request.form['precio_unitario'])
            material.precio_compra = float(request.form.get('precio_compra', 0))
            material.unidad_medida = request.form['unidad_medida']
            material.stock_minimo = int(request.form['stock_minimo'])
            db.session.commit()
            
            flash('Material actualizado exitosamente', 'success')
            return redirect(url_for('materiales'))
        
        return render_template('editar_material.html', material=material)
    
    @app.route('/inventario/materiales/eliminar/<int:id>')
    @login_required
    def eliminar_material(id):
        material = Material.query.get_or_404(id)
        material.activo = False
        db.session.commit()
        flash('Material desactivado exitosamente', 'success')
        return redirect(url_for('materiales'))
    
    @app.route('/inventario/ajustar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def ajustar_inventario(id):
        inventario = Inventario.query.get_or_404(id)
        
        if request.method == 'POST':
            tipo_ajuste = request.form['tipo_ajuste']
            cantidad = int(request.form['cantidad'])
            
            if tipo_ajuste == 'entrada':
                inventario.cantidad += cantidad
            elif tipo_ajuste == 'salida':
                if inventario.cantidad >= cantidad:
                    inventario.cantidad -= cantidad
                else:
                    flash('No hay suficiente stock para realizar la salida', 'error')
                    return redirect(url_for('inventario'))
            elif tipo_ajuste == 'ajuste':
                inventario.cantidad = cantidad
            
            inventario.ubicacion = request.form.get('ubicacion', inventario.ubicacion)
            inventario.fecha_actualizacion = datetime.utcnow()
            db.session.commit()
            
            flash('Inventario ajustado exitosamente', 'success')
            return redirect(url_for('inventario'))
        
        return render_template('ajustar_inventario.html', inventario=inventario)
    
    # Gestión de Ventas
    @app.route('/ventas')
    @login_required
    def ventas():
        search = request.args.get('search', '')
        estado = request.args.get('estado', '')
        
        query = Venta.query.join(Cliente)
        
        if search:
            query = query.filter(
                db.or_(
                    Cliente.nombre.contains(search),
                    Cliente.apellido.contains(search)
                )
            )
        
        if estado:
            query = query.filter(Venta.estado == estado)
        
        ventas = query.order_by(Venta.fecha_venta.desc()).all()
        
        return render_template('ventas.html', ventas=ventas, search=search, estado=estado)
    
    @app.route('/ventas/crear', methods=['GET', 'POST'])
    @login_required
    def crear_venta():
        if request.method == 'POST':
            # Crear venta
            venta = Venta(
                id_cliente=request.form['id_cliente'],
                id_usuario=current_user.id_usuario,
                metodo_pago=request.form.get('metodo_pago', 'efectivo'),
                notas=request.form.get('notas', ''),
                impuesto=float(request.form.get('impuesto', 0)),
                descuento=float(request.form.get('descuento', 0)),
                total=0
            )
            db.session.add(venta)
            db.session.flush()
            
            # Procesar detalles de venta (servicios: planos y renderizados)
            descripciones = request.form.getlist('descripcion[]')
            cantidades = request.form.getlist('cantidad[]')
            precios = request.form.getlist('precio[]')
            
            for i in range(len(descripciones)):
                if descripciones[i] and cantidades[i] and precios[i]:
                    cantidad = int(cantidades[i])
                    precio = float(precios[i])
                    
                    # Crear detalle de venta (sin verificar inventario, son servicios)
                    detalle = DetalleVenta(
                        id_venta=venta.id_venta,
                        id_material=None,  # No hay material asociado
                        descripcion=descripciones[i],
                        cantidad=cantidad,
                        precio_unitario=precio
                    )
                    db.session.add(detalle)
            
            # Calcular total
            venta.calcular_total()
            db.session.commit()
            
            flash('Venta registrada exitosamente', 'success')
            return redirect(url_for('ventas'))
        
        clientes = Cliente.query.all()
        tipos_plano = TipoPlano.query.all()
        return render_template('crear_venta.html', clientes=clientes, tipos_plano=tipos_plano)
    
    @app.route('/ventas/ver/<int:id>')
    @login_required
    def ver_venta(id):
        venta = Venta.query.get_or_404(id)
        return render_template('ver_venta.html', venta=venta)
    
    @app.route('/ventas/eliminar/<int:id>')
    @login_required
    def eliminar_venta(id):
        venta = Venta.query.get_or_404(id)
        
        # Cancelar venta (ya no hay inventario que devolver, son servicios)
        venta.estado = 'cancelada'
        db.session.commit()
        flash('Venta cancelada exitosamente', 'success')
        return redirect(url_for('ventas'))
    
    @app.route('/ventas/imprimir/<int:id>')
    @login_required
    def imprimir_venta(id):
        venta = Venta.query.get_or_404(id)
        
        # Crear PDF de factura
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # Encabezado
        pdf.cell(0, 10, 'ASPLOT CENTER', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 5, 'Factura de Venta', 0, 1, 'C')
        pdf.ln(5)
        
        # Información de la venta
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 6, 'Factura No:', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(60, 6, f'{venta.id_venta:06d}', 0, 0)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 6, 'Fecha:', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, venta.fecha_venta.strftime('%Y-%m-%d %H:%M'), 0, 1)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 6, 'Cliente:', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, venta.cliente.nombre_completo, 0, 1)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 6, 'Atendido por:', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, venta.usuario.nombre_usuario, 0, 1)
        pdf.ln(5)
        
        # Tabla de detalles
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, 'Descripcion', 1, 0, 'C')
        pdf.cell(30, 8, 'Cantidad', 1, 0, 'C')
        pdf.cell(30, 8, 'Precio Unit.', 1, 0, 'C')
        pdf.cell(30, 8, 'Subtotal', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 9)
        for detalle in venta.detalle_ventas:
            pdf.cell(80, 6, detalle.descripcion[:40], 1, 0)
            pdf.cell(30, 6, str(detalle.cantidad), 1, 0, 'C')
            pdf.cell(30, 6, f'${detalle.precio_unitario:.2f}', 1, 0, 'R')
            pdf.cell(30, 6, f'${detalle.subtotal:.2f}', 1, 1, 'R')
        
        # Totales
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(140, 6, 'Subtotal:', 0, 0, 'R')
        pdf.cell(30, 6, f'${venta.subtotal:.2f}', 0, 1, 'R')
        
        if venta.impuesto > 0:
            pdf.cell(140, 6, 'Impuesto:', 0, 0, 'R')
            pdf.cell(30, 6, f'${venta.impuesto:.2f}', 0, 1, 'R')
        
        if venta.descuento > 0:
            pdf.cell(140, 6, 'Descuento:', 0, 0, 'R')
            pdf.cell(30, 6, f'-${venta.descuento:.2f}', 0, 1, 'R')
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(140, 8, 'TOTAL:', 0, 0, 'R')
        pdf.cell(30, 8, f'${venta.total:.2f}', 0, 1, 'R')
        
        # Generar respuesta
        output = io.BytesIO()
        pdf.output(output)
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'factura_{venta.id_venta:06d}.pdf',
            mimetype='application/pdf'
        )
    
    # Gestión de Reportes
    @app.route('/reportes')
    @login_required
    def reportes():
        return render_template('reportes.html')
    
    @app.route('/reportes/generar', methods=['POST'])
    @login_required
    def generar_reporte():
        tipo_reporte = request.form['tipo_reporte']
        periodo = request.form['periodo']
        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        if tipo_reporte == 'clientes':
            pdf.cell(0, 10, 'Reporte de Clientes', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(40, 10, 'Nombre', 1, 0, 'C')
            pdf.cell(60, 10, 'Email', 1, 0, 'C')
            pdf.cell(40, 10, 'Teléfono', 1, 0, 'C')
            pdf.cell(50, 10, 'Dirección', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            clientes = Cliente.query.all()
            for cliente in clientes:
                pdf.cell(40, 10, cliente.nombre_completo, 1, 0)
                pdf.cell(60, 10, cliente.email, 1, 0)
                pdf.cell(40, 10, cliente.telefono, 1, 0)
                pdf.cell(50, 10, cliente.direccion[:45], 1, 1)
        
        elif tipo_reporte == 'proyectos':
            pdf.cell(0, 10, 'Reporte de Proyectos', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(50, 10, 'Proyecto', 1, 0, 'C')
            pdf.cell(40, 10, 'Cliente', 1, 0, 'C')
            pdf.cell(30, 10, 'Estado', 1, 0, 'C')
            pdf.cell(30, 10, 'Inicio', 1, 0, 'C')
            pdf.cell(30, 10, 'Fin', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            proyectos = Proyecto.query.join(Cliente).all()
            for proyecto in proyectos:
                pdf.cell(50, 10, proyecto.nombre_proyecto[:25], 1, 0)
                pdf.cell(40, 10, proyecto.cliente.nombre_completo[:20], 1, 0)
                pdf.cell(30, 10, proyecto.estado, 1, 0)
                pdf.cell(30, 10, str(proyecto.fecha_inicio), 1, 0)
                pdf.cell(30, 10, str(proyecto.fecha_fin), 1, 1)
        
        elif tipo_reporte == 'ventas':
            pdf.cell(0, 10, 'Reporte de Ventas', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(30, 10, 'ID Venta', 1, 0, 'C')
            pdf.cell(50, 10, 'Cliente', 1, 0, 'C')
            pdf.cell(40, 10, 'Fecha', 1, 0, 'C')
            pdf.cell(30, 10, 'Total', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            ventas = Venta.query.join(Cliente).all()
            for venta in ventas:
                pdf.cell(30, 10, str(venta.id_venta), 1, 0)
                pdf.cell(50, 10, venta.cliente.nombre_completo[:25], 1, 0)
                pdf.cell(40, 10, str(venta.fecha_venta.date()), 1, 0)
                pdf.cell(30, 10, f"${venta.total}", 1, 1)
        
        elif tipo_reporte == 'inventario':
            pdf.cell(0, 10, 'Reporte de Inventario', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(60, 10, 'Material', 1, 0, 'C')
            pdf.cell(40, 10, 'Categoría', 1, 0, 'C')
            pdf.cell(30, 10, 'Cantidad', 1, 0, 'C')
            pdf.cell(30, 10, 'Precio Unit.', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 10)
            inventarios = Inventario.query.join(Material).filter(Material.activo == True).all()
            for inventario in inventarios:
                pdf.cell(60, 10, inventario.material.nombre_material[:30], 1, 0)
                pdf.cell(40, 10, inventario.material.categoria[:20], 1, 0)
                pdf.cell(30, 10, str(inventario.cantidad), 1, 0, 'C')
                pdf.cell(30, 10, f"${inventario.material.precio_unitario:.2f}", 1, 1, 'R')
        
        elif tipo_reporte == 'planos':
            pdf.cell(0, 10, 'Reporte de Planos', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(50, 8, 'Nombre Plano', 1, 0, 'C')
            pdf.cell(40, 8, 'Proyecto', 1, 0, 'C')
            pdf.cell(30, 8, 'Tipo', 1, 0, 'C')
            pdf.cell(35, 8, 'Cliente', 1, 0, 'C')
            pdf.cell(35, 8, 'Fecha', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 8)
            planos = Plano.query.join(Proyecto).join(Cliente).join(TipoPlano).all()
            for plano in planos:
                pdf.cell(50, 6, plano.nombre_plano[:25], 1, 0)
                pdf.cell(40, 6, plano.proyecto.nombre_proyecto[:20], 1, 0)
                pdf.cell(30, 6, plano.tipo_plano.nombre_tipo[:15], 1, 0)
                pdf.cell(35, 6, plano.proyecto.cliente.nombre_completo[:18], 1, 0)
                pdf.cell(35, 6, plano.fecha_subida.strftime('%Y-%m-%d'), 1, 1, 'C')
        
        elif tipo_reporte == 'planos_proyecto':
            id_proyecto = request.form.get('id_proyecto')
            proyecto = Proyecto.query.get(id_proyecto)
            
            pdf.cell(0, 10, f'Reporte de Planos - {proyecto.nombre_proyecto}', 0, 1, 'C')
            pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 6, 'Cliente:', 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, proyecto.cliente.nombre_completo, 0, 1)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(40, 6, 'Estado:', 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, proyecto.estado.title(), 0, 1)
            pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(70, 8, 'Nombre Plano', 1, 0, 'C')
            pdf.cell(40, 8, 'Tipo', 1, 0, 'C')
            pdf.cell(40, 8, 'Usuario', 1, 0, 'C')
            pdf.cell(40, 8, 'Fecha Subida', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 9)
            planos = Plano.query.filter_by(id_proyecto=id_proyecto).all()
            for plano in planos:
                pdf.cell(70, 6, plano.nombre_plano[:35], 1, 0)
                pdf.cell(40, 6, plano.tipo_plano.nombre_tipo, 1, 0)
                pdf.cell(40, 6, plano.usuario.nombre_usuario, 1, 0)
                pdf.cell(40, 6, plano.fecha_subida.strftime('%Y-%m-%d'), 1, 1, 'C')
            
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f'Total de planos: {len(planos)}', 0, 1)
        
        elif tipo_reporte == 'stock_bajo':
            pdf.cell(0, 10, 'Reporte de Stock Bajo', 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(60, 8, 'Material', 1, 0, 'C')
            pdf.cell(30, 8, 'Cantidad', 1, 0, 'C')
            pdf.cell(30, 8, 'Stock Min.', 1, 0, 'C')
            pdf.cell(40, 8, 'Ubicación', 1, 1, 'C')
            
            pdf.set_font('Arial', '', 9)
            inventarios = Inventario.query.join(Material).filter(
                Material.activo == True,
                Inventario.cantidad <= Material.stock_minimo
            ).all()
            
            for inventario in inventarios:
                pdf.cell(60, 6, inventario.material.nombre_material[:30], 1, 0)
                pdf.cell(30, 6, str(inventario.cantidad), 1, 0, 'C')
                pdf.cell(30, 6, str(inventario.material.stock_minimo), 1, 0, 'C')
                pdf.cell(40, 6, (inventario.ubicacion or 'N/A')[:20], 1, 1)
        
        # Generar respuesta
        output = io.BytesIO()
        pdf.output(output)
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'reporte_{tipo_reporte}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    
    # Gestión de Usuarios
    @app.route('/usuarios')
    @login_required
    def usuarios():
        if not current_user.es_administrador:
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('dashboard'))
        
        search = request.args.get('search', '')
        rol = request.args.get('rol', '')
        
        query = Usuario.query.filter(Usuario.activo == True)
        
        if search:
            query = query.filter(
                db.or_(
                    Usuario.nombre_usuario.contains(search),
                    Usuario.email.contains(search),
                    Usuario.nombre_completo.contains(search)
                )
            )
        
        if rol:
            query = query.filter(Usuario.rol == rol)
        
        usuarios = query.all()
        
        return render_template('usuarios.html', usuarios=usuarios, search=search, rol=rol)
    
    @app.route('/usuarios/crear', methods=['GET', 'POST'])
    @login_required
    def crear_usuario():
        if not current_user.es_administrador:
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            # Verificar si el usuario ya existe
            if Usuario.query.filter_by(email=request.form['email']).first():
                flash('El email ya está registrado', 'error')
                return redirect(url_for('crear_usuario'))
            
            if Usuario.query.filter_by(nombre_usuario=request.form['nombre_usuario']).first():
                flash('El nombre de usuario ya está en uso', 'error')
                return redirect(url_for('crear_usuario'))
            
            usuario = Usuario(
                nombre_usuario=request.form['nombre_usuario'],
                email=request.form['email'],
                rol=request.form['rol'],
                nombre_completo=request.form.get('nombre_completo', ''),
                telefono=request.form.get('telefono', ''),
                direccion=request.form.get('direccion', ''),
                activo=True
            )
            usuario.set_password(request.form['password'])
            db.session.add(usuario)
            db.session.commit()
            
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('usuarios'))
        
        return render_template('crear_usuario.html')
    
    @app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_usuario(id):
        if not current_user.es_administrador:
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('dashboard'))
        
        usuario = Usuario.query.get_or_404(id)
        
        if request.method == 'POST':
            # Verificar email único
            email_existente = Usuario.query.filter(
                Usuario.email == request.form['email'],
                Usuario.id_usuario != id
            ).first()
            if email_existente:
                flash('El email ya está registrado', 'error')
                return redirect(url_for('editar_usuario', id=id))
            
            usuario.nombre_usuario = request.form['nombre_usuario']
            usuario.email = request.form['email']
            usuario.rol = request.form['rol']
            usuario.nombre_completo = request.form.get('nombre_completo', '')
            usuario.telefono = request.form.get('telefono', '')
            usuario.direccion = request.form.get('direccion', '')
            
            if request.form.get('password'):
                usuario.set_password(request.form['password'])
            
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('usuarios'))
        
        return render_template('editar_usuario.html', usuario=usuario)
    
    @app.route('/usuarios/eliminar/<int:id>')
    @login_required
    def eliminar_usuario(id):
        if not current_user.es_administrador:
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('dashboard'))
        
        if id == current_user.id_usuario:
            flash('No puedes eliminar tu propio usuario', 'error')
            return redirect(url_for('usuarios'))
        
        usuario = Usuario.query.get_or_404(id)
        usuario.activo = False
        db.session.commit()
        flash('Usuario desactivado exitosamente', 'success')
        return redirect(url_for('usuarios'))
    
    # Configuración
    @app.route('/configuracion')
    @login_required
    def configuracion():
        return render_template('configuracion.html', usuario=current_user)
    
    @app.route('/configuracion/actualizar', methods=['POST'])
    @login_required
    def actualizar_configuracion():
        usuario = current_user
        usuario.nombre_usuario = request.form['nombre_usuario']
        usuario.email = request.form['email']
        usuario.nombre_completo = request.form.get('nombre_completo', '')
        usuario.telefono = request.form.get('telefono', '')
        usuario.direccion = request.form.get('direccion', '')
        
        if request.form.get('password'):
            usuario.set_password(request.form['password'])
        
        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
        return redirect(url_for('configuracion'))
    
    # Funciones auxiliares
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

