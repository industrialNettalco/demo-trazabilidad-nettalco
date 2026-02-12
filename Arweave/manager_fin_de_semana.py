import os
import subprocess
import shutil
import time

# --- CONFIGURACIÓN DE RECUPERACIÓN ---
# Como el 29 ya se hizo (aunque muchas veces), vamos con los que faltaron.
FECHAS_A_PROCESAR = [
    "2026-01-20",
    "2026-01-21",
    "2026-01-22",
    "2026-01-23",
    "2026-01-24"
]
    


# Rutas de carpetas
CARPETA_COLA = "cola_de_envio"
CARPETA_BACKUP_RAIZ = "BACKUP_FINDE"
ARCHIVO_REPORTE = "REPORTE_COSTOS_RECUPERACION.txt"
ARCHIVO_ENV = ".env"

def actualizar_env(fecha):
    """Reescribe el archivo .env con la nueva fecha (UTF-8 FORZADO)"""
    print(f"🔄 Actualizando .env para la fecha: {fecha}...")
    lines = []
    try:
        # LEER CON UTF-8
        with open(ARCHIVO_ENV, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # ESCRIBIR CON UTF-8
        with open(ARCHIVO_ENV, "w", encoding="utf-8") as f:
            found = False
            for line in lines:
                if line.startswith("TARGET_DATE="):
                    f.write(f"TARGET_DATE={fecha}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"\nTARGET_DATE={fecha}\n")
    except Exception as e:
        print(f"❌ Error CRÍTICO actualizando .env: {e}")
        # Si falla esto, detenemos el script para no repetir días
        raise e 

def registrar_log(mensaje):
    """Escribe en el reporte final (UTF-8 FORZADO)"""
    try:
        with open(ARCHIVO_REPORTE, "a", encoding="utf-8") as f:
            f.write(mensaje + "\n")
    except: pass
    print(mensaje)

def procesar_dia(fecha):
    start_time = time.time()
    banner = f"\n{'='*40}\n🚀 INICIANDO PROCESO PARA: {fecha}\n{'='*40}"
    registrar_log(banner)

    try:
        # 1. Configurar fecha (Si esto falla, se detiene el flujo)
        actualizar_env(fecha)
    except:
        return

    # 2. Ejecutar main_mariadb.py
    print(f"🔨 Ejecutando main_mariadb.py para {fecha}...")
    try:
        # capture_output=False deja que los prints salgan a consola en tiempo real
        subprocess.run(["python", "main_mariadb.py"], check=True)
        registrar_log(f"✅ Extracción completada para {fecha}.")
    except subprocess.CalledProcessError as e:
        registrar_log(f"❌ ERROR en main_mariadb.py para {fecha}: {e}")
        return 

    # 3. Ejecutar simulación de costos
    print(f"💰 Calculando costos para {fecha}...")
    try:
        # IMPORTANTE: errors='replace' evita que los emojis rompan el script en Windows
        resultado_simulacion = subprocess.check_output(
            ["node", "simulacion_costos.js"], 
            text=True, 
            shell=True, 
            encoding='utf-8', 
            errors='replace'
        )
        registrar_log(f"\n--- 📊 REPORTE DE COSTOS ({fecha}) ---\n{resultado_simulacion}\n----------------------------------")
    except Exception as e:
        registrar_log(f"⚠️ Error capturando output de simulación (pero se ejecutó): {e}")

    # 4. Mover archivos a Backup
    carpeta_destino = os.path.join(CARPETA_BACKUP_RAIZ, fecha)
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
    
    if os.path.exists(CARPETA_COLA):
        archivos_json = [f for f in os.listdir(CARPETA_COLA) if f.endswith('.json')]
        count = 0
        
        print(f"📦 Archivando {len(archivos_json)} archivos en {carpeta_destino}...")
        for archivo in archivos_json:
            src = os.path.join(CARPETA_COLA, archivo)
            dst = os.path.join(carpeta_destino, archivo)
            shutil.move(src, dst)
            count += 1
        
        registrar_log(f"💾 Se guardaron {count} archivos JSON en la carpeta de respaldo.")
    
    duration = (time.time() - start_time) / 3600
    registrar_log(f"🏁 Día {fecha} finalizado en {duration:.2f} horas.\n")

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    
    print("⏰ ¡El Manager de Recuperación ha iniciado!")

    # Limpiamos/Creamos el reporte
    with open(ARCHIVO_REPORTE, "w", encoding="utf-8") as f:
        f.write("📅 BITÁCORA DE RECUPERACIÓN - NETTALCO\n")

    for fecha in FECHAS_A_PROCESAR:
        procesar_dia(fecha)
        print(f"⏳ Esperando 5 segundos...\n")
        time.sleep(5)

    print("\n🎉 ¡RECUPERACIÓN COMPLETADA! 🎉")