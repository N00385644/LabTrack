import fs from 'node:fs';
import path from 'node:path';
import { Builder, By, until, type WebDriver, type WebElement } from 'selenium-webdriver';
import chrome from 'selenium-webdriver/chrome';

export const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:4173';
export const SCREENSHOTS_DIR = path.resolve(process.cwd(), 'e2e', 'screenshots');

export async function buildDriver(): Promise<WebDriver> {
  const options = new chrome.Options();
  options.addArguments(
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--window-size=1440,1000',
    '--lang=es-PE',
  );
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();
  await driver.manage().setTimeouts({ implicit: 0, pageLoad: 30_000, script: 30_000 });
  return driver;
}

export async function visit(driver: WebDriver, pathname: string): Promise<void> {
  await driver.get(`${BASE_URL}${pathname}`);
  await driver.wait(until.elementLocated(By.id('root')), 10_000);
}

export async function findTestId(driver: WebDriver, testId: string): Promise<WebElement> {
  return driver.wait(
    until.elementLocated(By.css(`[data-testid="${testId}"]`)),
    12_000,
    `No se encontró el elemento ${testId}`,
  );
}

export async function clickTestId(driver: WebDriver, testId: string): Promise<void> {
  const element = await findTestId(driver, testId);
  await driver.wait(until.elementIsVisible(element), 10_000);
  await element.click();
}

export async function typeTestId(driver: WebDriver, testId: string, text: string): Promise<void> {
  const element = await findTestId(driver, testId);
  await element.clear();
  await element.sendKeys(text);
}

export async function setInputValue(
  driver: WebDriver,
  testId: string,
  value: string,
): Promise<void> {
  await driver.executeScript(
    `
    const element = document.querySelector('[data-testid="' + arguments[0] + '"]');
    const descriptor = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
    descriptor.set.call(element, arguments[1]);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    `,
    testId,
    value,
  );
}

export async function login(
  driver: WebDriver,
  code: string,
  password: string,
): Promise<void> {
  await visit(driver, '/login');
  await typeTestId(driver, 'login-code', code);
  await typeTestId(driver, 'login-password', password);
  await clickTestId(driver, 'login-submit');
  await driver.wait(
    async () => {
      const url = await driver.getCurrentUrl();
      return url.includes('/catalogo') || url.includes('/admin');
    },
    15_000,
    'El inicio de sesión no redirigió al panel esperado',
  );
}

export async function logout(driver: WebDriver): Promise<void> {
  await clickTestId(driver, 'logout');
  await driver.wait(until.urlContains('/login'), 10_000);
}

export async function screenshot(driver: WebDriver, name: string): Promise<void> {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  const png = await driver.takeScreenshot();
  fs.writeFileSync(path.join(SCREENSHOTS_DIR, `${name}.png`), png, 'base64');
}

export async function waitForToast(driver: WebDriver, fragment: string): Promise<void> {
  await driver.wait(
    async () => {
      const toasts = await driver.findElements(By.css('output, [role="status"]'));
      for (const toast of toasts) {
        if ((await toast.getText()).toLowerCase().includes(fragment.toLowerCase())) {
          return true;
        }
      }
      return false;
    },
    12_000,
    `No apareció el mensaje que contiene "${fragment}"`,
  );
}

export async function rowContaining(
  driver: WebDriver,
  testId: string,
  fragment: string,
  timeout = 12_000,
): Promise<WebElement> {
  let found: WebElement | undefined;
  await driver.wait(
    async () => {
      const rows = await driver.findElements(By.css(`[data-testid="${testId}"]`));
      for (const row of rows) {
        if ((await row.getText()).includes(fragment)) {
          found = row;
          return true;
        }
      }
      return false;
    },
    timeout,
    `No se encontró una fila ${testId} con "${fragment}"`,
  );
  if (!found) {
    throw new Error(`No se encontró la fila con ${fragment}`);
  }
  return found;
}

export async function waitForRowMissing(
  driver: WebDriver,
  testId: string,
  fragment: string,
): Promise<void> {
  await driver.wait(
    async () => {
      const rows = await driver.findElements(By.css(`[data-testid="${testId}"]`));
      for (const row of rows) {
        if ((await row.getText()).includes(fragment)) {
          return false;
        }
      }
      return true;
    },
    12_000,
    `La fila con ${fragment} seguía visible`,
  );
}

