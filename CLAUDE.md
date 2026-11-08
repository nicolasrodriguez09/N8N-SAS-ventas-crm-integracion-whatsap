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
- **n8n**: un solo flujo para todos los negocios. Identifica el negocio por el `phone_id` de WhatsApp y carga su configuración desde la API de Laravel.
- **IA**: Gemini por API (AI Studio). En pruebas se usa un modelo Flash / Flash Lite (no TTS, no Preview).
- **Fotos**: Cloudinary para demos; luego disco local del VPS. Usar el sistema de discos (Storage) de Laravel para cambiar sin reescribir código.
- **Mensajería**: Telegram para pruebas (gratis), WhatsApp Business API oficial en producción. No usar WhatsApp Web no oficial.
- **Producción**: VPS Hostinger KVM 2 con Docker Compose (Laravel, MySQL, n8n, Postgres para memoria, Redis para caché/cola), dominio con SSL.

## Reglas de diseño importantes

- Toda tabla de datos lleva `negocio_id`; un dueño nunca ve datos de otro negocio (usar un global scope).
- `producto_fotos` es neutral al proveedor: campos `disco` (cloudinary | local), `ruta` y `url`. Nada de `cloudinary_public_id`.
- **El dueño NO configura el agente** (tono, reglas, prompt, plantillas). Eso es solo del rol `admin`. El dueño edita datos del negocio: horario, dirección, envíos, pagos, promociones.
- `suscripciones` = lo que cada negocio paga por usar la plataforma (no ventas del negocio). Si vence, el bot deja de atender.
- El agente marca `[INTERES_ALTO]` al final de su respuesta; n8n la detecta, la quita antes de enviar al cliente y registra el lead.
- Cuando el dueño pulsa "Yo atiendo", `clientes.bot_pausado = true` y el bot deja de responderle a ese cliente.
- Memoria del agente por `negocio_id + teléfono`. Simple Memory solo en pruebas; en producción Postgres o Redis.

## Dónde está cada cosa

- `diagramas-saas.drawio`: base de datos, actores, casos de uso, secuencia de un mensaje y estados del cliente (ábrelo en app.diagrams.net).
- Issues #1 a #30 del repo: historias de usuario y tareas técnicas, agrupadas en 6 hitos (Etapa 1 a Etapa 6). Trabaja en ese orden.
- `docs/contexto-proyecto.md`: decisiones, costos, endpoints, flujo de n8n y pendientes.
- `docs/prompt-cumbre-caps.md`: system message del agente de prueba (tienda de gorras en Cali).

## Convenciones

- Código, tablas y rutas en español sin tildes (`negocios`, `producto_fotos`, `/api/agente/config`).
- Commits pequeños y en español. Referencia el issue (`Refs #7`).
