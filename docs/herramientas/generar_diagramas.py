import html, os, re, sys
# Genera diagramas-saas.drawio en la raíz del repositorio.
# Uso: python docs/herramientas/generar_diagramas.py
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
os.makedirs(OUT, exist_ok=True)

class D:
    def __init__(s, name): s.name = name; s.c = []; s.n = 2
    def id(s): s.n += 1; return f"c{s.n}"
    def v(s, val, x, y, w, h, style, parent="1"):
        i = s.id(); s.c.append(f'<mxCell id="{i}" value="{html.escape(val, quote=True)}" style="{style}" vertex="1" parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'); return i
    def e(s, src, tgt, style, val=""):
        i = s.id(); s.c.append(f'<mxCell id="{i}" value="{html.escape(val, quote=True)}" style="{style}" edge="1" parent="1" source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry"/></mxCell>'); return i
    def ep(s, x1, y1, x2, y2, style, val=""):
        i = s.id(); s.c.append(f'<mxCell id="{i}" value="{html.escape(val, quote=True)}" style="{style}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" as="targetPoint"/></mxGeometry></mxCell>'); return i
    def xml(s, idx):
        return f'<diagram id="p{idx}" name="{html.escape(s.name)}"><mxGraphModel grid="1" gridSize="10" page="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(s.c)}</root></mxGraphModel></diagram>'

G = "#1f7a55"; GS = "#e3f1ea"; NAR = "#b4621d"; NARS = "#fff4e6"; ROJ = "#a33b3b"; ROJS = "#f3e4e4"
pages = []

# ---------------------------------------------------------------- 1. Base de datos
d = D("Base de datos")
tables = {
 "plantillas": [("PK","id int"),("","tipo varchar"),("","texto_base text")],
 "negocios": [("PK","id int"),("FK","plantilla_id int"),("","nombre varchar"),("","tipo_negocio varchar"),
   ("","canal enum(telegram,whatsapp)"),("UK","canal_identificador varchar"),("","canal_token varchar (cifrado)"),
   ("","aviso_chat_id varchar"),("","minutos_reaviso int"),("","telefono_dueno varchar"),
   ("","nombre_agente varchar"),("","nombre_asesor varchar"),("","tono varchar"),("","instrucciones_extra text"),
   ("","horario json"),("","direccion text"),("","info_envios text"),("","medios_pago text"),("","promociones text"),
   ("","plan varchar"),("","activo boolean")],
 "usuarios": [("PK","id int"),("FK","negocio_id int"),("","nombre varchar"),("UK","email varchar"),("","password varchar"),("","rol enum(dueno,empleado,admin)")],
 "suscripciones": [("PK","id int"),("FK","negocio_id int"),("","plan varchar"),("","estado varchar"),("","vence_el date")],
 "categorias": [("PK","id int"),("FK","negocio_id int"),("","nombre varchar")],
 "productos": [("PK","id int"),("FK","negocio_id int"),("FK","categoria_id int"),("","nombre varchar"),("","descripcion text"),("","precio decimal"),("","variantes json"),("","stock int"),("","activo boolean")],
 "producto_fotos": [("PK","id int"),("FK","producto_id int"),("","disco varchar (cloudinary, local)"),("","ruta varchar"),("","url varchar"),("","orden int")],
 "clientes": [("PK","id int"),("FK","negocio_id int"),("","canal_chat_id varchar"),("","telefono varchar"),("","nombre varchar"),
   ("","estado enum(nuevo,interes_medio,por_atender,en_atencion,vendido,perdido)"),
   ("","bot_pausado boolean"),("","ultimo_mensaje_at datetime")],
 "atenciones": [("PK","id int"),("FK","negocio_id int"),("FK","cliente_id int"),("FK","asignado_a int (usuario)"),
   ("","motivo enum(compra,pago,comprobante,descuento,reclamo,pide_persona,otro)"),("","resumen text"),
   ("","datos_interes json (producto, variante, cantidad, ciudad)"),
   ("","estado enum(por_atender,en_atencion,vendido,perdido,devuelta_al_bot)"),("","monto_venta decimal"),("","notas text"),
   ("","creada_at datetime"),("","tomada_at datetime"),("","cerrada_at datetime"),("","ultimo_aviso_at datetime")],
 "mensajes": [("PK","id int"),("FK","negocio_id int"),("FK","cliente_id int"),("FK","atencion_id int"),("FK","usuario_id int"),
   ("","rol enum(cliente,bot,humano)"),("","tipo enum(texto,imagen,audio)"),("","texto text"),("","media_url varchar"),
   ("","canal_mensaje_id varchar"),("","created_at datetime")],
}
W = 330; R = 24
pos = {"plantillas": (40, 40), "negocios": (420, 40), "usuarios": (820, 40), "suscripciones": (40, 240),
       "categorias": (40, 460), "productos": (420, 640), "producto_fotos": (40, 640),
       "clientes": (1220, 40), "atenciones": (820, 300), "mensajes": (1220, 360)}
