# Contexto del proyecto

Resumen de lo decidido durante la planeación (noviembre de 2026).

## 1. La idea

Agente de automatización para la atención primaria de cualquier tipo de negocio por WhatsApp:

- Responde a quienes solo piden información básica e intenta motivarlos a comprar, sin presionar.
- Si el cliente no compra, no pasa nada.
- Si el interés es alto (pregunta cómo pagar, disponibilidad, envíos o dice que quiere comprar), avisa al dueño con nombre, número y resumen, y el dueño cierra la venta personalmente.
- El bot debe sonar como una persona real (vendedora colombiana), no como una IA.

## 2. Por qué un solo sistema (SaaS) y un solo flujo de n8n

- Replicar el software por cliente obliga a actualizar cada copia a mano. Se eligió una sola plataforma multi-negocio.
- Un flujo de n8n es una "receta": cada mensaje crea una ejecución independiente en paralelo. 100 negocios × 300 mensajes/día ≈ 30.000 mensajes, menos de 1 por segundo en promedio.
- La personalidad de cada agente vive en la base de datos (ficha del negocio + plantilla por tipo de negocio). n8n llena los huecos del prompt en cada mensaje.
- Para crecer: n8n en modo cola (queue mode) con workers, memoria en Postgres/Redis, caché en la API, plan de pago del modelo de IA.

## 3. Arquitectura

```
Cliente → WhatsApp/Telegram → n8n ──► API Laravel ──► MySQL
                                │            └──► Fotos (Cloudinary o disco local)
                                ├──► Modelo IA (Gemini)
                                └──► Aviso al dueño (Telegram)
```

### Base de datos (MySQL)

- `plantillas`: id, tipo, texto_base (prompt con huecos `{{nombre}}`, `{{catalogo}}`, `{{tono}}`…)
- `negocios`: id, plantilla_id, nombre, tipo_negocio, whatsapp_phone_id (único), telefono_dueno, nombre_agente, nombre_asesor, tono, horario, direccion, info_envios, info_pagos, promociones, instrucciones_extra, plan, activo
- `usuarios`: id, negocio_id, nombre, email, password, rol (dueno, empleado, admin)
- `categorias`: id, negocio_id, nombre
- `productos`: id, negocio_id, categoria_id, nombre, descripcion, precio, variantes (json), stock, activo
- `producto_fotos`: id, producto_id, disco, ruta, url, orden
- `clientes`: id, negocio_id, atendido_por (usuario), telefono, nombre, nivel_interes, estado, bot_pausado, ultimo_mensaje_at
- `mensajes`: id, negocio_id, cliente_id, rol (cliente, bot, dueno), texto, media_url, created_at
- `suscripciones`: id, negocio_id, plan, estado, vence_el (lo que el negocio paga por la plataforma)

Campos de agente (`tono`, `instrucciones_extra`, `nombre_agente`, plantilla) solo los edita el rol admin.

### API para n8n (protegida con token)

- `GET /api/agente/config?phone_id=` → negocio + prompt armado (con caché)
- `GET /api/agente/productos?negocio_id=&buscar=` → productos activos con precio, stock y URLs de fotos
- `GET /api/agente/cliente?negocio_id=&telefono=` → cliente (lo crea si no existe) y `bot_pausado`
- `POST /api/agente/mensajes` → guarda cada mensaje
- `POST /api/agente/leads` → marca interés alto y dispara el aviso

### Flujo de n8n

1. Trigger (WhatsApp o Telegram; en pruebas, Chat Trigger).
2. HTTP Request → config del negocio.
3. HTTP Request → cliente; si `bot_pausado`, termina.
4. AI Agent con el prompt del negocio. Chat Model: Gemini. Memoria: clave `negocio_id + telefono`. Herramienta: HTTP Request Tool para buscar productos.
5. IF la respuesta contiene `[INTERES_ALTO]` → POST /leads y aviso al dueño.
6. Quitar la etiqueta, enviar la respuesta (y la foto si aplica).
7. POST /mensajes.

### Estados del cliente

nuevo → interés medio → interés alto → atendido (bot pausado) → vendido | perdido. Un perdido que vuelve a escribir regresa a nuevo.

## 4. Estado actual

- n8n corre en local (Windows, Node 22, `npx n8n`).
- Hay un flujo de prueba: Chat Trigger → AI Agent + Google Gemini Chat Model (modelo Flash Lite) + Simple Memory (ventana de 10 mensajes). El system message es el de `docs/prompt-cumbre-caps.md`.
- Lecciones: algunos modelos de Gemini ya no se ofrecen a usuarios nuevos (error 404); los Preview pueden saturarse (503); los modelos TTS devuelven audio y el texto sale vacío. La suscripción Pro de la app de Gemini no sirve para la API: la clave se saca gratis en aistudio.google.com.
- El patrón de subida a Cloudinary ya se usó en otro proyecto de la dueña (React + Firebase): subida directa con upload preset, se guarda `secure_url`, cola offline con reintentos.
- Issues #1 a #30 creados en GitHub con hitos por etapa. Falta crear el tablero Kanban en GitHub Projects (no se pudo desde la API).

## 5. Etapas

1. Base del sistema y catálogo (Laravel, migraciones, login por roles, negocios, productos, fotos).
2. Configuración del agente y conexión con n8n (plantillas, API config y productos, flujo conectado).
3. Clientes, interés alto y aviso al dueño (leads, Telegram, tablero, "Yo atiendo", historial).
4. Canales de mensajería (Telegram, WhatsApp Business API, fotos en el chat, memoria persistente).
5. Despliegue (VPS, backups, migrar fotos de Cloudinary al VPS).
6. Suscripciones y escalado (suscripciones, consumo, n8n en modo cola).

## 6. Costos y límites de referencia (verificar antes de decidir)

- **Hostinger VPS**: KVM 1 ~US$6.49/mes (4 GB RAM, 50 GB); KVM 2 ~US$8.79/mes (8 GB RAM, 100 GB, recomendado; renueva ~US$14.99); KVM 4 ~US$12.99/mes. Un KVM 2 aguantaría del orden de 20–40 negocios / ~10.000 mensajes al día (estimación).
- **n8n Community self-hosted**: sin límite de ejecuciones. La IA se paga aparte por tokens. Revisar la licencia de n8n antes de comercializar (no revender n8n ni dar acceso a él como si fuera propio).
- **Cloudinary Free**: 25 créditos (1 crédito = 1 GB guardado, 1 GB descargado o 1.000 transformaciones). Descargas y transformaciones en ventana móvil de 30 días; almacenamiento = lo guardado en el momento. Si se excede, puede suspender en vez de cobrar. Plus US$89–99/mes (225 créditos). Prohibido abrir varias cuentas para evitar los límites. Estimado: ~0,5 créditos/mes por negocio promedio.
- **WhatsApp Business API**: Meta cobra por mensajes de plantilla según país; las respuestas dentro de la ventana de 24 h no se cobran.

## 7. Competencia vista

Cliengo, Leadsales, Wati, Mercately, Respond.io, Kommo, Treble, B2Chat (Colombia), Wizybot (Colombia, para e-commerce), Funnelchat. También agencias y freelancers que lo hacen a la medida con n8n. Diferenciación pensada: precio en pesos, simplicidad para tiendas pequeñas, configuración hecha por nosotros, nicho local y soporte cercano.
