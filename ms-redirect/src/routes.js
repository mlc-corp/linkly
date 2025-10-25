import express from "express";

import { getLinkBySlug, incrementMetrics } from "./dynamo.js";
import { extractContextFromCFHeaders } from "./metrics.js";

const router = express.Router();

router.get("/health", (_req, res) => res.json({ ok: true }));

async function handleRedirect(req, res, variantFromPath) {
  const slug = req.params.slug;
  const link = await getLinkBySlug(slug);
  if (!link) return res.status(404).json({ error: "Not found" });

  const v = variantFromPath || "default";

  let country = "UN";
  let device = "unknown";
  try {
    const ctx = extractContextFromCFHeaders(req);
    country = (ctx?.country || "UN").toUpperCase();
    device = ctx?.device || "unknown";
  } catch {
    // Intencional: si fallan los headers de Cloudflare, ignoramos y usamos defaults
  }

  await incrementMetrics({ slug, variant, country, device });

  incrementMetrics({ slug, variant, country, device })
    .then((r) => console.log("[metrics] ok", r?.$metadata))
    .catch((e) => console.error("[metrics] error", e));

  return res.redirect(302, link.destinationUrl);
}

router.get("/:slug", (req, res) => handleRedirect(req, res, undefined));
router.get("/:slug/:variant", (req, res) =>
  handleRedirect(req, res, req.params.variant),
);

export default router;
