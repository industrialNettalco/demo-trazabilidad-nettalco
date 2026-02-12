/**
 * SCRIPT DE SUBIDA INDIVIDUAL A ARWEAVE
 *
 * Uso: node subida_individual.js <ruta_al_json>
 * Ejemplo: node subida_individual.js ../data/092583907531.json
 */

const Irys = require("@irys/sdk");
const fs = require("fs");
const path = require("path");
require("dotenv").config();

// Configuración Irys
const IRYS_CONFIG = {
  network: "mainnet",
  token: "base-eth",
  key: process.env.PRIVATE_KEY,
  config: {
    providerUrl: "https://mainnet.base.org"
  }
};

// Ruta al archivo de mapeo
const ARWEAVE_MAP_FILE = path.join(__dirname, "..", "arweave_map.json");

/**
 * Carga el mapa actual de transacciones Arweave
 */
function cargarMapaArweave() {
  try {
    if (fs.existsSync(ARWEAVE_MAP_FILE)) {
      const data = fs.readFileSync(ARWEAVE_MAP_FILE, "utf-8");
      return JSON.parse(data);
    }
  } catch (error) {
    console.log("[!] No se pudo cargar arweave_map.json, creando nuevo mapa");
  }
  return {};
}

/**
 * Guarda el mapa actualizado de transacciones
 */
function guardarMapaArweave(mapa) {
  fs.writeFileSync(ARWEAVE_MAP_FILE, JSON.stringify(mapa, null, 2), "utf-8");
  console.log(`[OK] Mapa guardado en: ${ARWEAVE_MAP_FILE}`);
}

/**
 * Sube un archivo JSON a Arweave
 */
async function subirArchivoIndividual(rutaArchivo) {
  console.log("\n========================================");
  console.log("SUBIDA INDIVIDUAL A ARWEAVE");
  console.log("========================================\n");

  // Validar que el archivo existe
  if (!fs.existsSync(rutaArchivo)) {
    console.error(`[ERROR] El archivo no existe: ${rutaArchivo}`);
    process.exit(1);
  }

  // Validar que sea un JSON
  if (!rutaArchivo.endsWith(".json")) {
    console.error("[ERROR] El archivo debe ser un JSON (.json)");
    process.exit(1);
  }

  const nombreArchivo = path.basename(rutaArchivo, ".json");
  console.log(`[+] Archivo a subir: ${nombreArchivo}.json`);

  // Leer el contenido del archivo
  let contenidoJSON;
  try {
    const contenido = fs.readFileSync(rutaArchivo, "utf-8");
    contenidoJSON = JSON.parse(contenido);
    console.log(`[OK] JSON válido cargado`);
  } catch (error) {
    console.error(`[ERROR] El archivo no es un JSON válido: ${error.message}`);
    process.exit(1);
  }

  // Validar que existe PRIVATE_KEY
  if (!process.env.PRIVATE_KEY) {
    console.error("[ERROR] No se encontró PRIVATE_KEY en .env");
    process.exit(1);
  }

  console.log("\n[+] Conectando a Irys (Arweave)...");

  try {
    // Conectar a Irys
    const irys = new Irys(IRYS_CONFIG);
    console.log("[OK] Conectado a Irys");

    // Obtener balance
    const balance = await irys.getLoadedBalance();
    console.log(`[i] Balance en nodo: ${irys.utils.fromAtomic(balance)} ETH`);

    // Calcular costo
    const dataSize = Buffer.byteLength(JSON.stringify(contenidoJSON));
    const price = await irys.getPrice(dataSize);
    const costoETH = irys.utils.fromAtomic(price);
    console.log(`[i] Tamaño: ${dataSize} bytes`);
    console.log(`[i] Costo estimado: ${costoETH} ETH`);

    // Verificar solvencia
    if (balance.lt(price)) {
      console.log("\n[!] Balance insuficiente en el nodo");
      console.log("[+] Intentando fondear desde wallet...");

      const walletBalance = await irys.utils.getBigNumber(await irys.token.getBalance());

      if (walletBalance.lt(price)) {
        console.error("[ERROR] Fondos insuficientes en wallet");
        console.error(`   Necesario: ${costoETH} ETH`);
        console.error(`   Disponible: ${irys.utils.fromAtomic(walletBalance)} ETH`);
        process.exit(1);
      }

      await irys.fund(price);
      console.log("[OK] Nodo fondeado exitosamente");
    }

    // Confirmar subida
    console.log("\n========================================");
    console.log("¿Deseas continuar con la subida?");
    console.log(`   Archivo: ${nombreArchivo}.json`);
    console.log(`   Costo: ${costoETH} ETH`);
    console.log("========================================");
    console.log("Escribe 'si' para confirmar:");

    // Esperar confirmación del usuario
    const readline = require("readline");
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    const respuesta = await new Promise(resolve => {
      rl.question("", answer => {
        rl.close();
        resolve(answer);
      });
    });

    if (respuesta.toLowerCase() !== "si") {
      console.log("\n[!] Subida cancelada por el usuario");
      process.exit(0);
    }

    // Subir a Arweave
    console.log("\n[+] Subiendo a Arweave...");

    const tags = [
      { name: "Content-Type", value: "application/json" },
      { name: "App", value: "Nettalco-Trazabilidad" },
      { name: "Tickbarr", value: nombreArchivo }
    ];

    const receipt = await irys.upload(JSON.stringify(contenidoJSON), { tags });

    console.log("\n========================================");
    console.log("SUBIDA EXITOSA");
    console.log("========================================");
    console.log(`   Archivo: ${nombreArchivo}.json`);
    console.log(`   TX ID: ${receipt.id}`);
    console.log(`   URL Arweave: https://arweave.net/${receipt.id}`);
    console.log(`   URL ViewBlock: https://viewblock.io/arweave/tx/${receipt.id}`);
    console.log("========================================\n");

    // Actualizar mapa de Arweave
    console.log("[+] Actualizando arweave_map.json...");
    const mapa = cargarMapaArweave();
    mapa[nombreArchivo] = receipt.id;
    guardarMapaArweave(mapa);

    console.log("\n[OK] PROCESO COMPLETADO");
    console.log(`[i] El archivo ya está vinculado en el sistema`);
    console.log(`[i] URL para verificar: ${process.env.VERCEL_URL || 'tu-dominio'}/index.html?id=${nombreArchivo}`);

  } catch (error) {
    console.error("\n[ERROR] Falló la subida a Arweave:");
    console.error(error);
    process.exit(1);
  }
}

// Ejecutar script
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log("\n========================================");
    console.log("USO DEL SCRIPT");
    console.log("========================================");
    console.log("\nnode subida_individual.js <ruta_al_json>\n");
    console.log("Ejemplos:");
    console.log("  node subida_individual.js ../data/092583907531.json");
    console.log("  node subida_individual.js json_rescatados.json");
    console.log("\nEl script:");
    console.log("  1. Sube el JSON a Arweave");
    console.log("  2. Obtiene el Transaction ID");
    console.log("  3. Actualiza arweave_map.json automáticamente");
    console.log("========================================\n");
    process.exit(0);
  }

  const rutaArchivo = path.resolve(args[0]);
  subirArchivoIndividual(rutaArchivo);
}

module.exports = { subirArchivoIndividual };
