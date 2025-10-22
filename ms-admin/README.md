# ⚙️ MS Admin

El **Microservicio Administrativo (ms-admin)** gestiona la creación, modificación y desactivación de enlaces dentro del sistema.  
Provee endpoints internos para definir variantes, configurar destinos, consultar estadísticas agregadas y aplicar reglas de negocio.  
Actúa como el **plano de control** de la plataforma, asegurando la coherencia entre los enlaces, métricas y configuraciones administrativas.
# 🟩 MS Admin

El microservicio **ms-admin** actúa como la API interna del sistema, encargada de crear, listar, consultar 
y eliminar enlaces, así como de leer y agregar las métricas almacenadas en **DynamoDB**. Gestiona las 
entradas base de cada link (slug, destino, variantes) y expone endpoints que permiten al frontend visualizar 
métricas totales por canal, país y dispositivo de forma centralizada.
