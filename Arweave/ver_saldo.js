require("dotenv").config();
const { ethers } = require("ethers");
const Irys = require("@irys/sdk");

async function main() {
    console.log("\n===================================================");
    console.log("💰 BALANCE FINAL - CIERRE DE OPERACIÓN");
    console.log("===================================================");

    // 1. Consultar Precio ETH actual
    let precioEth = 0;
    try {
        const resp = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd");
        const data = await resp.json();
        precioEth = data.ethereum.usd;
    } catch (e) {
        console.log("⚠️ No se pudo obtener precio USD en tiempo real.");
    }

    // 2. SALDO EN BILLETERA (Tu cuenta principal)
    const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    const balanceWei = await provider.getBalance(wallet.address);
    const balanceEth = ethers.formatEther(balanceWei);
    const balanceUsd = (balanceEth * precioEth).toFixed(2);

    console.log("\n🏦 1. TU BILLETERA (BASE MAINNET):");
    console.log(`   Dirección: ${wallet.address}`);
    console.log(`   Saldo:     ${Number(balanceEth).toFixed(6)} ETH`);
    console.log(`   Valor:     $${balanceUsd} USD`);

    // 3. SALDO EN NODO IRYS (Remanente del Nodo)
    const irys = new Irys.default({
        network: "mainnet",
        token: "base-eth",
        key: process.env.PRIVATE_KEY,
        config: { providerUrl: "https://mainnet.base.org" }
    });
    
    const atomics = await irys.getLoadedBalance();
    const irysEth = irys.utils.fromAtomic(atomics);
    const irysUsd = (irysEth * precioEth).toFixed(4);

    console.log("\n☁️  2. NODO IRYS (Saldo Remanente):");
    console.log(`   Saldo:     ${Number(irysEth).toFixed(6)} ETH`);
    console.log(`   Valor:     $${irysUsd} USD`);
    
    console.log("\n---------------------------------------------------");
    console.log("📝 NOTA: Es normal que quede un pequeño saldo en el Nodo Irys");
    console.log("      (centavos) debido al margen de seguridad del 10%.");
    console.log("      Ese saldo se usará automáticamente en tu próxima subida.");
    console.log("===================================================\n");
}

main();