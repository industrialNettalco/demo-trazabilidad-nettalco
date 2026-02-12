import subprocess
import os
import datetime

# CONFIGURACIÓN
# Asegúrate de que esta ruta sea la de tu repositorio LOCAL clonado
RUTA_REPO_GITHUB = r"C:\Users\aponce\Desktop\Piloto Nettalco\demo-trazabilidad-nettalco"
MENSAJE_COMMIT = f"Auto-Sync: Carga de datos {datetime.datetime.now()}"

def subir_cambios():
    print(f"🚀 Iniciando sincronización con GitHub...")
    
    try:
        # 1. Cambiar al directorio del repo
        os.chdir(RUTA_REPO_GITHUB)
        
        # 2. Agregar todos los archivos nuevos (JSONs)
        print("📦 Agregando archivos...")
        subprocess.run(["git", "add", "."], check=True)
        
        # 3. Guardar cambios (Commit)
        print("💾 Creando commit...")
        # El try/except es por si no hay nada nuevo que guardar
        try:
            subprocess.run(["git", "commit", "-m", MENSAJE_COMMIT], check=True)
        except subprocess.CalledProcessError:
            print("⚠️ Nada nuevo que subir.")
            return

        # 4. Subir a la nube (Push)
        print("☁️ Subiendo a GitHub (Push)...")
        subprocess.run(["git", "push"], check=True)
        
        print("✅ ¡Sincronización COMPLETADA! Los datos ya están en la web.")
        
    except Exception as e:
        print(f"❌ Error en la sincronización: {e}")
        print("💡 PISTA: Asegúrate de tener Internet y las credenciales de Git guardadas.")

if __name__ == "__main__":
    subir_cambios()