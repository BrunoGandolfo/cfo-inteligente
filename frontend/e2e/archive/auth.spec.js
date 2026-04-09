/**
 * Suite E2E - Autenticación
 * Sistema CFO Inteligente
 * 
 * Tests del flujo completo de login/logout con BD real
 */

import { test, expect } from '@playwright/test';

test.describe('Autenticación - Sistema CFO', () => {
  
  test.beforeEach(async ({ page }) => {
    // Limpiar localStorage antes de cada test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('1. Login exitoso con credenciales válidas', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');
    
    // Fill credentials (usuario de test creado específicamente para E2E)
    await page.fill('input[type="email"]', 'test@cfo.local');
    await page.fill('input[type="password"]', 'test123');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // Wait for redirect (puede tardar)
    await page.waitForURL(/dashboard/, { timeout: 10000 });
    
    // Verify we're on dashboard
    expect(page.url()).toContain('dashboard');
  });

  test('2. Login fallido con credenciales inválidas', async ({ page }) => {
    await page.goto('/login');
    
    // Credenciales incorrectas
    await page.fill('input[type="email"]', 'fake@test.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    
    await page.click('button[type="submit"]');
    
    // Wait for error (toast or alert)
    await page.waitForTimeout(2000);
    
    // Verificar que NO redirigió a dashboard (sigue en login)
    expect(page.url()).toContain('login');
  });

  test('3. Token se guarda en localStorage', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[type="email"]', 'test@cfo.local');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Esperar redirect
    await page.waitForTimeout(3000);
    
    // Check localStorage (después del redirect)
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();
    expect(token.length).toBeGreaterThan(20);
  });

  test('4. userName y esSocio se guardan en localStorage', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[type="email"]', 'test@cfo.local');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    await page.waitForTimeout(3000);
    
    const userName = await page.evaluate(() => localStorage.getItem('userName'));
    const esSocio = await page.evaluate(() => localStorage.getItem('esSocio'));
    
    expect(userName).toBeTruthy();
    expect(esSocio).not.toBeNull(); // Puede ser 'true' o 'false'
  });

  test('5. Redirige a dashboard después de login', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[type="email"]', 'test@cfo.local');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Esperar redirect (window.location.href)
    await page.waitForTimeout(3000);
    
    // Verify URL changed
    const url = page.url();
    expect(url).not.toContain('login');
  });

  test('6. Logout limpia localStorage', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@cfo.local');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Verify token exists
    let token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();
    
    // Logout
    await page.click('text=Cerrar sesión');
    await page.waitForTimeout(1500); // Esperar logout completo
    
    // Verify localStorage cleared
    token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeNull();
  });

  test('7. Logout redirige a login', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@cfo.local');
    await page.fill('input[type="password"]', 'test123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Logout
    await page.click('text=Cerrar sesión');
    
    // Esperar redirect con delay
    await page.waitForTimeout(1500);
    expect(page.url()).toContain('login');
  });

  test('8. Dashboard sin token redirige a home', async ({ page }) => {
    // Intentar acceder a dashboard sin token
    await page.goto('/dashboard');
    
    // Should redirect to home o login
    await page.waitForTimeout(500);
    const url = page.url();
    expect(url).not.toContain('dashboard');
  });
});

