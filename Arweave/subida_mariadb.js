require("dotenv").config();
const Irys = require("@irys/sdk");
const fs = require("fs");
const path = require("path");
const mysql = require("mysql2/promise");
const readline = require("readline");
const { ethers } = require("ethers"); // Nueva importación para leer tu billetera

// --- CONFIGURACIÓN BASE DE DATOS ---
const dbConfig = {
    host: process.env.DB_PRENDAS_HOST,
    user: process.env.DB_PRENDAS_USER,
    password: process.env.DB_PRENDAS_PASSWORD,
    database: process.env.DB_PRENDAS_NAME,
    port: process.env.DB_PRENDAS_PORT
};

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function obtenerPrecioEther() {
    try {
        const respuesta = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd");
        const datos = await respuesta.json();
        return datos.ethereum.usd;
    } catch (error) {
        return 0; // Si falla, mostraremos 0
    }
}

async function main() {
    console.log("\n===================================================");
    console.log("🚀 NETTALCO - UPLOADER MAESTRO (CON PANEL FINANCIERO)");
    console.log("===================================================");

    const carpetaEntrada = "./cola_de_envio";
    
    // 1. Verificar archivos
    if (!fs.existsSync(carpetaEntrada)) {
        console.log("❌ No existe la carpeta 'cola_de_envio'.");
        process.exit(0);
    }
    
    const archivos = fs.readdirSync(carpetaEntrada).filter(file => file.endsWith('.json'));
    
    if (archivos.length === 0) {
        console.log("✅ No hay archivos pendientes. Todo al día.");
        process.exit(0);
    }

    // 2. Conectar a Irys y Base
    const irys = new Irys.default({
        network: "mainnet",
        token: "base-eth",
        key: process.env.PRIVATE_KEY,
        config: { providerUrl: "https://mainnet.base.org" }
    });

    const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

    // 3. ANÁLISIS DE COSTOS Y SALDOS
    console.log(`📦 Analizando lote de ${archivos.length} archivos...`);
    
    let pesoTotalBytes = 0;
    for (const archivo of archivos) {
        const ruta = path.join(carpetaEntrada, archivo);
        pesoTotalBytes += fs.statSync(ruta).size;
    }

    // Cálculos financieros
    const precioEthUnitario = await obtenerPrecioEther();
    
    const costoAtomic = await irys.getPrice(pesoTotalBytes);
    const costoEth = irys.utils.fromAtomic(costoAtomic);
    const costoUsd = (costoEth * precioEthUnitario).toFixed(4);
    
    // Saldo Nodo Irys (Precargado)
    const saldoIrysAtomic = await irys.getLoadedBalance();
    const saldoIrysEth = irys.utils.fromAtomic(saldoIrysAtomic);
    const saldoIrysUsd = (saldoIrysEth * precioEthUnitario).toFixed(4);

    // Saldo Billetera Real (Base Mainnet)
    const balanceWei = await provider.getBalance(wallet.address);
    const balanceWalletEth = ethers.formatEther(balanceWei);
    const balanceWalletUsd = (balanceWalletEth * precioEthUnitario).toFixed(2);

    // Lógica de Fondeo
    let necesitaFondeo = false;
    let costoFondeoEth = 0;
    
    if (saldoIrysAtomic.lt(costoAtomic)) {
        necesitaFondeo = true;
        // Calculamos faltante + 10% buffer
        costoFondeoEth = costoAtomic.minus(saldoIrysAtomic).multipliedBy(1.1); 
    }

    console.log("\n📊 TABLERO FINANCIERO:");
    console.log("---------------------------------------------------");
    console.log(`   💲 Precio ETH Actual:  $${precioEthUnitario} USD`);
    console.log("---------------------------------------------------");
    console.log(`   📂 LOTE A SUBIR:       ${archivos.length} Archivos (${(pesoTotalBytes / 1024 / 1024).toFixed(2)} MB)`);
    console.log(`   💰 Costo Estimado:     $${costoUsd} USD  (${Number(costoEth).toFixed(6)} ETH)`);
    console.log("---------------------------------------------------");
    console.log(`   ☁️  Saldo Nodo Irys:    $${saldoIrysUsd} USD  (${Number(saldoIrysEth).toFixed(6)} ETH)`);
    console.log(`   🏦 Saldo Tu Billetera: $${balanceWalletUsd} USD  (${Number(balanceWalletEth).toFixed(6)} ETH)`);
    console.log("---------------------------------------------------");

    if (necesitaFondeo) {
        const costoFondeoReadable = irys.utils.fromAtomic(costoFondeoEth).toFixed(6);
        console.log(`⚠️  SALDO INSUFICIENTE EN NODO.`);
        console.log(`   El script tomará ~${costoFondeoReadable} ETH ($${(costoFondeoReadable*precioEthUnitario).toFixed(2)}) de tu billetera.`);
        
        // Verificación final de solvencia
        if (parseFloat(balanceWalletEth) < parseFloat(costoFondeoReadable)) {
            console.log("\n❌ ERROR CRÍTICO: No tienes suficiente saldo en tu Billetera para cubrir el costo.");
            process.exit(0);
        }
    } else {
        console.log("✅ Tienes saldo suficiente en el Nodo. No se tocará tu Billetera.");
    }

    // 4. PREGUNTA DE SEGURIDAD
    rl.question('\n¿ CONFIRMAS SUBIR ESTE LOTE ? (Escribe "si"): ', async (respuesta) => {
        if (respuesta.toLowerCase() !== 'si') {
            console.log("❌ Operación cancelada.");
            process.exit(0);
        }

        console.log("\n🚀 Iniciando secuencia de subida...");
        
        try {
            const connection = await mysql.createConnection(dbConfig);
            console.log("🐬 Conexión DB establecida.");

            // Fondeo preventivo
            if (necesitaFondeo) {
                console.log("🔄 Ejecutando recarga de saldo desde billetera...");
                await irys.fund(costoFondeoEth.integerValue());
                console.log("✅ Recarga completada.");
            }

            for (let i = 0; i < archivos.length; i++) {
                const archivo = archivos[i];
                const rutaCompleta = path.join(carpetaEntrada, archivo);
                const hashInterno = archivo.replace(".json", ""); 
                
                process.stdout.write(`[${i+1}/${archivos.length}] Subiendo ${hashInterno.substring(0, 8)}... `);

                const etiquetas = [
                    { name: "Content-Type", value: "application/json" },
                    { name: "App", value: "Nettalco-Trazabilidad" },
                    { name: "Hash-Interno", value: hashInterno }
                ];

                try {
                    const receipt = await irys.uploadFile(rutaCompleta, { tags: etiquetas });
                    const arweaveID = receipt.id;

                    await connection.execute(
                        "UPDATE apdobloctrazhashtemp SET TTICKHASH = ? WHERE THASHINTE = ?",
                        [arweaveID, hashInterno]
                    );

                    console.log(`✅ TxID: ${arweaveID}`);
                    // fs.unlinkSync(rutaCompleta); 

                } catch (e) {
                    console.log(`❌ ERROR: ${e.message}`);
                }
            }

            await connection.end();
            console.log("\n🏁 ¡LOTE COMPLETADO CON ÉXITO!");
            process.exit(0);

        } catch (error) {
            console.error("\n❌ Error Crítico:", error.message);
            process.exit(1);
        }
    });
}

main();