require("dotenv").config();
const Irys = require("@irys/sdk");
const { ethers } = require("ethers");
const fs = require("fs");
const readline = require("readline");

// Configuración de interfaz
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

// --- FUNCIÓN NUEVA: CONSULTAR PRECIO REAL ---
async function obtenerPrecioEther() {
    try {
        console.log("🌍 Consultando precio actual de Ethereum en CoinGecko...");
        const respuesta = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd");
        const datos = await respuesta.json();
        return datos.ethereum.usd;
    } catch (error) {
        console.log("⚠️ No se pudo conectar a la API de precios. Usando valor referencia ($3300).");
        return 3300; 
    }
}

async function main() {
    try {
        // MODIFICACIÓN: Quitamos console.clear() y ponemos separadores visuales
        console.log("\n\n"); // Dos saltos de línea para separar de lo anterior
        console.log("===================================================");
        console.log("💎 NETTALCO PILOT - UPLOADER PRO (Live Market Data)");
        console.log("===================================================");

        // 1. OBTENER PRECIO REAL DE ETH
        const precioEthEnUsd = await obtenerPrecioEther();
        console.log(`💲 Precio ETH Hoy: $${precioEthEnUsd.toLocaleString()} USD`);
        console.log("---------------------------------------------------");

        // 2. VERIFICAR TU BILLETERA
        const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
        const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
        const balanceWei = await provider.getBalance(wallet.address);
        const balanceEth = ethers.formatEther(balanceWei);
        const tuSaldoUsd = (parseFloat(balanceEth) * precioEthEnUsd).toFixed(2);

        console.log(`👤 Usuario: ${wallet.address}`);
        console.log(`💰 TU SALDO: ${balanceEth} ETH (aprox. $${tuSaldoUsd} USD)`);
        console.log("---------------------------------------------------");

        // 3. COTIZACIÓN DEL ARCHIVO
        const irys = new Irys.default({
            network: "mainnet",
            token: "base-eth",
            key: process.env.PRIVATE_KEY,
            config: { providerUrl: "https://mainnet.base.org" }
        });

        // CAMBIO: Ahora buscamos el JSON por defecto
        const nombreArchivo = "test.json"; 
        if (!fs.existsSync(nombreArchivo)) throw new Error(`No encuentro el archivo '${nombreArchivo}'.`);

        const stats = fs.statSync(nombreArchivo);
        const tamanoBytes = stats.size;
        const tamanoKB = (tamanoBytes / 1024).toFixed(2);

        const precioAtomic = await irys.getPrice(tamanoBytes);
        const precioEthSubida = irys.utils.fromAtomic(precioAtomic);
        const costoRealUsd = (parseFloat(precioEthSubida) * precioEthEnUsd).toFixed(6);

        console.log(`📦 ARCHIVO: ${nombreArchivo} (${tamanoKB} KB)`);
        console.log(`\n📉 COSTO FINAL DE LA TRANSACCIÓN:`);
        console.log(`   Crypto: ${precioEthSubida} ETH`);
        console.log(`   Fiat:   $${costoRealUsd} USD (Al tipo de cambio actual)`);
        console.log("---------------------------------------------------");

        // 4. PREGUNTA DE SEGURIDAD
        rl.question('¿ EJECUTAR GASTO ? (Escribe "si" para confirmar): ', async (respuesta) => {
            if (respuesta.toLowerCase() === 'si' || respuesta.toLowerCase() === 'yes') {
                await ejecutarSubida(irys, precioAtomic, nombreArchivo);
            } else {
                console.log("\n❌ Cancelado. Tu dinero está a salvo.");
                process.exit(0);
            }
            rl.close();
        });

    } catch (error) {
        console.error("❌ Error:", error.message);
        rl.close();
    }
}

async function ejecutarSubida(irys, precio, archivo) {
    try {
        const saldoNodo = await irys.getLoadedBalance();
        if (saldoNodo.lt(precio)) {
            console.log(`\n🔄 Moviendo fondos exactos al nodo...`);
            const aFondear = precio.minus(saldoNodo).multipliedBy(1.1).integerValue();
            await irys.fund(aFondear);
        }

        console.log("🚀 Subiendo a la Permaweb...");
        const etiquetas = [
            { name: "Content-Type", value: "application/json" }, // Asegurando que sea JSON
            { name: "App", value: "Nettalco-Pro-Uploader" },
            { name: "Timestamp", value: new Date().toISOString() }
        ];
        
        const receipt = await irys.uploadFile(archivo, { tags: etiquetas });
        
        console.log("\n🎉 ¡ÉXITO! ARCHIVO INMUTABLE REGISTRADO.");
        console.log(`🔗 Link Oficial: https://gateway.irys.xyz/${receipt.id}`);
        
    } catch (e) {
        console.error("Fallo técnico:", e);
    }
}

main();