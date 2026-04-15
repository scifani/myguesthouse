import base64
import logging
import os
import tempfile
from datetime import datetime

from flask import Flask, jsonify, render_template, request, Response
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from registration.models.apartment import Apartment, Base as ApartmentBase
from registration.models.guest import Guest, GuestGender, GuestType
from registration.services.alloggiatiweb_api import AlloggiatiWebApi
from registration.services.mrz_reader import MrzReader
from registration.services.registration_service import RegistrationService
from registration.services.table_service import TableService
from registration.utils.guest_mapper import GuestMapper

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ── database ──────────────────────────────────────────────────────────────────

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(_DATA_DIR, exist_ok=True)
_DB_PATH = os.path.join(_DATA_DIR, 'myguesthouse.db')
_engine = create_engine(f'sqlite:///{_DB_PATH}')
ApartmentBase.metadata.create_all(_engine)
_Session = sessionmaker(bind=_engine)

# Idempotent migration: add ROSS1000 columns if they don't exist yet
with _engine.connect() as _conn:
    _existing = {row[1] for row in _conn.execute(text('PRAGMA table_info(registration_apartments)'))}
    for _col, _def in [
        ('cin', 'VARCHAR(50)'), ('cir', 'VARCHAR(50)'),
        ('comune', 'VARCHAR(100)'), ('indirizzo', 'VARCHAR(200)'),
        ('ross_codice', 'VARCHAR(10)'), ('ross_camere', 'INTEGER'), ('ross_letti', 'INTEGER'),
    ]:
        if _col not in _existing:
            _conn.execute(text(f'ALTER TABLE registration_apartments ADD COLUMN {_col} {_def}'))
    _conn.commit()

# ── lookup tables + MRZ ───────────────────────────────────────────────────────

_TABLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'registration', 'tables')
table_service = TableService(_TABLES_DIR)
guest_mapper = GuestMapper(table_service)

# ── AlloggiatiWeb API cache (keyed by apartment id) ───────────────────────────

_api_cache: dict[str, AlloggiatiWebApi] = {}


def _get_api(apartment_id: str) -> AlloggiatiWebApi:
    if apartment_id not in _api_cache:
        with _Session() as session:
            apt = session.get(Apartment, apartment_id)
            if apt is None:
                raise ValueError(f"Appartamento non trovato: {apartment_id}")
            _api_cache[apartment_id] = AlloggiatiWebApi(
                apt.aw_user, apt.aw_password, apt.aw_ws_key
            )
    return _api_cache[apartment_id]


# ── helpers ───────────────────────────────────────────────────────────────────

_GUEST_TYPE_MAP = {
    '16': GuestType.SINGLE,
    '17': GuestType.HOUSE_HEAD,
    '18': GuestType.GROUP_LEADER,
    '19': GuestType.FAMILY_MEMBER,
    '20': GuestType.GROUP_MEMBER,
}

_GENDER_MAP = {
    'M': GuestGender.MALE,
    'F': GuestGender.FEMALE,
    'X': GuestGender.UNKNOWN,
}

_GUEST_TYPE_LABELS = {
    '16': 'Ospite Singolo',
    '17': 'Capo Famiglia',
    '18': 'Capo Gruppo',
    '19': 'Familiare',
    '20': 'Membro Gruppo',
}

# ── routes: static ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/guest-types')
def guest_types():
    return jsonify([{'code': k, 'label': v} for k, v in _GUEST_TYPE_LABELS.items()])


@app.route('/api/document-types')
def document_types():
    return jsonify([{'code': c, 'label': d} for c, d in table_service.get_document_types()])


@app.route('/api/municipalities')
def municipalities():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify([{'code': c, 'label': f"{n} ({p})", 'name': n, 'province': p}
                    for c, n, p in table_service.search_municipalities(q)])


@app.route('/api/countries')
def countries():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify([{'code': c, 'label': n} for c, n in table_service.search_countries(q)])


@app.route('/api/places')
def places():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    return jsonify(table_service.search_places(q))


# ── routes: apartments ────────────────────────────────────────────────────────

@app.route('/api/apartments', methods=['GET'])
def list_apartments():
    with _Session() as session:
        apts = session.query(Apartment).order_by(Apartment.name).all()
        return jsonify([a.to_dict() for a in apts])


