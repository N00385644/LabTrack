import { By, until, type WebDriver } from 'selenium-webdriver';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import {
  BASE_URL,
  buildDriver,
  clickTestId,
  findTestId,
  login,
  logout,
  rowContaining,
  screenshot,
  setInputValue,
  typeTestId,
  visit,
  waitForRowMissing,
  waitForToast,
} from './helpers/e2e';

let driver: WebDriver;

beforeAll(async () => {
  const health = await fetch(`${BASE_URL}/`).catch(() => null);
  if (!health || !health.ok) {
    throw new Error(
      `El frontend no responde en ${BASE_URL}. Ejecuta la aplicación antes de las pruebas E2E.`,
    );
  }
  driver = await buildDriver();
});

afterAll(async () => {
  if (driver) {
    await driver.quit();
  }
});

describe('Flujos críticos de LabTrack · Selenium', () => {
  it('HU-01 · rechaza credenciales inválidas con el mensaje exigido', async () => {
    await visit(driver, '/login');
    await typeTestId(driver, 'login-code', '99999999');
    await typeTestId(driver, 'login-password', 'NoExiste2026!');
    await clickTestId(driver, 'login-submit');

    const error = await findTestId(driver, 'login-error');
    await driver.wait(until.elementTextContains(error, 'Credenciales inválidas'), 10_000);
    await screenshot(driver, '01-login-credenciales-invalidas');
  });

  it('HU-01 · bloquea la cuenta tras 3 intentos fallidos', async () => {
    await visit(driver, '/login');
    await typeTestId(driver, 'login-code', '20241059');
    await typeTestId(driver, 'login-password', 'ClaveIncorrecta2026!');

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      await clickTestId(driver, 'login-submit');
      await driver.wait(
        async () => {
          const errors = await driver.findElements(By.css('[data-testid="login-error"]'));
          if (errors.length === 0) return false;
          const text = await errors[0].getText();
          return attempt < 3
            ? text.includes('Credenciales inválidas')
            : text.includes('bloqueada temporalmente');
        },
        10_000,
        `El intento ${attempt} no mostró el mensaje esperado`,
      );
    }

    const error = await findTestId(driver, 'login-error');
    expect(await error.getText()).toContain('bloqueada temporalmente');
    await screenshot(driver, '02-login-cuenta-bloqueada');
  });

  it('HU-01 · inicia sesión como estudiante y muestra el catálogo', async () => {
    await login(driver, '20240001', 'Estudiante2026!');

    expect(await driver.getCurrentUrl()).toContain('/catalogo');
    expect(await (await findTestId(driver, 'nav-catalogo')).isDisplayed()).toBe(true);
    const search = await findTestId(driver, 'catalog-search');
    expect(await search.isDisplayed()).toBe(true);
    await screenshot(driver, '03-catalogo-estudiante');
  });

  it('HU-02 · aplica los filtros exactos por categoría', async () => {
    await clickTestId(driver, 'filter-electronica');
    await driver.wait(
      async () => {
        const count = await findTestId(driver, 'catalog-count');
        return (await count.getText()).includes('Electrónica');
      },
      10_000,
      'No se actualizó el filtro de Electrónica',
    );

    await driver.wait(
      async () => {
        const cards = await driver.findElements(By.css('[data-testid="equipment-card"]'));
        if (cards.length === 0) return false;
        for (const card of cards) {
          if (!(await card.getText()).includes('Electrónica')) return false;
        }
        return true;
      },
      10_000,
      'Las tarjetas no se actualizaron al filtro de Electrónica',
    );
    await screenshot(driver, '04-filtro-electronica');

    await clickTestId(driver, 'filter-redes');
    await driver.wait(
      async () => {
        const cards = await driver.findElements(By.css('[data-testid="equipment-card"]'));
        if (cards.length === 0) return false;
        for (const card of cards) {
          if (!(await card.getText()).includes('Redes')) return false;
        }
        return true;
      },
      10_000,
      'Las tarjetas no se actualizaron al filtro de Redes',
    );
  });

  it('HU-03 · registra una reserva desde el catálogo', async () => {
    await visit(driver, '/catalogo');
    await clickTestId(driver, 'reserve-COMP-003');

    const select = await findTestId(driver, 'reservation-equipment');
    await driver.wait(
      async () => {
        const selected = await driver.executeScript<string>(
          "return document.querySelector('[data-testid=\"reservation-equipment\"]').selectedOptions[0]?.textContent ?? ''",
        );
        return selected.includes('COMP-003');
      },
      10_000,
      'El equipo no quedó preseleccionado',
    );
    expect(await select.isDisplayed()).toBe(true);

    await setInputValue(driver, 'reservation-start', '16:00');
    await setInputValue(driver, 'reservation-end', '17:00');
    await clickTestId(driver, 'reservation-submit');

    await driver.wait(until.urlContains('/mis-reservas'), 12_000);
    await waitForToast(driver, 'pendiente de aprobación');
    const reservationRow = await rowContaining(driver, 'reservation-row', 'COMP-003');
    expect(await reservationRow.getText()).toContain('Pendiente');
    await screenshot(driver, '05-reserva-registrada');
  });

  it('HU-04 · el administrador aprueba la solicitud pendiente', async () => {
    await logout(driver);
    await login(driver, 'ADMIN01', 'Admin2026!');

    const pendingRow = await rowContaining(driver, 'pending-row', 'COMP-003');
    expect(await pendingRow.getText()).toContain('Valeria Ramos');

    await (
      await pendingRow.findElement(By.css('[data-action="approve"]'))
    ).click();
    await waitForToast(driver, 'aprobada');
    await waitForRowMissing(driver, 'pending-row', 'COMP-003');
    await screenshot(driver, '06-solicitud-aprobada');
  });

  it('HU-05 · registra la devolución tardía y aplica la penalización', async () => {
    await clickTestId(driver, 'nav-devoluciones');

    const returnRow = await rowContaining(driver, 'return-row', 'ELEC-003');
    expect(await returnRow.getText()).toContain('Vencida');

    await (
      await returnRow.findElement(By.css('[data-action="return"]'))
    ).click();
    const warning = await findTestId(driver, 'return-confirm');
    await driver.wait(until.elementIsVisible(warning), 5_000);
    const dialog = await driver.findElement(By.css('dialog, [role="dialog"]'));
    expect(await dialog.getText()).toContain('Penalizado');

    await clickTestId(driver, 'return-confirm');
    await waitForToast(driver, 'penalización');
    await waitForRowMissing(driver, 'return-row', 'ELEC-003');
    await screenshot(driver, '07-devolucion-penalizada');

    await clickTestId(driver, 'nav-historial');
    await clickTestId(driver, 'tab-audit');
    const auditEntry = await driver.wait(
      until.elementLocated(By.xpath("//*[contains(text(),'Penalización aplicada')]")),
      12_000,
      'No se encontró el evento de penalización en la bitácora',
    );
    expect(await auditEntry.isDisplayed()).toBe(true);
    await screenshot(driver, '08-bitacora-penalizacion');
  });
});

