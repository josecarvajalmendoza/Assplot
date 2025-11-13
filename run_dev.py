# Configuración del servidor de desarrollo
# Ejecutar con: python run_dev.py

from app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    
    # Configuración del servidor
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("🚀 Iniciando As Plot Center...")
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"🔧 Modo debug: {'Activado' if debug else 'Desactivado'}")
    print("📋 Credenciales: admin@asplot.com / admin123")
    print("⏹️  Para detener: Ctrl+C")
    print("-" * 50)
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido. ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error del servidor: {e}")





