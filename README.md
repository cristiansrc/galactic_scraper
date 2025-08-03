# Sistema Asíncrono de Recolección de Datos de Mercados Intergalácticos

## 1. Contexto del Proyecto

Este proyecto implementa un sistema distribuido y asíncrono para la recolección de datos de "Mercados Intergalácticos". La arquitectura simula un entorno de web scraping real, donde un servicio centralizado ("Coordinador de Consultas" o Producer) genera órdenes de recolección que son procesadas por una flota de agentes ("Naves de Recolección" o Agent).

La comunicación entre los componentes se realiza a través de **RabbitMQ** para garantizar la robustez y el desacoplamiento, mientras que **PostgreSQL** se utiliza para la persistencia, trazabilidad y auditoría de cada tarea.

## 2. Arquitectura y Diseño

El sistema sigue un patrón **Productor-Consumidor** y está completamente contenedorizado con **Docker** y **docker-compose**.

- **Coordinador de Consultas (Producer):** Genera y registra órdenes de recolección en la base de datos (estado `PENDING`) y las envía a la cola `recoleccion_tareas` de RabbitMQ. Cada orden es un diccionario con un `task_id` único, SKU, URL de proveedor, prioridad y timestamp.
- **Nave de Recolección (Agent/Consumer):** Escucha la cola de tareas, procesa cada orden simulando scraping (con casos de éxito y fallo), actualiza el estado de la tarea en la base de datos en cada paso y notifica los resultados a la cola `recoleccion_resultados`.
- **RabbitMQ:** Broker de mensajes, gestiona las colas `recoleccion_tareas` y `recoleccion_resultados`.
- **PostgreSQL:** Almacena el estado de cada tarea y un log detallado de todos los eventos (tabla `tasks` y `task_logs`).

### Diseño de Código
Ambas aplicaciones (`producer` y `agent`) siguen una **arquitectura en capas**:
- **`config.py`**: Carga la configuración desde variables de entorno.
- **`repository.py`**: Encapsula la lógica de acceso a la base de datos.
- **`messaging.py`**: Abstrae la comunicación con RabbitMQ.
- **`service.py`**: Contiene la lógica de negocio principal.
- **`main.py`**: Punto de entrada de la aplicación.

## 3. Cómo Levantar el Entorno

Todo el ecosistema está orquestado con `docker-compose`.

### Prerrequisitos
- Docker
- Docker Compose

### Pasos para la Ejecución
1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/cristiansrc/galactic_scraper.git
   cd galactic_scraper
   ```
2. **Construir y levantar los servicios:**
   ```bash
   docker compose up --build -d
   ```
3. **Ejecutar el producer (coordinador):**
   ```bash
   docker compose run --rm producer python main.py
   ```
   Esto generará y enviará 5 órdenes de recolección a la cola.

4. **Ejecutar el agent (nave de recolección):**
   ```bash
   docker compose run --rm agent python main.py
   ```
   Esto procesará las órdenes, simulará scraping y actualizará la base de datos y los logs.

## 4. Estructura de Carpetas

- `producer/`: Código del coordinador de consultas.
- `agent/`: Código de la nave de recolección.
- `db/init_db.sql`: Script para crear las tablas `tasks` y `task_logs`.
- `docker-compose.yml`: Orquestador de servicios.

## 5. Ejemplo de Orden y Flujo

### Orden generada por el Producer
```json
{
  "task_id": "UUID único",
  "resource_sku": "GALACTIC_CRYSTAL_X",
  "vendor_planet_url": "https://vendorA.galactic-market.com",
  "priority": 1,
  "timestamp_created": "2025-08-03T21:00:00Z"
}
```

### Flujo resumido
1. Producer inserta la orden en la tabla `tasks` (estado `PENDING`) y la envía a RabbitMQ.
2. Agent recibe la orden, actualiza el estado a `IN_PROGRESS`, simula scraping paso a paso (con logs en `task_logs`), y actualiza el estado final (`COMPLETED`, `NETWORK_ERROR`, `SKU_NOT_FOUND`, `DETAIL_PAGE_ERROR`).
3. Agent envía el resultado a la cola `recoleccion_resultados` (opcional, bonus).

## 6. Manejo de Errores y Logging
- Todas las excepciones y fallos simulados se registran en la tabla `task_logs` y en los logs de la aplicación.
- El agent nunca colapsa por un error individual; registra el error y continúa con la siguiente tarea.
- Se usan try/except y logging en todas las operaciones críticas (DB, RabbitMQ, procesamiento).

## 7. Configuración y Variables de Entorno
- Todas las credenciales y parámetros de conexión están en archivos `.env` y son cargados por `config.py`.
- Puedes usar `.env.example` como plantilla.

## 8. Consideraciones de Concurrencia e Idempotencia (Bonus)
- **Concurrencia:** El agent puede escalarse lanzando múltiples instancias del contenedor agent, ya que cada una compite por mensajes en la cola. Para concurrencia interna, se podría usar threading o asyncio.
- **Idempotencia:** Cada tarea tiene un `task_id` único. Antes de procesar o actualizar una tarea, el agent verifica el estado en la base de datos para evitar duplicados si un mensaje se entrega más de una vez.

## 9. Decisiones de Diseño Clave
- Arquitectura en capas para facilitar el mantenimiento y la extensibilidad.
- Uso de logging y trazabilidad exhaustiva en BD y consola.
- Separación clara de responsabilidades entre producer y agent.
- Dockerización completa para facilitar el despliegue y pruebas.

## 10. Créditos y Autor
Desarrollado por cristiansrc para la prueba técnica de Desarrollador Python Senior (2025).
