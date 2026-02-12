async function medirVelocidad() {
    // Mantenemos el formato de historial visual
    console.log("\n\n"); 
    console.log("===================================================");
    console.log("⏱️  AUDITORÍA DE VELOCIDAD (Intento de Caché)");
    console.log("===================================================");

    const urlObjetivo = "https://gateway.irys.xyz/T9TQ4GZqeowsxKH-dEKaxdHmHgkdzFLtkqkz117Blss";
    
    console.log(`🎯 Consultando: ${urlObjetivo}`);
    console.log("⏳ Descargando...");

    const inicio = performance.now();

    try {
        const respuesta = await fetch(urlObjetivo);
        if (!respuesta.ok) throw new Error(`Error HTTP: ${respuesta.status}`);
        
        const datos = await respuesta.json();

        const fin = performance.now();
        const duracion = (fin - inicio).toFixed(2); 

        console.log("\n✅ ¡Descarga Completa!");
        console.log("---------------------------------------------------");
        console.log(`🚀 TIEMPO TOTAL DE RESPUESTA:  ${duracion} ms`);
        console.log("---------------------------------------------------");
        
        // Evaluación de KPI
        if (duracion < 200) console.log("📊 Veredicto: EXCELENTE (Velocidad Caché/CDN)");
        else if (duracion < 500) console.log("📊 Veredicto: BUENO (Estándar web)");
        else if (duracion < 1000) console.log("📊 Veredicto: ACCEPTABLE (Carga perceptible)");
        else console.log("📊 Veredicto: LENTO (Cold Start o Red saturada)");

        console.log("---------------------------------------------------");
        console.log("🔍 DIAGNÓSTICO DE ESTRUCTURA JSON:");
        console.log("   El script anterior falló porque no conocíamos los nombres de tus campos.");
        console.log("   Aquí están las llaves principales detectadas en tu archivo:");
        console.log("---------------------------------------------------");
        
        // ESTO ES LO NUEVO: Imprimimos las llaves para ver cómo se llaman
        console.log(Object.keys(datos)); 
        
        console.log("---------------------------------------------------");
        console.log("⚠️  Usa estos nombres para ajustar tu integración Web2.");

    } catch (error) {
        console.error("❌ Falló la prueba:", error.message);
    }
}

medirVelocidad();