ids = {}
for t, rows in tables.items():
    x, y = pos[t]
    fill = NAR if t == "atenciones" else G
    tid = d.v(t, x, y, W, 30 + R * len(rows), f"swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;resizeParent=1;resizeLast=0;collapsible=1;marginBottom=0;rounded=1;arcSize=4;fillColor={fill};fontColor=#ffffff;strokeColor={fill};swimlaneFillColor=#ffffff;fontSize=13;")
    ids[t] = tid
    for k, (key, txt) in enumerate(rows):
        lab = (f"{key}  " if key else "      ") + txt
        st = "text;align=left;verticalAlign=middle;spacingLeft=8;fontSize=11;fontFamily=Courier New;whiteSpace=wrap;" + ("fontStyle=1;" if key == "PK" else "") + ("fontColor=#b4621d;" if key in ("FK", "UK") else "fontColor=#1d2420;")
        d.v(lab, 0, 30 + R * k, W, R, st, parent=tid)
rel = "edgeStyle=entityRelationEdgeStyle;rounded=0;html=1;endArrow=ERmany;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#5d6a62;fontSize=11;"
rel01 = rel.replace("startArrow=ERmandOne", "startArrow=ERzeroToOne")
for a, b, l in [("plantillas","negocios","sirve de base"),("negocios","usuarios","tiene"),("negocios","suscripciones","paga"),
                ("negocios","categorias","organiza"),("negocios","productos","vende"),("categorias","productos","agrupa"),
                ("productos","producto_fotos","tiene"),("negocios","clientes","atiende"),("clientes","atenciones","genera"),
                ("negocios","atenciones","recibe"),("clientes","mensajes","escribe"),("negocios","mensajes","registra")]:
    d.e(ids[a], ids[b], rel, l)
d.e(ids["usuarios"], ids["atenciones"], rel01, "atiende (asignado_a)")
d.e(ids["atenciones"], ids["mensajes"], rel01, "agrupa")
d.e(ids["usuarios"], ids["mensajes"], rel01, "escribe (humano)")
d.v("<b>atenciones</b> = cada vez que el bot pasa un cliente a una persona.<br>Ahí queda el motivo, el resumen, los datos del interés,<br>quién lo atiende y el monto si se vendió.",
    820, 680, 330, 80, "shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#fff4e6;strokeColor=#b4621d;fontSize=11;align=left;spacingLeft=8;")
pages.append(d)

# ---------------------------------------------------------------- 2. Actores
d = D("Actores")
acts = [("Cliente final", "Escribe por Telegram (MVP) o WhatsApp. Curiosea, pregunta precios o quiere comprar."),
        ("Dueño del negocio", "Mantiene el catálogo y los datos del negocio. Atiende a los clientes que el bot le pasa."),
        ("Empleado", "Atiende la lista 'Por atender': concreta la venta, verifica el pago y la marca vendida."),
        ("Administradora", "Crea negocios, configura el agente de cada uno, plantillas y suscripciones.")]