@app.route('/api/apartments', methods=['POST'])
def create_apartment():
    data = request.json
    for field in ('name', 'aw_user', 'aw_password', 'aw_ws_key'):
        if not data.get(field):
            return jsonify({'error': f"Campo obbligatorio: {field}"}), 400
    with _Session() as session:
        apt = Apartment(
            id=__import__('uuid').uuid4().__str__(),
            name=data['name'],
            aw_user=data['aw_user'],
            aw_password=data['aw_password'],
            aw_ws_key=data['aw_ws_key'],
            cin=data.get('cin') or None,
            cir=data.get('cir') or None,
            comune=data.get('comune') or None,
            indirizzo=data.get('indirizzo') or None,
            ross_codice=data.get('ross_codice') or None,
            ross_camere=int(data['ross_camere']) if data.get('ross_camere') else None,
            ross_letti=int(data['ross_letti']) if data.get('ross_letti') else None,
        )
        session.add(apt)
        try:
            session.commit()
        except Exception:
            return jsonify({'error': "Nome appartamento già esistente"}), 409
        return jsonify(apt.to_dict()), 201


@app.route('/api/apartments/<apt_id>', methods=['GET'])
def get_apartment(apt_id):
    with _Session() as session:
        apt = session.get(Apartment, apt_id)
        if apt is None:
            return jsonify({'error': 'Non trovato'}), 404
        return jsonify(apt.to_dict(include_credentials=True))


@app.route('/api/apartments/<apt_id>', methods=['PUT'])
def update_apartment(apt_id):
    data = request.json
    _api_cache.pop(apt_id, None)
    with _Session() as session:
        apt = session.get(Apartment, apt_id)
        if apt is None:
            return jsonify({'error': 'Non trovato'}), 404
        for field in ('name', 'aw_user', 'aw_password', 'aw_ws_key'):
            if data.get(field):
                setattr(apt, field, data[field])
        for field in ('cin', 'cir', 'comune', 'indirizzo'):
            if field in data:
                setattr(apt, field, data[field] or None)
        if 'ross_codice' in data:
            apt.ross_codice = data['ross_codice'] or None
        if 'ross_camere' in data:
            apt.ross_camere = int(data['ross_camere']) if data['ross_camere'] else None
        if 'ross_letti' in data:
            apt.ross_letti = int(data['ross_letti']) if data['ross_letti'] else None
        session.commit()
        return jsonify(apt.to_dict())


@app.route('/api/apartments/<apt_id>', methods=['DELETE'])
def delete_apartment(apt_id):
    _api_cache.pop(apt_id, None)
    with _Session() as session:
        apt = session.get(Apartment, apt_id)
        if apt is None:
            return jsonify({'error': 'Non trovato'}), 404
        session.delete(apt)
        session.commit()
        return jsonify({'ok': True})


@app.route('/api/apartments/test-credentials', methods=['POST'])
def test_credentials():
    data = request.json
    try:
        api = AlloggiatiWebApi(data['aw_user'], data['aw_password'], data['aw_ws_key'])
        result = api.authentication_test()
        return jsonify({'ok': result.success, 'error': result.err_desc if not result.success else None})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 200


# ── routes: MRZ scan ──────────────────────────────────────────────────────────

