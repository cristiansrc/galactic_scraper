import json
import time
import datetime

class AgentService:
    def __init__(self, repository):
        self.repository = repository

    def handle_message(self, ch, method, body):
        try:
            task = json.loads(body)
            task_id = task["task_id"]
            sku = task["resource_sku"]
            vendor = task["vendor_planet_url"]

            # Verificar que la tarea exista antes de procesar
            if not self.repository.task_exists(task_id):
                print(f"❌ Tarea {task_id} no existe en la base de datos. Se descarta el mensaje.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            print(f"🛰️ Desplegando sonda para recolectar: {sku} desde {vendor}")
            time.sleep(1 + len(sku) % 3)
            result = {"data": f"Resultado ficticio de {sku}"}

            # Determinar el resultado (éxito o error)
            if "fail_load" in vendor:
                raise Exception("Fallo de red galáctico")
            elif sku == "SKU_NO_ENCONTRADO":
                raise ValueError("SKU no encontrado")
            elif sku == "ERROR_PAGINA_DETALLE":
                raise LookupError("Error en página de detalle")

            # Éxito: actualizar como DONE y loguear
            self.repository.update_task_done(task_id, result)
            self.repository.insert_log(task_id, "Recolección completada con éxito", level="INFO", details=result)
            print(f"✅ Recolección exitosa de {sku}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"🚨 Error galáctico: ❌ {e}")
            error_type = str(e)
            # Mapear el error al status permitido
            if "red galáctico" in error_type:
                new_status = "NETWORK_ERROR"
            elif "SKU" in error_type:
                new_status = "SKU_NOT_FOUND"
            elif "detalle" in error_type:
                new_status = "DETAIL_PAGE_ERROR"
            else:
                new_status = "NETWORK_ERROR"  # fallback seguro
            if self.repository.task_exists(task_id):
                self.repository.update_task_error(task_id, new_status, error_type)
                self.repository.insert_log(task_id, f"Error durante recolección: {error_type}", level="ERROR", details={"error": error_type})
            else:
                print(f"❌ No se puede loguear error: la tarea {task_id} no existe en la base de datos.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
