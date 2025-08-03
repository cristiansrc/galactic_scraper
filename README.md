# Sistema Asíncrono de Recolección de Datos de Mercados Intergalácticos

## 1. Contexto del Proyecto

Este proyecto implementa un sistema distribuido y asíncrono para la recolección de datos de "Mercados Intergalácticos". La arquitectura simula un entorno de web scraping real, donde un servicio centralizado (`Coordinador de Consultas`) genera órdenes de recolección que son procesadas por una flota de agentes (`Naves de Recolección`).

La comunicación entre los componentes se realiza a través de **RabbitMQ** para garantizar la robustez y el desacoplamiento, mientras que **PostgreSQL** se utiliza para la persistencia, trazabilidad y auditoría de cada tarea.

## 2. Arquitectura y Diseño

El sistema sigue un patrón **Productor-Consumidor** y está completamente contenedorizado con **Docker**.

- **Coordinador de Consultas (Producer):** Aplicación Python responsable de generar "órdenes de recolección", registrarlas en la base de datos con estado `PENDING` y enviarlas a una cola de RabbitMQ.
- **Nave de Recolección (Agent/Consumer):** Aplicación Python que escucha la cola de tareas. Procesa cada orden, simula la interacción de scraping (incluyendo casos de éxito y fallo), actualiza el estado de la tarea en la base de datos en cada paso y notifica los resultados a otra cola.
- **RabbitMQ:** Actúa como broker de mensajes, gestionando las colas `recoleccion_tareas` (para nuevas órdenes) y `recoleccion_resultados` (para los resultados).
- **PostgreSQL:** Almacena el estado de cada tarea y un log detallado de todos los eventos que ocurren en el ciclo de vida de una orden.

### Diseño de Código
Ambas aplicaciones (`producer` y `agent`) fueron refactorizadas para seguir una **arquitectura en capas**, separando claramente las responsabilidades:
- **`config.py`**: Carga y provee acceso a toda la configuración desde variables de entorno.
- **`database.py`**: Encapsula toda la lógica de interacción con la base de datos (`DatabaseManager`).
- **`messaging.py`**: Abstrae la comunicación con RabbitMQ (`RabbitMQProducer` / `RabbitMQConsumer`).
- **`task_service.py` / `processing.py`**: Contiene la lógica de negocio principal para orquestar o procesar las tareas.
- **`main.py`**: Punto de entrada de la aplicación, responsable de instanciar y ejecutar los servicios.

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
   docker-compose up --build
   ```
3. **Ejecutamos el consumer:**
   ```bash
   docker compose run --rm producer python main.py
   ```
   Esto ejecutara el consumer de la aplicacion

4. **Ejecutamos el agent:**
   ```bash
   docker compose run --rm agent python main.py
   ```
   Esto ejecutara el agent de la aplicacion

Este comando construirá las imágenes de producer y agent, iniciará los contenedores de rabbitmq y postgresql, y ejecutará las aplicaciones. La base de datos se inicializará automáticamente con el schema definido en init_db.sql, e iniciara los producer y los agent de la aplicacion

## 4. Flujo de Trabajo y Simulación

### 4.1. Coordinador de Consultas (Producer)

Al iniciar, el productor ejecuta los siguientes pasos:
1. Se conecta a PostgreSQL y RabbitMQ.
2. Genera 5 órdenes de recolección con diferentes escenarios simulados.
3. Para cada orden:
    - Inserta un registro en la tabla `tasks` con estado `PENDING`.
    - Envía la orden como un mensaje JSON a la cola `recoleccion_tareas`.
    - Registra un log en `task_logs` indicando que la tarea fue enviada.
4. Una vez enviadas todas las tareas, el productor finaliza su ejecución.

**Órdenes de Ejemplo Generadas:**
- **Éxito:** `GALACTIC_CRYSTAL_X`, `VOID_DUST_99`, `QUANTUM_FLUX_CAPACITOR`
- **Fallo (SKU no encontrado):** `SKU_NO_ENCONTRADO`
- **Fallo (Página de detalle):** `ERROR_PAGINA_DETALLE`
- **Fallo (Error de red):** Tarea con URL `https://vendorC.red-error.com/fail_load`

### 4.2. Nave de Recolección (Agent)

