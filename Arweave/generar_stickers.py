import qrcode
import os
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# ⚙️ CONFIGURACIÓN DE LA DEMO
# ==========================================
# Link antiguo
# BASE_URL = "https://industrialnettalco.github.io/demo-trazabilidad-nettalco"

# Link NUEVO y Rápido 👇
BASE_URL = "https://demo-trazabilidad-nettalco.vercel.app"
OUTPUT_FOLDER = "stickers_qr"
# ==========================================

def crear_sticker(tickbar, hash_id):
    """Genera un QR escaneable con el ID de la prenda abajo"""
    
    # 1. Armar el Link Mágico
    url_final = f"{BASE_URL}/index.html?id={hash_id}"
    print(f"🏷️  Generando: {tickbar}")

    # 2. Crear el QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url_final)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # 3. Agregar texto abajo (El ID Visual)
    ancho, alto = img_qr.size
    alto_texto = 50
    lienzo = Image.new('RGB', (ancho, alto + alto_texto), 'white')
    lienzo.paste(img_qr, (0, 0))

    # Dibujar texto
    d = ImageDraw.Draw(lienzo)
    # Intentamos cargar una fuente, si no usa la default
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    texto = f"ID: {tickbar}"
    
    # Truco para centrar el texto (bbox)
    bbox = d.textbbox((0, 0), texto, font=font)
    ancho_texto = bbox[2] - bbox[0]
    x = (ancho - ancho_texto) / 2
    y = alto + 10
    
    d.text((x, y), texto, fill="black", font=font)

    # 4. Guardar
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    lienzo.save(f"{OUTPUT_FOLDER}/{tickbar}.png")

# --- PRUEBA RÁPIDA ---
if __name__ == "__main__":
    # Usa aquí UN PAR de datos reales que veas en tu HeidiSQL o en los JSONs que se están creando
    lote_demo = [
        # {"tick": "ID_PRENDA_REAL", "hash": "HASH_REAL_DEL_JSON"},
        {"tick": "092640703069", "hash": "ff48d9ca5592d872113131718d83c5d8962ed2a26148830dee2062bd062a09ee"},
    ]

    print(f"🏭 Iniciando fábrica de stickers apuntando a: {BASE_URL}")
    for prenda in lote_demo:
        crear_sticker(prenda["tick"], prenda["hash"])
    
    print("✅ ¡Revisa la carpeta 'stickers_qr' y escanea con tu celular!")