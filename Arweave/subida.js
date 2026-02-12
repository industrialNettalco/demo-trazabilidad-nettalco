// 1. Configuración de herramientas
require("dotenv").config(); // Esto carga tu llave privada del archivo .env
const Irys = require("@irys/sdk");

async function main() {
    try {
        console.log("---------------------------------------------------");
        console.log("🚀 Iniciando proceso de subida a Arweave (vía Base)...");

        // 2. Verificar que la llave existe
        if (!process.env.PRIVATE_KEY) {
            throw new Error("No encontré la PRIVATE_KEY en el archivo .env");
        }

        // 3. Conexión con Irys (El 'Mensajero')
        // Usamos la red 'mainnet' de Irys, pagando con 'base-eth'
        const irys = new Irys.default({
            network: "mainnet",
            token: "base-eth",
            key: process.env.PRIVATE_KEY, 
            config: { providerUrl: "https://mainnet.base.org" } // RPC oficial de Base
        });

        console.log("💳 Billetera conectada: " + irys.address);
        
        // Verificamos saldo (opcional, pero útil)
        const balance = await irys.getLoadedBalance();
        console.log(`💰 Saldo detectado: ${irys.utils.fromAtomic(balance)} ETH (Base)`);

        // 4. Preparar los datos a subir
        // Para esta prueba, subiremos un texto simple. Luego subiremos PDFs.
        const datosASubir = "Piloto Nettalco: Primer registro inmutable en Arweave desde Windows. Fecha: " + new Date().toISOString();
        
        // Calcular precio
        const precio = await irys.getPrice(datosASubir.length);
        console.log(`⚖️  Costo de subida: ${irys.utils.fromAtomic(precio)} ETH (¡Ínfimo!)`);

        // 5. ¡SUBIR!
        console.log("scaneando bloque y subiendo...");
        const receipt = await irys.upload(datosASubir);

        // 6. Resultado
        console.log("---------------------------------------------------");
        console.log("✅ ¡ÉXITO! Archivo inmutable subido.");
        console.log("🔗 Enlace Permanente (Arweave): https://arweave.net/" + receipt.id);
        console.log("---------------------------------------------------");

    } catch (error) {
        console.error("❌ Error:", error.message);
    }
}

main();