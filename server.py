# server.py con Flask-SocketIO y traducción al español
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
import requests

app = Flask(__name__)
socketio = SocketIO(app)

info_actual = {}
debilidades = []
movimientos_info = []

# Colores por tipo
type_colors = {
    'normal': '#A8A77A', 'fuego': '#EE8130', 'agua': '#6390F0', 'eléctrico': '#F7D02C',
    'planta': '#7AC74C', 'hielo': '#96D9D6', 'lucha': '#C22E28', 'veneno': '#A33EA1',
    'tierra': '#E2BF65', 'volador': '#A98FF3', 'psíquico': '#F95587', 'bicho': '#A6B91A',
    'roca': '#B6A136', 'fantasma': '#735797', 'dragón': '#6F35FC', 'siniestro': '#705746',
    'acero': '#B7B7CE', 'hada': '#D685AD'
}

def traducir_nombre(objeto, idioma='es'):
    for nombre in objeto.get('names', []):
        if nombre['language']['name'] == idioma:
            return nombre['name']
    return objeto.get('name', '').capitalize()

@app.route('/')
def index():
    if not info_actual:
        return render_template_string("""
    <html>
      <head>
        <script src=\"https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js\"></script>
        <script>
            var socket = io();
            socket.on('actualizar', () => {
                location.reload();
            });
        </script>
      </head>
      <body>
        <h2>Esperando datos de un Pokémon...</h2>
      </body>
    </html>""")

    nombre = traducir_nombre(info_actual)
    sprite = info_actual.get('sprites', {}).get('front_default', '')
    tipos = info_actual.get('translated_types', [])
    habilidades = info_actual.get('translated_abilities', [])
    debilidades_traducidas = info_actual.get('translated_d', [])

    return render_template_string("""
    <html>
    <head>
        <title>{{ nombre }}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
        <script>
            var socket = io();
            socket.on('actualizar', () => {
                location.reload();
            });
        </script>
        <style>
            body { font-family: Arial, sans-serif; background: #f0f0f0; padding: 30px; }
            .card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                max-width: 700px;
                margin: auto;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            h1, h2 { text-align: center; }
            img { display: block; margin: 0 auto 15px; }
            .badge {
                padding: 6px 14px;
                border-radius: 20px;
                font-weight: bold;
                color: white;
                margin: 4px;
                display: inline-block;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.4);
            }
            .tag {
                background: #444;
                padding: 5px 10px;
                border-radius: 12px;
                color: white;
                font-size: 14px;
                margin: 4px;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <img src="{{ sprite }}" alt="{{ nombre }}">
            <h1>{{ nombre }}</h1>

            <h2>Tipos</h2>
            <div style="text-align: center;">
                {% for tipo in tipos %}
                    <span class="badge" style="background-color: {{ type_colors[tipo.lower()] }}">{{ tipo }}</span>
                {% endfor %}
            </div>

            <h2>Habilidades</h2>
            <div style="text-align: center;">
                {% for hab in habilidades %}
                    <span class="tag">{{ hab }}</span>
                {% endfor %}
            </div>

            <h2>Movimientos (10 primeros)</h2>
            <div style="text-align: center;">
                {% for move in movimientos_info %}
                    <span class="badge" style="background-color: {{ type_colors[move.type.lower()] }}">{{ move.name }}</span>
                {% endfor %}
            </div>

            <h2>Debilidades</h2>
            <div style="text-align: center;">
                {% for tipo in debilidades_traducidas %}
                    <span class="badge" style="background-color: {{ type_colors[tipo.lower()] }}">{{ tipo }}</span>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, nombre=nombre, sprite=sprite, tipos=tipos, habilidades=habilidades,
           debilidades_traducidas=debilidades_traducidas, movimientos_info=movimientos_info, type_colors=type_colors)

@app.route('/update', methods=['POST'])
def update():
    global info_actual, debilidades, movimientos_info
    data = request.get_json()
    nombre = data.get("nombre", "").lower().strip()

    if not nombre:
        return jsonify({"error": "No se proporcionó nombre"}), 400

    print(f"Buscando info de: {nombre}")
    res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{nombre}")

    if res.status_code != 200:
        print(res.json)
        info_actual = {}
        debilidades = []
        movimientos_info = []
        return jsonify({"error": "Pokémon no encontrado"}), 404

    info_actual = res.json()

    # Traducir habilidades
    habilidades_traducidas = []
    for a in info_actual.get('abilities', []):
        try:
            ability_data = requests.get(a['ability']['url']).json()
            habilidades_traducidas.append(traducir_nombre(ability_data))
        except:
            habilidades_traducidas.append(a['ability']['name'].capitalize())
    info_actual['translated_abilities'] = habilidades_traducidas

    # Traducir tipos y debilidades
    tipos_traducidos = []
    debilidades_set = set()
    debilidades_traducidas = set()
    tipo_urls = [t['type']['url'] for t in info_actual['types']]
    for url in tipo_urls:
        tipo_data = requests.get(url).json()
        tipos_traducidos.append(traducir_nombre(tipo_data))
        for d in tipo_data['damage_relations']['double_damage_from']:
            debilidades_set.add(d['name'])
    info_actual['translated_types'] = sorted(tipos_traducidos)

    for tipo in debilidades_set:
        try:
            tipo_data = requests.get(f"https://pokeapi.co/api/v2/type/{tipo.lower()}").json()
            debilidades_traducidas.add(traducir_nombre(tipo_data))
        except:
            debilidades_traducidas.add(tipo.capitalize())

    info_actual['translated_d'] = sorted(debilidades_traducidas)

    # Movimientos
    movimientos_info = []
    for m in info_actual.get('moves', [])[:10]:
        move_name_raw = m['move']['name']
        move_url = m['move']['url']
        try:
            move_data = requests.get(move_url).json()
            move_type_en = move_data['type']['name']
            move_type_data = requests.get(f"https://pokeapi.co/api/v2/type/{move_type_en}").json()
            move_type = traducir_nombre(move_type_data)
            move_name = traducir_nombre(move_data)
            movimientos_info.append({"name": move_name, "type": move_type})
        except:
            movimientos_info.append({"name": move_name_raw.capitalize(), "type": "normal"})

    socketio.emit('actualizar')
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
