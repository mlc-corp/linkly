# 🐍 MS Redirect

El microservicio **ms-redirect** maneja las peticiones públicas de los enlaces generados por Linkly, 
recibiendo rutas del tipo `/:slug` o `/:slug/:variant` y respondiendo con una redirección **HTTP 302** hacia 
el destino original. Utiliza los headers enviados por **CloudFront** (como país y tipo de dispositivo) para 
actualizar las métricas correspondientes en **DynamoDB**, incrementando los contadores de clics y agregados 
por canal, país y dispositivo sin bloquear la redirección.



