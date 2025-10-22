import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import routes from "./routes.js";

export function createApp() {
  const app = express();

  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(morgan("combined"));

  app.set("trust proxy", true);

  app.use("/", routes);

  app.use((req, res) => res.status(404).json({ error: "Not found" }));

  return app;
}
