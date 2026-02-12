import qrcode
import os
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
# URL de tu web (Vercel)
BASE_URL = "https://demo-trazabilidad-nettalco.vercel.app"
CARPETA_SALIDA = "stickers_qr"
# ==========================================

def crear_sticker(titulo_visual, hash_id):
    """
    titulo_visual: El texto que sale abajo (ej: TicketBar)
    hash_id: El nombre del archivo JSON (sin .json) que buscará la web
    """
    
    # 1. Crear URL
    url_final = f"{BASE_URL}/index.html?id={hash_id}"
    print(f"🎨 Creando QR para: {titulo_visual}")
    print(f"   🔗 Link: {url_final}")

    # 2. Generar QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url_final)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # 3. Preparar Lienzo (QR + Espacio para texto)
    ancho_qr, alto_qr = img_qr.size
    alto_texto = 60 # Un poco más de espacio
    lienzo = Image.new('RGB', (ancho_qr, alto_qr + alto_texto), 'white')
    lienzo.paste(img_qr, (0, 0))

    # 4. Dibujar Texto
    d = ImageDraw.Draw(lienzo)
    try:
        # Intenta usar Arial, si no usa la default
        font = ImageFont.truetype("arial.ttf", 26)
    except:
        font = ImageFont.load_default()

    texto = f"ID: {titulo_visual}"
    
    # Centrar texto (Lógica moderna de Pillow)
    try:
        left, top, right, bottom = d.textbbox((0, 0), texto, font=font)
        ancho_texto = right - left
        alto_fuente = bottom - top
    except:
        # Fallback para versiones viejas de Pillow
        ancho_texto, alto_fuente = d.textsize(texto, font=font)

    x = (ancho_qr - ancho_texto) / 2
    y = alto_qr + (alto_texto - alto_fuente) / 2 - 5 # Centrado vertical ajustado
    
    d.text((x, y), texto, fill="black", font=font)

    # 5. Guardar
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)
    
    nombre_archivo = f"{CARPETA_SALIDA}/{titulo_visual}.png"
    lienzo.save(nombre_archivo)
    
    # Imprimir ruta absoluta para encontrarlo facil
    print(f"   ✅ Guardado en: {os.path.abspath(nombre_archivo)}\n")

# --- BLOQUE DE PRUEBA ---
if __name__ == "__main__":
    
    # ⚠️ IMPORTANTE: 
    # 1. Ve a tu carpeta 'cola_de_envio'
    # 2. Copia el NOMBRE de un archivo .json (ese es el Hash)
    # 3. Pégalo aquí abajo en 'hash'
    
    lote = [
        {
            "tick": "092686113013", 
            "hash": "json_rescatados" 
        }
    ]

    print("🏭 INICIANDO GENERACIÓN DE STICKERS...\n")
    
    if lote[0]["hash"] == "REEMPLAZAR_CON_NOMBRE_DEL_JSON_QUE_ACABAS_DE_CREAR":
        print("❌ ALERTA: No has puesto el Hash del JSON en el script.")
        print("   Ve a la carpeta 'cola_de_envio', copia el nombre de un archivo .json y pégalo en el script.")
    else:
        for item in lote:
            crear_sticker(item["tick"], item["hash"])