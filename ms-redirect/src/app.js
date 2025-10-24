import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import routes from "./routes.js";

export function createApp() {
  const app = express();

  app.use(
    helmet({
      contentSecurityPolicy: {
        useDefaults: true,
        directives: {
          "default-src": ["'self'"],
          "connect-src": ["'self'"],
          "script-src": ["'self'"],
          "style-src": ["'self'"],
          "font-src": ["'self'", "data:"],
          "img-src": ["'self'", "data:"],
          "object-src": ["'none'"],
          "base-uri": ["'self'"],
          "frame-ancestors": ["'none'"],
          "upgrade-insecure-requests": [],
        },
      },
      crossOriginEmbedderPolicy: true,
      crossOriginOpenerPolicy: { policy: "same-origin" },
      crossOriginResourcePolicy: { policy: "same-origin" },
      referrerPolicy: { policy: "no-referrer" },
    })
  );

  app.use(morgan("combined"));
  app.set("trust proxy", true);

  app.use("/", routes);

  app.use((req, res) => res.status(404).json({ error: "Not found" }));

  return app;
}
