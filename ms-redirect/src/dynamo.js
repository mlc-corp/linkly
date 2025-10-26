import { initializeApp, applicationDefault } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";

// --- Configuración de Firestore ---

// Inicializa el SDK de Firebase Admin.
// Usará las credenciales predeterminadas (Application Default Credentials - ADC)
// o la variable de entorno GOOGLE_APPLICATION_CREDENTIALS si está definida.
initializeApp({
  credential: applicationDefault(),
});

// Obtiene la instancia de la base de datos de Firestore
export const db = getFirestore();

// Define los nombres de tus colecciones (equivalente a las tablas de DynamoDB)
const LINKS_COLLECTION = process.env.LINKS_COLLECTION || "links";
const METRICS_COLLECTION = process.env.METRICS_COLLECTION || "metrics";

// Ya no necesitas las variables de entorno DDB_TABLE, DDB_ENDPOINT, etc.

// --- Lógica de la aplicación migrada ---

/**
 * Obtiene un enlace por su slug desde Firestore.
 * @param {string} slug
 * @returns {Promise<{ destinationUrl: string } | null>}
 */
export async function getLinkBySlug(slug) {
  // 1. Obtenemos la referencia al documento usando el slug como ID
  const docRef = db.collection(LINKS_COLLECTION).doc(slug);

  // 2. Leemos el documento
  const doc = await docRef.get();

  // 3. Verificamos que exista y esté habilitado
  if (!doc.exists) return null;

  const data = doc.data();

  // Asumimos que los campos se llaman 'enabled' y 'destinationUrl'
  if (data.enabled === false) return null;

  return { destinationUrl: data.destinationUrl };
}

/**
 * Incrementa las métricas de clics de forma atómica en Firestore.
 * @param {{ slug: string, variant?: string, country?: string, device?: string }}
 */
export async function incrementMetrics({
  slug,
  variant = "default",
  country = "UN",
  device = "unknown",
}) {
  const c = (country || "UN").toUpperCase();
  const d = device || "unknown";

  // Usamos un ID de documento compuesto para las métricas (p.ej. "mi-slug#default")
  const metricDocId = `${slug}#${variant}`;
  const docRef = db.collection(METRICS_COLLECTION).doc(metricDocId);

  // Usamos una transacción para asegurar la atomicidad (lectura-modificación-escritura)
  // Esto replica el comportamiento de UpdateCommand de DynamoDB
  try {
    await db.runTransaction(async (transaction) => {
      // 1. Leer el documento dentro de la transacción
      const doc = await transaction.get(docRef);

      let currentData;

      // 2. Si no existe, inicializamos los datos (como if_not_exists)
      if (!doc.exists) {
        currentData = {
          clicks: 0,
          byCountry: {},
          byDevice: {},
        };
      } else {
        currentData = doc.data();
      }

      // 3. Calculamos los nuevos valores
      const newData = {
        ...currentData,
        // Incrementamos el total de clics
        clicks: (currentData.clicks || 0) + 1,
        // Incrementamos el contador por país
        byCountry: {
          ...currentData.byCountry,
          [c]: (currentData.byCountry?.[c] || 0) + 1,
        },
        // Incrementamos el contador por dispositivo
        byDevice: {
          ...currentData.byDevice,
          [d]: (currentData.byDevice?.[d] || 0) + 1,
        },
      };

      // 4. Escribimos los datos actualizados en la transacción
      transaction.set(docRef, newData);
    });
  } catch (e) {
    console.error(`[ms-redirect] Error al incrementar métricas: ${metricDocId}`, e);
    // Maneja el error como prefieras (p.ej. reintentar o simplemente loguear)
  }
}