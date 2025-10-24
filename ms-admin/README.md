# ⚙️ MS Admin

El microservicio **ms-admin** actúa como la API interna del sistema, encargada de crear, listar, consultar 
y eliminar enlaces, así como de leer y agregar las métricas almacenadas en **DynamoDB**. Gestiona las 
entradas base de cada link (slug, destino, variantes) y expone endpoints que permiten al frontend visualizar 
métricas totales por canal, país y dispositivo de forma centralizada.

