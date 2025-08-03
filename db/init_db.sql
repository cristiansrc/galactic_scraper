-- Tabla principal de tareas
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY,
    resource_sku VARCHAR NOT NULL,
    vendor_planet_url VARCHAR NOT NULL,
    priority INTEGER NOT NULL,
    status VARCHAR NOT NULL CHECK (status IN (
        'PENDING', 'IN_PROGRESS', 'COMPLETED',
        'NETWORK_ERROR', 'SKU_NOT_FOUND', 'DETAIL_PAGE_ERROR'
    )),
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    extracted_data JSONB,
    error_message TEXT
);

-- Tabla de logs por tarea
CREATE TABLE IF NOT EXISTS task_logs (
    log_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(task_id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR NOT NULL CHECK (level IN ('INFO', 'WARNING', 'ERROR')),
    message TEXT NOT NULL,
    component VARCHAR NOT NULL CHECK (component IN ('PRODUCER', 'AGENT')),
    details JSONB
);