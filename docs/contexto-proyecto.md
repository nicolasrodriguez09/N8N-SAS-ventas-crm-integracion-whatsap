# Contexto del proyecto

Resumen de lo decidido durante la planeación (noviembre de 2026).

## 1. La idea

Agente de automatización para la atención primaria de cualquier negocio de ventas por chat (Telegram en el MVP, WhatsApp en producción):

- Responde a quienes solo piden información básica e intenta motivarlos a comprar, sin presionar.
- Si el cliente no compra, no pasa nada.
- En un **momento importante** (quiere comprar o pagar, manda un comprobante, pide descuento, tiene un reclamo o pide hablar con una persona), el bot deja **un último mensaje**, **se pausa** para ese cliente y lo deja en el panel, en la lista **"Por atender"**.
- Desde el panel, el dueño o un empleado **concreta la venta y verifica las transacciones**. El bot nunca cobra ni confirma pagos.
- El bot debe sonar como una persona real (vendedora colombiana), no como una IA.

## 2. Decisiones clave

| Decisión | Por qué |
| --- | --- |
| Un solo sistema multi-negocio (SaaS) | Replicar el software por cliente obliga a actualizar cada copia a mano. |
| Un solo flujo de n8n para todos | Cada mensaje es una ejecución independiente en paralelo. La personalidad de cada agente vive en la base de datos. |
| El bot no cierra ventas ni maneja pagos | Evita comprobantes falsos, errores de precio, descuentos inventados y stock desactualizado. Las personas verifican. |
| Paso a una persona con una herramienta (`pasar_a_persona`) | Más confiable que una etiqueta en el texto: no se olvida ni se cuela al cliente, y trae datos estructurados. |
| Pausa automática del bot | El cliente no recibe respuestas del bot mientras una persona lo atiende. |
| El empleado responde desde el panel | En Telegram no se puede escribir dentro del chat del bot desde otro lado, y en WhatsApp la API puede impedir usar la app en el mismo número. Así el cliente siempre habla con el mismo número. |
| Laravel decide, n8n es la puerta de mensajes | Todo lo que entra o sale por el canal pasa por n8n. Cambiar de Telegram a WhatsApp solo toca n8n. |
| Fotos neutrales al proveedor (`disco`, `ruta`, `url`) | Cloudinary en el MVP, disco del VPS después, sin reescribir código. |
| El dueño no configura el agente | Solo el rol admin cambia tono, reglas y prompt, para que el agente no se dañe. |

## 3. Arquitectura

```
Cliente ⇄ Telegram/WhatsApp ⇄ n8n ⇄ API Laravel ⇄ MySQL
                               │         │
                               ⇄ Gemini  ├─ Panel web (dueño, empleado, admin)
                                         ├─ Tareas programadas (reavisos)
                                         └─ Fotos (Cloudinary o disco local)
```

### Base de datos (MySQL)

- `plantillas`: id, tipo, texto_base (prompt con huecos `{{nombre}}`, `{{catalogo}}`, `{{tono}}`, `{{abierto_ahora}}`…)
- `negocios`: id, plantilla_id, nombre, tipo_negocio, canal (telegram | whatsapp), canal_identificador (único), canal_token (cifrado), aviso_chat_id, minutos_reaviso, telefono_dueno, nombre_agente, nombre_asesor, tono, instrucciones_extra, horario (json por día), direccion, info_envios, medios_pago, promociones, plan, activo
- `usuarios`: id, negocio_id, nombre, email, password, rol (dueno, empleado, admin)
- `categorias`: id, negocio_id, nombre
- `productos`: id, negocio_id, categoria_id, nombre, descripcion, precio, variantes (json), stock, activo
- `producto_fotos`: id, producto_id, disco, ruta, url, orden
- `clientes`: id, negocio_id, canal_chat_id, telefono, nombre, estado (nuevo, interes_medio, por_atender, en_atencion, vendido, perdido), bot_pausado, ultimo_mensaje_at
- `atenciones`: id, negocio_id, cliente_id, asignado_a (usuario), motivo (compra, pago, comprobante, descuento, reclamo, pide_persona, otro), resumen, datos_interes (json: producto, variante, cantidad, ciudad), estado (por_atender, en_atencion, vendido, perdido, devuelta_al_bot), monto_venta, notas, creada_at, tomada_at, cerrada_at, ultimo_aviso_at
- `mensajes`: id, negocio_id, cliente_id, atencion_id, usuario_id (si lo escribió una persona), rol (cliente, bot, humano), tipo (texto, imagen, audio), texto, media_url, canal_mensaje_id, created_at
- `suscripciones`: id, negocio_id, plan, estado, vence_el (lo que el negocio paga por la plataforma)

Campos del agente (`tono`, `instrucciones_extra`, `nombre_agente`, plantilla) y del canal solo los edita el rol admin.

### API para n8n (protegida con token)

- `GET /api/agente/config?canal=&identificador=` → negocio, prompt armado y si está abierto ahora (con caché)
- `GET /api/agente/productos?negocio_id=&buscar=` → productos activos con precio, stock y URLs de fotos
- `GET /api/agente/cliente?negocio_id=&chat_id=` → cliente (lo crea si no existe) y `bot_pausado`
- `POST /api/agente/mensajes` → guarda cada mensaje; si el cliente está pausado, avisa al encargado
- `POST /api/agente/atenciones` → crea la atención `por_atender`, pausa el bot y dispara el aviso

