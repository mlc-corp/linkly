export function extractContextFromCFHeaders(req) {
  const h = req.headers;

  const country = String(
    h["cloudfront-viewer-country"] ||
    h["x-cloudfront-viewer-country"] ||
    "UN"
  ).toUpperCase();

  const isMobile  = h["cloudfront-is-mobile-viewer"]  === "true";
  const isTablet  = h["cloudfront-is-tablet-viewer"]  === "true";
  const isDesktop = h["cloudfront-is-desktop-viewer"] === "true";

  let device = "unknown";
  if (isMobile) device = "mobile";
  else if (isTablet) device = "tablet";
  else if (isDesktop) device = "desktop";

  return { country, device };
}
