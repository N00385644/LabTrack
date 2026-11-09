/**
 * Script de automatización Playwright para capturar el dashboard HTML de Apache JMeter.
 * Uso:
 *   node docs/evidencias-jmeter/capture_report.js
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

async function captureDashboard() {
  const reportsToCapture = [
    {
      name: 'carga',
      htmlPath: path.resolve(__dirname, 'carga/html/index.html'),
      fallbackPath: path.resolve(__dirname, '../../jmeter/reports/html/index.html'),
      outputDir: path.resolve(__dirname, 'capturas-carga'),
    },
    {
      name: 'estres',
      htmlPath: path.resolve(__dirname, 'estres/html/index.html'),
      fallbackPath: path.resolve(__dirname, '../../jmeter/reports-stress/html/index.html'),
      outputDir: path.resolve(__dirname, 'capturas-estres'),
    },
  ];

  console.log('Iniciando captura de reportes HTML de JMeter con Playwright...');
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
  } catch (err) {
    console.error('No se pudo iniciar el navegador Chromium:', err.message);
    process.exit(1);
  }

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  for (const item of reportsToCapture) {
    let targetFile = item.htmlPath;
    if (!fs.existsSync(targetFile)) {
      if (fs.existsSync(item.fallbackPath)) {
        targetFile = item.fallbackPath;
      } else {
        console.warn(`[OMITIDO] No existe el reporte HTML para ${item.name}: ${targetFile}`);
        continue;
      }
    }

    fs.mkdirSync(item.outputDir, { recursive: true });
    console.log(`Cargando reporte de ${item.name}: ${targetFile}`);
    await page.goto(`file://${targetFile}`, { waitUntil: 'networkidle' });

    // 1. Captura del dashboard general
    const dashboardShot = path.join(item.outputDir, `dashboard-${item.name}.png`);
    await page.screenshot({ path: dashboardShot, fullPage: true });
    console.log(`✓ Captura guardada: ${dashboardShot}`);

    // 2. Captura de la tabla APDEX y estadísticas
    try {
      const statsTable = await page.$('#statisticsTable, .table-responsive, #dashboard');
      if (statsTable) {
        const statsShot = path.join(item.outputDir, `tabla-estadisticas-${item.name}.png`);
        await statsTable.screenshot({ path: statsShot });
        console.log(`✓ Tabla de estadísticas guardada: ${statsShot}`);
      }
    } catch (e) {
      console.warn(`No se pudo aislar la tabla de estadísticas: ${e.message}`);
    }
  }

  await browser.close();
  console.log('Capturas finalizadas.');
}

captureDashboard().catch((err) => {
  console.error('Error durante la ejecución de Playwright:', err);
  process.exit(1);
});
