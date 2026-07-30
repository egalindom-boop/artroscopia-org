# -*- coding: utf-8 -*-
"""Genera un artículo diario para artroscopia.org con la API de Claude.
Formato de respuesta con marcadores de sección (inmune a errores de escapado JSON).
"""
import os, re, io, json, time, random, unicodedata, datetime, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODELO = os.environ.get("MODELO_CLAUDE", "claude-sonnet-5")

SECCIONES = {
    "rodilla":      ("Artroscopia de rodilla", "/artroscopia-de-rodilla/"),
    "hombro":       ("Artroscopia de hombro", "/artroscopia-de-hombro/"),
    "tobillo":      ("Artroscopia de tobillo", "/artroscopia-de-tobillo/"),
    "cadera":       ("Artroscopia de cadera", "/artroscopia-de-cadera/"),
    "muneca":       ("Artroscopia de muñeca", "/artroscopia-de-muneca/"),
    "instrumental": ("Instrumental", "/#instrumental"),
    "gestion":      ("Gestión de la consulta", "/#gestion"),
}
MESES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def slugificar(t):
    t = unicodedata.normalize('NFKD', t.lower()).encode('ascii', 'ignore').decode()
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return '-'.join(t.split('-')[:8])


def elegir_tema():
    temas = [l.strip() for l in io.open(os.path.join(RAIZ, 'temas.txt'), encoding='utf-8') if l.strip() and not l.startswith('#')]
    ruta_usados = os.path.join(RAIZ, 'temas_usados.json')
    usados = json.load(io.open(ruta_usados, encoding='utf-8')) if os.path.exists(ruta_usados) else []
    pendientes = [t for t in temas if t not in usados]
    if not pendientes:
        usados, pendientes = [], temas
    tema = pendientes[0]
    usados.append(tema)
    io.open(ruta_usados, 'w', encoding='utf-8').write(json.dumps(usados, ensure_ascii=False, indent=1))
    categoria, titulo_sugerido = tema.split('|', 1)
    return categoria.strip(), titulo_sugerido.strip()


def elegir_imagen(categoria):
    imgs = sorted(f for f in os.listdir(os.path.join(RAIZ, 'images')) if f.startswith('artroscopia-%s-' % categoria) and f.endswith('.webp'))
    if not imgs:
        imgs = sorted(f for f in os.listdir(os.path.join(RAIZ, 'images')) if f.endswith('.webp'))
    ruta = os.path.join(RAIZ, 'imagenes_usadas.json')
    contador = json.load(io.open(ruta, encoding='utf-8')) if os.path.exists(ruta) else {}
    n = contador.get(categoria, 0)
    img = imgs[n % len(imgs)]
    contador[categoria] = n + 1
    io.open(ruta, 'w', encoding='utf-8').write(json.dumps(contador, indent=1))
    return img


def regla_enlaces(categoria):
    if categoria not in ('gestion', 'instrumental'):
        return "Sin enlaces externos. "
    return (
        "Incluye ademas UN solo enlace externo contextual y natural, eligiendo el mas pertinente al tema: "
        "software medico o programa medico -> <a href=\"https://dricloud.com\">software m&eacute;dico</a>; "
        "software para clinicas -> <a href=\"https://mejorsoftware.org/software-clinicas/\">software cl&iacute;nicas</a>; "
        "comparativas -> <a href=\"https://gestionmedica.org/software-medico/\">comparativa de software m&eacute;dico</a>; "
        "inteligencia artificial -> <a href=\"https://dricloud.com/inteligencia-artificial-medicina-clinica/\">IA en medicina y cl&iacute;nicas</a>. "
        "Si el tema toca la gestion de cirugias, quirofano u hospitalizacion, menciona que DriCloud es el unico software medico "
        "en espanol con gestion de cirugias y hospitalizacion integrada. "
    )