for i, (n, t) in enumerate(acts):
    x = 40 + i * 290
    d.v(n, x + 100, 40, 40, 70, f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;fontStyle=1;strokeColor={G};fillColor={GS};")
    d.v(t, x, 150, 240, 80, f"rounded=1;whiteSpace=wrap;fillColor={GS};strokeColor={G};fontSize=12;")
sis = [("Agente IA (n8n)", "Atiende, busca en el catálogo y, en un momento importante, deja un último mensaje, se pausa y pasa el cliente a una persona."),
       ("Tareas programadas (Laravel)", "Vuelven a avisar si un cliente lleva mucho tiempo sin ser atendido."),
       ("Servicios externos", "Telegram, WhatsApp Business API, Gemini y Cloudinary.")]
for i, (n, t) in enumerate(sis):
    x = 40 + i * 390
    d.v("<b>" + n + "</b><br><br>" + t, x, 280, 340, 110, f"rounded=1;whiteSpace=wrap;html=1;fillColor={NARS};strokeColor={NAR};fontSize=12;dashed=1;")
pages.append(d)

# ---------------------------------------------------------------- 3. Casos de uso
d = D("Casos de uso")
uc = f"ellipse;whiteSpace=wrap;fillColor=#ffffff;strokeColor={G};fontSize=12;"
ucn = f"ellipse;whiteSpace=wrap;fillColor={NARS};strokeColor={NAR};fontSize=12;fontStyle=1;"
box = "rounded=0;whiteSpace=wrap;verticalAlign=top;fontStyle=1;fontSize=14;fillColor={};strokeColor=#9aa89f;"
act = f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;fontStyle=1;strokeColor={G};fillColor={GS};"
actS = f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;fontStyle=1;strokeColor={NAR};fillColor={NARS};"
line = "endArrow=none;strokeColor=#5d6a62;"
inc = f"dashed=1;endArrow=open;strokeColor={NAR};fontSize=10;fontColor={NAR};"
def group(title, x, y, items, fill, w=260):
    h = 50 + len(items) * 62
    d.v(title, x, y, w, h, box.format(fill))
    out = []
    for k, t in enumerate(items):
        nuevo = t.startswith("*"); t = t.lstrip("*")
        out.append(d.v(t, x + 20, y + 40 + k * 62, w - 40, 48, ucn if nuevo else uc))
    return out
chat = group("Atención por chat", 260, 40, ["Enviar mensaje", "Consultar productos y precios", "Ver fotos de productos",
             "Preguntar envíos y medios de pago", "*Pedir comprar, pagar, descuento o hablar con una persona"], "#f6f7f4")
ag = group("Agente IA", 640, 40, ["Identificar negocio por canal", "Cargar configuración, prompt y horario", "Verificar si el bot está pausado",
           "Buscar en el catálogo", "Enviar foto del producto", "*Detectar momento importante",
           "*Pasar a una persona (último mensaje + pausa)", "Guardar conversación"], "#fff8ef")
pan = group("Panel del negocio", 260, 520, ["Iniciar sesión", "Editar datos del negocio", "Gestionar catálogo y fotos",
            "*Ver lista 'Por atender'", "*Tomar una atención", "*Responder al cliente desde el panel",
            "*Verificar pago y marcar vendido con monto", "Marcar perdido", "*Devolver el cliente al bot", "Ver historial de chats"], "#f6f7f4")
avi = group("Avisos", 640, 620, ["*Avisar al encargado (nuevo cliente o mensaje nuevo)", "*Reavisar si nadie atiende"], "#fff8ef")
adm = group("Administración del SaaS", 640, 860, ["Crear y activar negocios", "Configurar el agente (tono, reglas, prompt)",
            "Gestionar plantillas por tipo", "Gestionar suscripciones", "Revisar uso y consumo"], "#f6f7f4")
C = d.v("Cliente final", 80, 180, 40, 70, act)
IA = d.v("Agente IA (n8n)", 1020, 280, 40, 70, actS)
DU = d.v("Dueño / Empleado", 80, 800, 40, 70, act)
TP = d.v("Tareas programadas", 1020, 680, 40, 70, actS)
AD = d.v("Administradora", 1020, 960, 40, 70, act)
for u in chat: d.e(C, u, line)
for u in ag: d.e(IA, u, line)
for u in pan: d.e(DU, u, line)
d.e(TP, avi[1], line)
for u in adm: d.e(AD, u, line)
for a, b, l in [(chat[0], ag[0], "«incluye»"), (ag[0], ag[1], "«incluye»"), (ag[1], ag[2], "«incluye»"),
                (chat[1], ag[3], "«usa»"), (chat[2], ag[4], "«usa»"), (chat[4], ag[5], "«dispara»"),
                (ag[5], ag[6], "«incluye»"), (ag[6], avi[0], "«dispara»"), (avi[0], pan[3], "«alimenta»"),
                (pan[3], pan[4], ""), (pan[8], ag[2], "«reactiva»"), (adm[1], ag[1], "«configura»"),
                (adm[2], ag[1], "«define»"), (pan[1], ag[1], "«aporta datos»")]:
    d.e(a, b, inc, l)
d.v("Naranja = casos nuevos del diseño de paso a una persona", 260, 1220, 380, 30, f"rounded=1;fillColor={NARS};strokeColor={NAR};fontSize=11;")
pages.append(d)

# ---------------------------------------------------------------- 4. Secuencia
d = D("Flujo de un mensaje")
parts = ["Cliente", "Telegram / WhatsApp", "n8n", "API Laravel", "MySQL", "Gemini", "Dueño / Empleado"]
X = {}
H = 1620
for i, p in enumerate(parts):
    x = 40 + i * 200; X[i] = x + 75
    if p in ("Cliente", "Dueño / Empleado"):
        st = f"shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;container=1;collapsible=0;recursiveResize=0;size=40;fillColor={GS};strokeColor={G};fontStyle=1;verticalAlign=top;spacingTop=36;"
    else:
        st = f"shape=umlLifeline;perimeter=lifelinePerimeter;container=1;collapsible=0;recursiveResize=0;size=40;fillColor={GS};strokeColor={G};fontStyle=1;fontSize=12;"
    d.v(p, x, 40, 150, H, st)
msgs = [
 (0,1,'"Quiero las 2 negras planas, ¿cómo pago?"',0),
 (1,2,"Webhook (canal, chat_id)",0),
 (2,3,"GET /agente/config",0),
 (3,4,"Negocio + plantilla + horario",0),
 (3,2,"Prompt armado (abierto ahora: sí)",1),
 (2,3,"GET /agente/cliente",0),
 (3,2,"bot_pausado = no",1),
 (2,3,"POST /agente/mensajes (cliente)",0),
 (2,5,"Mensaje + prompt + memoria",0),
 (5,2,"Herramienta: buscar_productos",0),
 (2,3,"GET /agente/productos",0),
 (3,2,"Productos, precios y fotos",1),
 (5,2,"Herramienta: pasar_a_persona(motivo=pago, resumen, datos)",0),
 (2,3,"POST /agente/atenciones",0),
 (3,4,"Atención 'por atender' + bot_pausado = sí",0),
 (3,2,"Webhook enviar-aviso",0),
 (2,6,"Aviso: cliente, motivo, resumen y datos",0),
 (5,2,"Último mensaje",1),
 (2,1,"Enviar respuesta",0),
 (1,0,'"Listo, Andrés te confirma el pago por aquí 👌"',0),
 (2,3,"POST /agente/mensajes (bot)",0),
 ("NOTA","Desde aquí el bot no responde a este cliente"),
 (0,1,'"Ok, quedo atento"',0),
 (1,2,"Webhook",0),
 (2,3,"GET /agente/cliente → bot_pausado = sí",0),
 (2,3,"POST /agente/mensajes (cliente)",0),
 (3,2,"Webhook enviar-aviso (mensaje nuevo)",0),
 (2,6,"Aviso: el cliente escribió de nuevo",0),
 (6,3,"Panel: tomar atención",0),
 (6,3,"Panel: escribir respuesta",0),
 (3,2,"Webhook enviar-mensaje",0),
 (2,1,"Enviar mensaje del empleado",0),
 (1,0,'"Hola, te comparto los datos de pago…"',0),
 (6,3,"Verificar pago y marcar vendido ($122.000)",0),
 (3,4,"Atención = vendido, monto_venta",0),
]
y = 120
for m in msgs:
    if m[0] == "NOTA":
        d.v(m[1], X[1] - 40, y - 6, X[4] - X[1] + 80, 34, f"shape=note;whiteSpace=wrap;size=12;fillColor={NARS};strokeColor={NAR};fontSize=12;fontStyle=1;")
        y += 48; continue
    a, b, l, ret = m
    st = "html=1;verticalAlign=bottom;fontSize=11;strokeColor=#1d2420;" + ("dashed=1;endArrow=open;" if ret else "endArrow=block;endFill=1;")
    if a == b: continue
    d.ep(X[a], y, X[b], y, st, l); y += 40
pages.append(d)

# ---------------------------------------------------------------- 5. Estados del cliente
d = D("Estados del cliente")
st = f"rounded=1;arcSize=30;whiteSpace=wrap;fillColor={GS};strokeColor={G};fontStyle=1;fontSize=13;"
stN = f"rounded=1;arcSize=30;whiteSpace=wrap;fillColor={NARS};strokeColor={NAR};fontStyle=1;fontSize=13;"
ini = d.v("", 40, 215, 30, 30, "ellipse;fillColor=#1d2420;strokeColor=#1d2420;")
N = d.v("Nuevo", 130, 200, 130, 60, st)
M = d.v("Interés medio", 360, 60, 150, 60, st)
P = d.v("Por atender\n(bot pausado)", 380, 320, 160, 70, stN)
A = d.v("En atención\n(bot pausado)", 680, 320, 160, 70, stN)
V = d.v("Vendido\n(con monto)", 960, 200, 140, 60, st)
L = d.v("Perdido", 960, 460, 140, 60, f"rounded=1;arcSize=30;whiteSpace=wrap;fillColor={ROJS};strokeColor={ROJ};fontStyle=1;fontSize=13;")
tr = "endArrow=block;endFill=1;strokeColor=#5d6a62;fontSize=11;html=1;edgeStyle=orthogonalEdgeStyle;rounded=1;"
trB = tr.replace("#5d6a62", NAR) + f"fontColor={NAR};dashed=1;"
for a, b, l, s in [(ini, N, "primer mensaje", tr), (N, M, "pregunta precios o modelos", tr),
                   (N, P, "momento importante", tr), (M, P, "quiere comprar, pagar, descuento o una persona", tr),
                   (M, L, "no vuelve a escribir", tr), (P, A, "un empleado la toma", tr),
                   (A, V, "pago verificado", tr), (A, L, "no compra", tr),
                   (P, M, "devuelto al bot", trB), (A, M, "devuelto al bot", trB),
                   (V, M, "vuelve a escribir", trB), (L, N, "vuelve a escribir", trB)]:
    d.e(a, b, s, l)
d.e(P, P, "endArrow=block;endFill=1;strokeColor=#b4621d;fontColor=#b4621d;fontSize=11;html=1;edgeStyle=orthogonalEdgeStyle;rounded=1;exitX=0.25;exitY=1;entryX=0.75;entryY=1;loop=1;", "reaviso cada X min si nadie la toma")
d.v("Mientras el cliente está 'Por atender' o 'En atención', el bot no responde.\nLos mensajes nuevos se guardan y avisan al encargado.", 360, 560, 520, 50, f"shape=note;whiteSpace=wrap;size=12;fillColor={NARS};strokeColor={NAR};fontSize=12;")
pages.append(d)

# ---------------------------------------------------------------- 6. Arquitectura
d = D("Arquitectura")
bx = lambda t, x, y, w, h, f=GS, s=G: d.v(t, x, y, w, h, f"rounded=1;whiteSpace=wrap;html=1;fillColor={f};strokeColor={s};fontSize=12;")
cl = d.v("Cliente", 40, 230, 40, 70, act)
ch = bx("<b>Telegram</b> (MVP)<br>WhatsApp Business API", 150, 220, 170, 90)
n8n = d.v("n8n", 400, 60, 260, 420, f"rounded=1;whiteSpace=wrap;verticalAlign=top;fontStyle=1;fontSize=14;fillColor=#fff8ef;strokeColor={NAR};")
f1 = bx("<b>Flujo: mensajes entrantes</b><br>config → cliente → ¿pausado?<br>→ Agente IA (buscar_productos,<br>pasar_a_persona) → responder", 420, 100, 220, 110, NARS, NAR)
f2 = bx("<b>Webhook: enviar-mensaje</b><br>respuestas del empleado", 420, 240, 220, 70, NARS, NAR)
f3 = bx("<b>Webhook: enviar-aviso</b><br>avisos al encargado", 420, 340, 220, 70, NARS, NAR)
lar = d.v("Laravel", 760, 60, 260, 420, f"rounded=1;whiteSpace=wrap;verticalAlign=top;fontStyle=1;fontSize=14;fillColor=#f6f7f4;strokeColor={G};")
api = bx("<b>API del agente</b><br>/agente/config, cliente,<br>productos, mensajes, atenciones", 780, 100, 220, 90)
pnl = bx("<b>Panel web</b><br>catálogo, 'Por atender',<br>chat, ventas, admin", 780, 220, 220, 90)
job = bx("<b>Tareas programadas</b><br>reaviso si nadie atiende", 780, 340, 220, 70)
gem = bx("<b>Gemini</b><br>modelo de IA", 420, 540, 220, 60, "#ffffff", "#5d6a62")
db = d.v("MySQL", 800, 540, 80, 80, f"shape=cylinder3;whiteSpace=wrap;boundedLbl=1;size=12;fillColor={GS};strokeColor={G};fontStyle=1;")
rd = d.v("Redis", 900, 540, 80, 80, f"shape=cylinder3;whiteSpace=wrap;boundedLbl=1;size=12;fillColor={GS};strokeColor={G};fontStyle=1;")
ph = bx("<b>Fotos</b><br>Cloudinary (MVP)<br>o disco del VPS", 1080, 540, 160, 80, "#ffffff", "#5d6a62")
em = d.v("Dueño / Empleado", 1140, 240, 40, 70, act)
a = "endArrow=block;endFill=1;strokeColor=#5d6a62;fontSize=11;html=1;"
ab = a + "startArrow=block;startFill=1;"
d.e(cl, ch, ab, "mensajes")
d.e(ch, f1, a, "webhook")
d.e(f2, ch, a, "envía")
d.e(f3, ch, a, "avisa")
d.e(f1, api, ab, "HTTP + token")
d.e(f1, gem, ab, "")
d.e(api, f3, a, "dispara")
d.e(pnl, f2, a, "dispara")
d.e(job, f3, a, "dispara")
d.e(api, db, ab, "")
d.e(pnl, rd, ab, "caché")
d.e(pnl, ph, ab, "fotos")
d.e(em, pnl, ab, "usa")
d.v("Regla: Laravel decide y guarda; n8n es la única puerta de entrada y salida de mensajes y la que habla con la IA.\nAsí, cambiar de Telegram a WhatsApp solo toca n8n.", 40, 660, 700, 50, f"shape=note;whiteSpace=wrap;size=12;fillColor={NARS};strokeColor={NAR};fontSize=12;")
pages.append(d)

xml = '<mxfile host="app.diagrams.net">' + "".join(p.xml(i + 1) for i, p in enumerate(pages)) + '</mxfile>'
open(f"{OUT}/diagramas-saas.drawio", "w", encoding="utf-8").write(xml)
print("ok", [p.name for p in pages])
