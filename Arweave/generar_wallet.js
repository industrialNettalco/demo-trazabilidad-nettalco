const { ethers } = require("ethers");

// Crear una billetera aleatoria
const wallet = ethers.Wallet.createRandom();

console.log("---------------------------------------------------");
console.log("💎 NUEVA BILLETERA GENERADA PARA NETTALCO");
console.log("---------------------------------------------------");
console.log("1. TU DIRECCIÓN PÚBLICA (Para recibir fondos):");
console.log(wallet.address);
console.log("\n");
console.log("2. TU LLAVE PRIVADA (Para configurar el robot):");
console.log(wallet.privateKey);
console.log("---------------------------------------------------");
console.log("⚠️  IMPORTANTE: Guarda esta llave privada en un lugar seguro.");
console.log("    Si pierdes esto, pierdes el acceso a lo que subas.");
console.log("---------------------------------------------------");