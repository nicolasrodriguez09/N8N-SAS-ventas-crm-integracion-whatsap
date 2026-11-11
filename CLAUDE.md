# CLAUDE.md

Contexto para Claude Code. Este proyecto se planeó en una conversación larga con Claude; aquí está lo decidido. El detalle completo está en `docs/contexto-proyecto.md` y el prompt del agente de ejemplo en `docs/prompt-cumbre-caps.md`.

## Qué es

Un SaaS multi-negocio: cada tienda (gorras, zapatos, celulares, comida…) tiene un agente de IA que atiende por WhatsApp, responde dudas básicas, motiva la compra y clasifica el interés del cliente. Cuando el interés es alto, avisa al dueño para que él cierre la venta personalmente. El dueño administra su catálogo y sus clientes en un panel web.

## Con quién trabajas

- La dueña del proyecto tiene conocimiento técnico medio. Explica en español, con palabras sencillas y paso a paso; evita jerga sin explicarla.
- Trabaja en Windows, con Node 22 y n8n local (`npx n8n`, `localhost:5678`).
- Antes de crear muchas cosas de golpe (issues, archivos, cambios grandes), muéstrale la lista y espera su visto bueno.

## Stack decidido

- **Laravel (PHP 8.3) + MySQL**: panel web + API para n8n. Un solo sistema para todos los negocios (multi-tenant por `negocio_id`).
- **n8n**: un solo flujo para todos los negocios. Identifica el negocio por su canal (`canal_identificador`: el bot de Telegram o el `phone_id` de WhatsApp) y carga su configuración desde la API de Laravel.
- **IA**: Gemini por API (AI Studio). En pruebas se usa un modelo Flash / Flash Lite (no TTS, no Preview).
- **Fotos**: Cloudinary para demos; luego disco local del VPS. Usar el sistema de discos (Storage) de Laravel para cambiar sin reescribir código.
- **Mensajería**: Telegram para pruebas (gratis), WhatsApp Business API oficial en producción. No usar WhatsApp Web no oficial.
- **Producción**: VPS Hostinger KVM 2 con Docker Compose (Laravel, MySQL, n8n, Postgres para memoria, Redis para caché/cola), dominio con SSL.

## Alcance del MVP

El MVP es el sistema funcionando de punta a punta, con **Telegram** como canal y fotos en **Cloudinary**. No es una versión recortada.

- Incluye: Etapa 1 (#1–#8 y #32), Etapa 2 (#9–#13), Etapa 3 (#14–#20 y #33–#36), #21 (Telegram) y #23 (fotos en el chat, por Telegram).
- Fuera del MVP: #22 WhatsApp Business, #24 memoria en Postgres (en el MVP basta Simple Memory), Etapa 5 (despliegue en VPS) y Etapa 6 (suscripciones y escalado).
- Aun así, diseña pensando en lo que viene: el código no debe amarrarse a Telegram ni a Cloudinary.

## Reglas de diseño importantes

- Toda tabla de datos lleva `negocio_id`; un dueño nunca ve datos de otro negocio (usar un global scope).
- `producto_fotos` es neutral al proveedor: campos `disco` (cloudinary | local), `ruta` y `url`. Nada de `cloudinary_public_id`.
- **El dueño NO configura el agente** (tono, reglas, prompt, plantillas). Eso es solo del rol `admin`. El dueño edita datos del negocio: horario, dirección, envíos, pagos, promociones.
- `suscripciones` = lo que cada negocio paga por usar la plataforma (no ventas del negocio). Si vence, el bot deja de atender.
- Memoria del agente por `negocio_id + teléfono`. Simple Memory solo en pruebas; en producción Postgres o Redis.

## Paso a una persona (decisión clave)

El bot **no cierra ventas ni maneja pagos**. Atiende, filtra y entusiasma; las personas concretan la venta y verifican las transacciones.

- **Momento importante** = el cliente quiere comprar o pagar, envía un comprobante, pide descuento, tiene un reclamo o pide hablar con una persona.
- En ese momento el agente llama a la herramienta `pasar_a_persona(motivo, resumen, datos_interes)`. No se usan etiquetas en el texto (nada de `[INTERES_ALTO]`).
- La API crea un registro en `atenciones` (estado `por_atender`), pone `clientes.bot_pausado = true` y dispara el aviso al encargado.
- El agente envía **un último mensaje** según el horario (abierto: "Andrés te confirma por aquí"; cerrado: "mañana a primera hora te confirman") y deja de responder.
- Si el cliente sigue escribiendo mientras está pausado: el bot no contesta, el mensaje se guarda y se avisa al encargado.
- En el panel, la lista **"Por atender"** muestra cliente, motivo, resumen y datos. Un empleado la **toma**, **responde desde el panel** (el mensaje sale por el mismo canal), **verifica el pago** y la marca **vendida con monto** o **perdida**. También puede **devolver el cliente al bot**.
- Si nadie la toma en `negocios.minutos_reaviso` minutos (dentro del horario), una tarea programada de Laravel vuelve a avisar.
- El bot puede decir qué **medios de pago** se aceptan, pero **nunca** da números de cuenta, links de pago ni confirma un pago.

## Quién hace qué entre Laravel y n8n

- **Laravel decide y guarda**: API del agente, panel, reglas de negocio, tareas programadas.
- **n8n es la única puerta de mensajes**: recibe los mensajes del canal, habla con la IA y envía todo lo que sale (respuestas del bot, mensajes del empleado vía webhook `enviar-mensaje`, avisos vía webhook `enviar-aviso`).
- Así, cambiar de Telegram a WhatsApp solo toca n8n y la configuración del negocio (`canal`, `canal_identificador`, `canal_token`).

## Dónde está cada cosa

- `diagramas-saas.drawio`: base de datos, actores, casos de uso, secuencia de un mensaje, estados del cliente y arquitectura (ábrelo en app.diagrams.net). Se genera con `docs/herramientas/generar_diagramas.py`.
- Issues del repo: historias de usuario y tareas técnicas, agrupadas en 6 hitos (Etapa 1 a Etapa 6). Trabaja en ese orden.
- `docs/contexto-proyecto.md`: decisiones, costos, endpoints, flujo de n8n y pendientes.
- `docs/prompt-cumbre-caps.md`: system message del agente de prueba (tienda de gorras en Cali).

## Convenciones

- Código, tablas y rutas en español sin tildes (`negocios`, `producto_fotos`, `/api/agente/config`).
- Commits pequeños y en español. Referencia el issue (`Refs #7`).
