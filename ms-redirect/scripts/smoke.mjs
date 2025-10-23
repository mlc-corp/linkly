import "dotenv/config";

const base = process.env.APP_BASE_URL || "https://tu-dominio.com";
const url = `${base.replace(/\/+$/, "")}/health`;

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function check() {
  for (let i = 1; i <= 10; i++) {
    try {
      const c = await fetch(url, { signal: AbortSignal.timeout(2000) });
      if (c.status === 200) {
        const body = await c.json().catch(() => ({}));
        if (body?.ok === true) {
          console.log("[smoke] OK (200 + { ok: true })");
          return 0;
        }
      }
      console.log(`[smoke] intento #${i} falló (status=${c.status})`);
    } catch (e) {
      console.log(`[smoke] intento #${i} error: ${e.message}`);
    }
    await sleep(1000);
  }
  console.error("[smoke] FAILED");
  return 1;
}

const code = await check();
process.exit(code);