@app.route('/api/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'Nessun file ricevuto'}), 400

    file = request.files['image']
    suffix = os.path.splitext(file.filename)[1] or '.jpg'

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        mrz = MrzReader.read_mrz_from_image(tmp_path)
    finally:
        os.unlink(tmp_path)

    if mrz is None:
        return jsonify({'success': False, 'error': 'Nessun MRZ rilevato nel documento'})

    d = mrz.to_dict()
    nationality_icao = d.get('nationality', '').strip('<').strip()
    country_icao = d.get('country', '').strip('<').strip()
    is_italian_born = (country_icao == 'ITA')

    citizenship_code = table_service.get_country_by_icao(nationality_icao) or ''
    birth_country_code = table_service.get_country_by_icao(country_icao) or ''
    citizenship_entry = table_service.get_country_by_code(citizenship_code)
    birth_country_entry = table_service.get_country_by_code(birth_country_code)

    from registration.utils.guest_mapper import _parse_mrz_date, _MRZ_TYPE_TO_DOC_CODE
    mrz_type = d.get('type', 'P')
    doc_type_char = mrz_type[0].upper() if mrz_type else 'P'
    doc_type_code = _MRZ_TYPE_TO_DOC_CODE.get(doc_type_char, 'PASOR')

    return jsonify({
        'success': True,
        'data': {
            'last_name': d.get('surname', '').replace('<', ' ').strip(),
            'first_name': d.get('names', '').replace('<', ' ').strip(),
            'gender': d.get('sex', 'X').replace('<', 'X'),
            'birth_date': _parse_mrz_date(d.get('date_of_birth', '')),
            'is_italian_born': is_italian_born,
            'birth_country_code': birth_country_code,
            'birth_country_name': birth_country_entry[1] if birth_country_entry else '',
            'citizenship_code': citizenship_code,
            'citizenship_name': citizenship_entry[1] if citizenship_entry else '',
            'document_type': doc_type_code,
            'document_number': d.get('number', '').strip('<').strip(),
        }
    })


# ── routes: registration ──────────────────────────────────────────────────────

@app.route('/api/ricevuta')
def ricevuta():
    apartment_id = request.args.get('apartment_id')
    if not apartment_id:
        return jsonify({'error': 'apartment_id obbligatorio'}), 400

    date_str = request.args.get('date')
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
    except ValueError:
        return jsonify({'error': 'Formato data non valido (usa YYYY-MM-DD)'}), 400

    try:
        api = _get_api(apartment_id)
        result = api.ricevuta(dt)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    if not result.success:
        return jsonify({'error': f"{result.err_desc} ({result.err_code})"}), 404

    pdf_bytes = base64.b64decode(result.data['PDF'])
    filename = f"ricevuta_{dt.strftime('%Y-%m-%d')}.pdf"
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@app.route('/api/guests/send', methods=['POST'])
def send_guests():
    return _submit(test=False)


@app.route('/api/guests/test', methods=['POST'])
def test_guests():
    return _submit(test=True)


def _submit(test: bool):
    data = request.json
    if not data or 'guests' not in data:
        return jsonify({'success': False, 'error': 'Payload non valido'}), 400

    apartment_id = data.get('apartment_id')
    if not apartment_id:
        return jsonify({'success': False, 'error': 'apartment_id obbligatorio'}), 400

    try:
        api = _get_api(apartment_id)
        service = RegistrationService(api)
        guests = [_dict_to_guest(g) for g in data['guests']]
        result = service.test_guests(guests) if test else service.send_guests(guests)
        schedine = result.data or {}
        return jsonify({
            'success': result.success,
            'err_code': result.err_code,
            'err_desc': result.err_desc,
            'err_detail': result.err_detail,
            'schedine_valide': schedine.get('schedine_valide', 0),
            'dettaglio': schedine.get('dettaglio', []),
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 422
    except Exception as e:
        logging.exception("Errore durante l'invio")
        return jsonify({'success': False, 'error': str(e)}), 500


def _dict_to_guest(g: dict) -> Guest:
    guest_type = _GUEST_TYPE_MAP.get(str(g['guest_type']), GuestType.SINGLE)
    gender = _GENDER_MAP.get(g.get('gender', 'X'), GuestGender.UNKNOWN)
    arrival = datetime.strptime(g['arrival_date'], '%Y-%m-%d')

    is_italian_born = g.get('is_italian_born', False)
    if is_italian_born:
        birth_city = g.get('birth_city_code', '')
        birth_province = g.get('birth_province', '')
    else:
        birth_city = g.get('birth_country_code', '')
        birth_province = ''

    return Guest(
        guest_type=guest_type,
        arrival_date=arrival,
        num_days=int(g['num_days']),
        last_name=g.get('last_name', '').upper(),
        first_name=g.get('first_name', '').upper(),
        gender=gender,
        birth_date=g.get('birth_date', ''),
        birth_city=birth_city,
        birth_province=birth_province,
        birth_country=g.get('birth_country_code', ''),
        citizenship=g.get('citizenship_code', ''),
        document_type=g.get('document_type', ''),
        document_number=g.get('document_number', ''),
        document_issue_place=g.get('issue_place_code', ''),
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