El agente está continuamente escuchando la cola `recoleccion_tareas`.
1. **Recepción:** Al recibir un mensaje, lo deserializa y actualiza el estado de la tarea a `IN_PROGRESS`.
2. **Simulación de Scraping:**
    - **Paso 1: Navegar a la URL:** Simula la carga de la página. Falla si la URL contiene `fail_load`.
    - **Paso 2: Buscar SKU:** Simula la búsqueda del producto. Falla si el SKU es `SKU_NO_ENCONTRADO`.
    - **Paso 3: Clic en Detalle:** Simula el clic. Falla si el SKU es `ERROR_PAGINA_DETALLE`.
    - **Paso 4: Extracción de Datos:** Si todos los pasos anteriores son exitosos, extrae los datos simulados.
3. **Trazabilidad:** Cada paso (éxito o fallo) es registrado en `task_logs` y el estado en la tabla `tasks` es actualizado correspondientemente (`COMPLETED`, `NETWORK_ERROR`, `SKU_NOT_FOUND`, `DETAIL_PAGE_ERROR`).
4. **Notificación de Resultados:** Al finalizar el procesamiento, envía un mensaje a la cola `recoleccion_resultados` con el estado final y los datos extraídos (si los hubo).
5. **ACK Manual:** El agente utiliza `manual acknowledgement`. Un mensaje solo se elimina de la cola (`ack`) después de que ha sido completamente procesado y registrado, garantizando que ninguna tarea se pierda en caso de que el agente falle.

## 5. Schema de la Base de Datos

La base de datos `galactic_market_db` contiene dos tablas principales:

### `tasks`
Almacena el estado general de cada orden de recolección.
- `task_id` (UUID, PK)
- `status` (VARCHAR): `PENDING`, `IN_PROGRESS`, `COMPLETED`, `NETWORK_ERROR`, etc.
- `extracted_data` (JSONB): Almacena los datos extraídos en caso de éxito.
- `error_message` (TEXT): Guarda el mensaje de error en caso de fallo.
- ... y otros campos como `resource_sku`, `vendor_planet_url`, timestamps.

### `task_logs`
Registra cada evento significativo en el ciclo de vida de una tarea para una auditoría detallada.
- `log_id` (UUID, PK)
- `task_id` (UUID, FK a `tasks`)
- `level` (VARCHAR): `INFO`, `WARNING`, `ERROR`
- `message` (TEXT): Descripción del evento.
- `component` (VARCHAR): `PRODUCER` o `AGENT`.
- `details` (JSONB): Datos adicionales como payloads o trazas de error.

## 6. Decisiones de Diseño y Buenas Prácticas

- **Manejo de Errores:** El agente está diseñado para ser resiliente. Los errores en el procesamiento de una tarea individual son capturados, registrados, y no detienen al consumidor, que continuará procesando otras tareas.
- **Configuración Externalizada:** Todas las credenciales y parámetros (hosts, nombres de colas, etc.) se gestionan a través de variables de entorno definidas en `docker-compose.yml`, sin valores hardcodeados en el código.
- **Manejo de Conexiones:** Las conexiones a RabbitMQ y PostgreSQL se gestionan de forma centralizada en sus respectivas capas, asegurando que se abran y cierren correctamente. Se implementa un manejo de excepciones para reintentar la conexión si los servicios no están disponibles inmediatamente al inicio.

## 7. Discusión sobre Concurrencia e Idempotencia (Bonus)

### Concurrencia
Para escalar el `agent` y procesar múltiples tareas concurrentemente, se podrían aplicar varias estrategias:
1.  **Múltiples Instancias del Contenedor:** La forma más sencilla con Docker es escalar el servicio `agent`: `docker-compose up --scale agent=5`. RabbitMQ distribuirá automáticamente los mensajes entre las 5 instancias del agente, procesando tareas en paralelo.
2.  **Multithreading/AsyncIO:** Dentro de una misma instancia del agente, se podría usar un pool de hilos (`ThreadPoolExecutor`) o `asyncio` para procesar varias tareas a la vez. `asyncio` sería ideal para una operación de I/O-bound como el scraping, ya que manejaría eficientemente los tiempos de espera (`time.sleep` en nuestra simulación, o esperas de red en un caso real).

### Idempotencia
Para garantizar que una tarea no se procese dos veces si RabbitMQ la re-entrega (por ejemplo, si un agente falla después de procesar pero antes de enviar el `ack`), se puede implementar una lógica de idempotencia:
- **Verificación de Estado en la BD:** Antes de iniciar el procesamiento de una tarea (`IN_PROGRESS`), el agente debería verificar el estado actual de la `task_id` en la base de datos. Si el estado ya es `IN_PROGRESS`, `COMPLETED` o algún estado de error, significa que otro agente ya tomó o completó la tarea. En ese caso, el agente actual simplemente descartaría el mensaje y enviaría el `ack`. Esta verificación convierte la operación de procesamiento en idempotente.