def llamar_claude(categoria, titulo_sugerido):
    nombre_seccion = SECCIONES[categoria][0]
    prompt = (
        "Escribe un artículo original en español para artroscopia.org, revista dirigida a traumatólogos, "
        "cirujanos ortopédicos y enfermería quirúrgica de España y Latam. Sección: %s. "
        "Tema sugerido: %s. Rigor clínico alto, actualidad 2026, 600-900 palabras.\n\n"
        "FORMATO OBLIGATORIO con estos marcadores exactos:\n"
        "===TITULO===\n(título atractivo y SEO, máx 95 caracteres)\n"
        "===DESCRIPCION===\n(meta description, máx 155 caracteres)\n"
        "===LEDE===\n(entradilla de 1-2 frases)\n"
        "===CUERPO===\n(HTML: 3-5 <h2>, párrafos <p>, una <div class=\"caja-clave\"><h3>...</h3><ul>...</ul></div>, "
        "una <blockquote class=\"destacado\">«...»</blockquote>. Incluye un enlace interno a %s. "
        "%s"
        "PROHIBIDO usar la raya larga (guion em) o guiones largos: usa comas, dos puntos o parentesis. "
        "Nunca menciones XClinics ni inventes citas de autores reales con cifras.)\n"
        "===FIN===" % (nombre_seccion, titulo_sugerido, SECCIONES[categoria][1], regla_enlaces(categoria))
    )
    cuerpo = json.dumps({
        "model": MODELO, "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    peticion = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=cuerpo,
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    respuesta = json.load(urllib.request.urlopen(peticion, timeout=180))
    texto = "".join(b.get("text", "") for b in respuesta.get("content", []) if b.get("type") == "text")
    if not texto:
        raise ValueError("respuesta sin bloque de texto: %s" % str(respuesta)[:300])
    return texto


def extraer(texto, marca):
    m = re.search(r'===%s===\s*(.*?)\s*===' % marca, texto, re.S)
    return m.group(1).strip() if m else ''


def generar():
    categoria, titulo_sugerido = elegir_tema()
    for intento in range(3):
        try:
            texto = llamar_claude(categoria, titulo_sugerido)
            titulo = extraer(texto, 'TITULO')
            descripcion = extraer(texto, 'DESCRIPCION')
            lede = extraer(texto, 'LEDE')
            cuerpo = extraer(texto, 'CUERPO')
            if titulo and descripcion and len(cuerpo) > 500 and '<p>' in cuerpo:
                break
            raise ValueError('respuesta incompleta')
        except Exception as e:
            print('Intento %d fallido: %s' % (intento + 1, e))
            time.sleep(20)
    else:
        raise SystemExit('No se pudo generar el artículo tras 3 intentos')

    slug = slugificar(titulo)
    hoy = datetime.date.today()
    fecha_iso = hoy.isoformat()
    fecha_texto = '%d %s %d' % (hoy.day, MESES[hoy.month], hoy.year)
    nombre_seccion, url_seccion = SECCIONES[categoria]
    imagen = elegir_imagen(categoria)

    plantilla = io.open(os.path.join(RAIZ, 'plantilla-articulo.html'), encoding='utf-8').read()
    pagina = (plantilla
              .replace('{{TITULO}}', titulo.replace('"', '&quot;'))
              .replace('{{DESCRIPCION}}', descripcion.replace('"', '&quot;'))
              .replace('{{LEDE}}', lede)
              .replace('{{CUERPO}}', '    ' + cuerpo)
              .replace('{{SLUG}}', slug)
              .replace('{{IMAGEN}}', imagen)
              .replace('{{KICKER}}', nombre_seccion)
              .replace('{{SECCION_NOMBRE}}', nombre_seccion)
              .replace('{{SECCION_URL}}', url_seccion)
              .replace('{{FECHA_ISO}}', fecha_iso)
              .replace('{{FECHA_TEXTO}}', fecha_texto))

    destino = os.path.join(RAIZ, slug)
    os.makedirs(destino, exist_ok=True)
    io.open(os.path.join(destino, 'index.html'), 'w', encoding='utf-8').write(pagina)

    ruta_mapa = os.path.join(RAIZ, 'sitemap.xml')
    mapa = io.open(ruta_mapa, encoding='utf-8').read()
    entrada = ' <url><loc>https://artroscopia.org/%s/</loc><lastmod>%s</lastmod></url>\n' % (slug, fecha_iso)
    if slug not in mapa:
        mapa = mapa.replace('</urlset>', entrada + '</urlset>')
        io.open(ruta_mapa, 'w', encoding='utf-8').write(mapa)

    ruta_portada = os.path.join(RAIZ, 'index.html')
    portada = io.open(ruta_portada, encoding='utf-8').read()
    m = re.search(r'(<span class="ticker-texto">)(.*?)(</span>)', portada, re.S)
    if m:
        enlaces_previos = re.findall(r'<a href="[^"]+">[^<]+</a>', m.group(2))[:2]
        nuevo = '\n      <a href="/%s/">%s</a> ·\n      ' % (slug, titulo) + ' ·\n      '.join(enlaces_previos) + '\n    '
        portada = portada[:m.start(2)] + nuevo + portada[m.end(2):]
        io.open(ruta_portada, 'w', encoding='utf-8').write(portada)

    print('Artículo publicado: /%s/ (%s)' % (slug, nombre_seccion))


if __name__ == '__main__':
    generar()