### Webhooks de n8n que llama Laravel

- `POST /webhook/enviar-mensaje` → envía al cliente lo que escribió el empleado en el panel
- `POST /webhook/enviar-aviso` → envía un aviso al encargado (nueva atención, mensaje nuevo, reaviso)

### Flujo de mensajes entrantes en n8n

1. Trigger del canal (Telegram en el MVP; Chat Trigger para pruebas en local).
2. HTTP Request → config del negocio.
3. HTTP Request → cliente.
4. HTTP Request → guardar el mensaje del cliente.
5. Si `bot_pausado`: termina (Laravel ya avisó al encargado).
6. AI Agent con el prompt del negocio. Herramientas: `buscar_productos` y `pasar_a_persona`. Memoria: clave `negocio_id + chat_id`.
7. Enviar la respuesta (y la foto, si aplica) y guardarla.

Si el agente llamó a `pasar_a_persona`, su respuesta es el último mensaje antes de la pausa.

### Estados del cliente

nuevo → interés medio (la API lo marca cuando el agente busca productos concretos) → **por atender** (bot pausado) → **en atención** → vendido (con monto) | perdido.
Desde "por atender" o "en atención" se puede **devolver al bot**. Si nadie toma una atención en `minutos_reaviso`, se vuelve a avisar. Un cliente vendido o perdido que vuelve a escribir regresa al flujo normal.

## 4. Estado actual

- n8n corre en local (Windows, Node 22, `npx n8n`).
- Hay un flujo de prueba: Chat Trigger → AI Agent + Google Gemini Chat Model (Flash Lite) + Simple Memory (ventana de 10). El system message es el de `docs/prompt-cumbre-caps.md`. Ese flujo de prueba todavía no tiene las herramientas; se agregan en la Etapa 2.
- Lecciones: algunos modelos de Gemini ya no se ofrecen a usuarios nuevos (error 404); los Preview pueden saturarse (503); los modelos TTS devuelven audio y el texto sale vacío. La suscripción Pro de la app de Gemini no sirve para la API: la clave se saca gratis en aistudio.google.com.
- El patrón de subida a Cloudinary ya se usó en otro proyecto de la dueña (React + Firebase): subida directa con upload preset, se guarda `secure_url`, cola offline con reintentos.
- Issues creados en GitHub con hitos por etapa y tablero Kanban privado "sas ventas whatsapp".

## 5. Etapas

1. Base del sistema y catálogo (Laravel, migraciones, login por roles, negocios, productos, fotos).
2. Configuración del agente y conexión con n8n (plantillas, API, herramientas del agente, flujo conectado).
3. Paso a una persona (pausa automática, lista "Por atender", avisos, responder desde el panel, venta con monto, devolver al bot, reavisos).
4. Canales de mensajería (Telegram, WhatsApp Business API, fotos en el chat, memoria persistente).
5. Despliegue (VPS, backups, migrar fotos de Cloudinary al VPS).
6. Suscripciones y escalado (suscripciones, consumo, n8n en modo cola).

## 6. Pendientes identificados (fuera del MVP por ahora)

- Juntar mensajes seguidos del cliente antes de responder.
- Transcribir notas de voz.
- Entender fotos que manda el cliente.
- Seguimiento automático a quien dijo "lo pienso" (en WhatsApp requiere plantillas aprobadas).
- Importar el catálogo desde Excel.
- Protección contra abusos (intentos de engañar al bot, spam, límites de mensajes) y mensaje de respaldo si n8n o la IA fallan.
- Verificar si en Colombia se puede usar la app de WhatsApp Business y la API en el mismo número ("coexistencia").
- Otras verticales: restaurantes (pedidos y domicilios) y servicios (agenda de citas). El MVP es para tiendas con catálogo.

## 7. Costos y límites de referencia (verificar antes de decidir)

- **Hostinger VPS**: KVM 1 ~US$6.49/mes (4 GB RAM, 50 GB); KVM 2 ~US$8.79/mes (8 GB RAM, 100 GB, recomendado; renueva ~US$14.99); KVM 4 ~US$12.99/mes. Un KVM 2 aguantaría del orden de 20–40 negocios / ~10.000 mensajes al día (estimación).
- **n8n Community self-hosted**: sin límite de ejecuciones. La IA se paga aparte por tokens. Revisar la licencia de n8n antes de comercializar (no revender n8n ni dar acceso a él como si fuera propio).
- **Cloudinary Free**: 25 créditos (1 crédito = 1 GB guardado, 1 GB descargado o 1.000 transformaciones). Descargas y transformaciones en ventana móvil de 30 días; almacenamiento = lo guardado en el momento. Si se excede, puede suspender en vez de cobrar. Plus US$89–99/mes (225 créditos). Prohibido abrir varias cuentas para evitar los límites. Estimado: ~0,5 créditos/mes por negocio promedio.
- **WhatsApp Business API**: Meta cobra por mensajes de plantilla según país; las respuestas dentro de la ventana de 24 h no se cobran.

## 8. Competencia vista

Cliengo, Leadsales, Wati, Mercately, Respond.io, Kommo, Treble, B2Chat (Colombia), Wizybot (Colombia, para e-commerce), Funnelchat. También agencias y freelancers que lo hacen a la medida con n8n. Diferenciación pensada: precio en pesos, simplicidad para tiendas pequeñas, configuración hecha por nosotros, nicho local y soporte cercano.
