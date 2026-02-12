require("dotenv").config();
const Irys = require("@irys/sdk");
const fs = require("fs");
const path = require("path");

async function obtenerPrecioEther() {
    try {
        const respuesta = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd");
        const datos = await respuesta.json();
        return datos.ethereum.usd;
    } catch (error) {
        return 0;
    }
}

async function main() {
    console.log("\n===================================================");
    console.log("🧪 NETTALCO - SIMULADOR DE COSTOS (MODO AHORRO)");
    console.log("===================================================");

    const carpetaEntrada = "./cola_de_envio";
    
    if (!fs.existsSync(carpetaEntrada)) {
        console.log("❌ No existe la carpeta 'cola_de_envio'.");
        return;
    }
    
    const archivos = fs.readdirSync(carpetaEntrada).filter(file => file.endsWith('.json'));
    
    if (archivos.length === 0) {
        console.log("✅ Carpeta vacía. Nada que cotizar.");
        return;
    }

    // Conexión solo para consultar precios (No requiere saldo)
    const irys = new Irys.default({
        network: "mainnet",
        token: "base-eth",
        key: process.env.PRIVATE_KEY, // Se requiere para inicializar, pero no gastará nada
        config: { providerUrl: "https://mainnet.base.org" }
    });

    console.log(`📦 Analizando ${archivos.length} archivos generados...`);
    
    let pesoTotalBytes = 0;
    for (const archivo of archivos) {
        const ruta = path.join(carpetaEntrada, archivo);
        pesoTotalBytes += fs.statSync(ruta).size;
    }

    // CÁLCULOS
    const precioEthUnitario = await obtenerPrecioEther();
    const costoAtomic = await irys.getPrice(pesoTotalBytes);
    const costoEth = irys.utils.fromAtomic(costoAtomic);
    const costoUsd = (costoEth * precioEthUnitario).toFixed(4);
    const pesoMB = (pesoTotalBytes / 1024 / 1024).toFixed(2);

    console.log("\n📊 REPORTE DE PRODUCCIÓN DIARIA:");
    console.log("---------------------------------------------------");
    console.log(`   📅 Archivos Únicos:    ${archivos.length}`);
    console.log(`   ⚖️  Peso de Datos:      ${pesoMB} MB`);
    console.log(`   💲 Precio ETH Hoy:     $${precioEthUnitario} USD`);
    console.log("---------------------------------------------------");
    console.log(`   💰 COSTO EVITADO:      $${costoUsd} USD`);
    console.log("---------------------------------------------------");
    console.log("   🚫 ESTO ES UN SIMULACRO. NO SE SUBIÓ NADA A BLOCKCHAIN.");

    // LIMPIEZA AUTOMÁTICA
    console.log("\n🧹 Limpiando zona de trabajo para el día siguiente...");
    for (const archivo of archivos) {
        fs.unlinkSync(path.join(carpetaEntrada, archivo));
    }
    console.log("✨ Carpeta 'cola_de_envio' vacía. Lista para procesar otro día.");
    console.log("===================================================\n");
}

main();