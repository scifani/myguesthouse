from registration.models.guest import Guest, GuestType, GuestGender
from registration.utils import soap_utils
from collections import namedtuple
from datetime import datetime
from enum import Enum
import logging
import xml.etree.ElementTree as ET

"""
Api for AlloggiatiWeb service
Documentation: https://alloggiatiweb.poliziadistato.it/service/Service.asmx
"""
class AlloggiatiWebApi:
    # URL for the service
    _url = 'https://alloggiatiweb.poliziadistato.it/service/service.asmx'

    # Namespace dictionary for parsing
    _namespaces = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'ns': 'AlloggiatiService'
    }

    # Result namedtuple
    Result = namedtuple('Result', ['success', 'err_code', 'err_desc', 'err_detail', 'data'])

    # Token namedtuple
    Token = namedtuple('Token', ['issued', 'expires', 'token'])

    # Location namedtuple
    Location= namedtuple('Location', ['id', 'name', 'province', 'timestamp'])

    # Enum for table types
    class TableType(Enum):
        LOCATIONS = 'Luoghi'
        DOCUMENT_TYPES = 'Tipi_Documento'
        GUEST_TYPES = 'Tipi_Alloggiato'
        ERROR_TYPES = 'TipoErrore'
        APARTMENTS_LIST = 'ListaAppartamenti'


    def __init__(self, user: str, password: str, ws_key: str):
        self._user = user
        self._password = password
        self._ws_key = ws_key
        self._token= self._generate_token()
        self._locations= None


    def authentication_test(self) -> Result:
        logging.info("Requesting 'Authentication_Test' endpoint")
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <Authentication_Test xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <token>{self._token.token}</token>
            </Authentication_Test>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result = self._parse_response(xml_response)
        logging.info(f"'Authentication_Test' result: {result}")
        return result


    def gestione_appartamenti_test(self, apartment_id: int, guests: list) -> Result:
        logging.info("Requesting 'GestioneAppartamenti_Test' endpoint")
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <GestioneAppartamenti_Test xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <token>{self._token.token}</token>
              <ElencoSchedine>
              {"".join([f"<string>{self._create_record(guest)}</string>" for guest in guests])}
              </ElencoSchedine>
              <IdAppartamento>{apartment_id}</IdAppartamento>
            </GestioneAppartamenti_Test>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result = self._parse_response(xml_response)
        logging.info(f"'GestioneAppartamenti_Test' result: {result}")
        return result


    def test_schedine(self, guests: list) -> Result:
        logging.info("Requesting 'Test' endpoint")
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <Test xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <token>{self._token.token}</token>
              <ElencoSchedine>
              {"".join([f"<string>{self._create_record(guest)}</string>" for guest in guests])}
              </ElencoSchedine>
            </Test>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result = self._parse_response(xml_response)
        logging.info(f"'Test' result: {result}")
        return result


    def send_schedine(self, guests: list) -> Result:
        logging.info("Requesting 'Send' endpoint")
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <Send xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <token>{self._token.token}</token>
              <ElencoSchedine>
              {"".join([f"<string>{self._create_record(guest)}</string>" for guest in guests])}
              </ElencoSchedine>
            </Send>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result = self._parse_response(xml_response)
        logging.info(f"'Send' result: {result}")
        return result


    def ricevuta(self, datetime: str) -> Result:
        logging.info(f"Requesting 'Ricevuta' endpoint. datetime: {datetime}")
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <Ricevuta xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <token>{self._token.token}</token>
              <Data>{datetime.isoformat()}</Data>
            </Ricevuta>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result = self._parse_response(xml_response, ['PDF'])
        logging.info(f"'Ricevuta' result: {result}")
        return result


    def tabella(self, table_type: TableType) -> Result:
        logging.info(f"Requesting 'Tabella' endpoint. Table type: {table_type}")
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <Tabella xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <token>{self._token.token}</token>
              <tipo>{table_type.value}</tipo>
            </Tabella>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result = self._parse_response(xml_response, ['CSV'])
        logging.info(f"'Tabella' result: {result}")
        return result


    def get_location(self, location_name: str):
        if self._locations is None:
            result= self.tabella(AlloggiatiWebApi.TableType.LOCATIONS)
            if not result.success:
                raise RuntimeError(f"Error: {result.err_code} - {result.err_desc}")
            csv_records = [x for x in result.data['CSV'].split("\n") if x != ""]
            self._locations= []
            for record in csv_records:
                ss= record.split(";")
                self._locations.append(AlloggiatiWebApi.Location(ss[0], ss[1], ss[2], ss[3]))

        return next((x for x in self._locations if x[1] == location_name), None)


    def _generate_token(self) -> Token:
        soap_envelope = soap_utils.new_envelope(
            soap_utils.new_body(f'''
            <GenerateToken xmlns="AlloggiatiService">
              <Utente>{self._user}</Utente>
              <Password>{self._password}</Password>
              <WsKey>{self._ws_key}</WsKey>
            </GenerateToken>''')
        )
        xml_response= soap_utils.make_request(self._url, soap_envelope)
        result= self._parse_response(xml_response)
        if not result.success:
            raise RuntimeError(f"Error: {result.err_code} - {result.err_desc}")
        token= AlloggiatiWebApi.Token(
            xml_response.find('.//ns:GenerateTokenResult/ns:issued', self._namespaces).text,
            xml_response.find('.//ns:GenerateTokenResult/ns:expires', self._namespaces).text,
            xml_response.find('.//ns:GenerateTokenResult/ns:token', self._namespaces).text)
        logging.debug(f"Token generated: {token}")
        return token


    def _parse_response(self, node: ET.Element, data_fields: list = []) -> Result:
        success = node.find('.//ns:esito', self._namespaces).text == "true"
        err_cod = node.find('.//ns:ErroreCod', self._namespaces).text
        err_des = node.find('.//ns:ErroreDes', self._namespaces).text
        err_det = node.find('.//ns:ErroreDettaglio', self._namespaces).text
        try:
            data= {}
            for field in data_fields:
                data[field] = node.find(f'.//ns:{field}', self._namespaces).text
        except AttributeError:
            data= None
        return AlloggiatiWebApi.Result(success, err_cod, err_des, err_det, data)


    def _create_record(self, guest: Guest) -> str:
        """
        Field                       |Length|Mandatory For 16, 17, 18|Mandatory for 19, 20|Notes
        ----------------------------|------|------------------------|--------------------|------------------
        Tipo Alloggiato             | 2    | Y                      | Y                  | Codice Tabella Tipo Alloggiati
        Data Arrivo                 | 10   | Y                      | Y                  | gg/mm/aaaa
        Numero Giorni di Permanenza | 2    | Y                      | Y                  | Massimo 30 gg
        Cognome                     | 50   | Y                      | Y                  |
        Nome                        | 30   | Y                      | Y                  |
        Sesso                       | 1    | Y                      | Y                  | 1 (M) - 2 (F)
        Data Nascita                | 10   | Y                      | Y                  | gg/mm/aaaa
        Comune Nascita              | 9    | Y (note-1)             | Y                  | Codice Tabella Comuni
        Provincia Nascita           | 2    | Y (note-1)             | Y                  | Sigla Provincia
        Stato Nascita               | 9    | Y                      | Y                  | Codice Tabella Stati
        Cittadinanza                | 9    | Y                      | Y                  | Codice Tabella Stati
        Tipo Documento              | 5    | Y                      | N                  | Codice Tabella Documenti
        Numero Documento            | 20   | Y                      | N                  |
        Luogo Rilascio Documento    | 9    | Y (Stato o Comune)     | N                  | Codice Tabella Stati o Comuni
        """
        record= f"{AlloggiatiWebApi._guest_type_to_int(guest.guest_type):02d}"
        record+= f"{AlloggiatiWebApi._datetime_to_str(guest.arrival_date)}"
        record+= f"{guest.num_days:02d}"
        record+= f"{guest.last_name}" + " "*(50-len(guest.last_name))
        record+= f"{guest.first_name}" + " "*(30-len(guest.first_name))
        record+= f"{AlloggiatiWebApi._guest_gender_to_str(guest.gender)}"
        record+= f"{guest.birth_date}" + "0"*(10-len(guest.birth_date))
        record+= f"{guest.birth_city}" + " "*(9-len(guest.birth_city))
        record+= f"{guest.birth_province}" + " "*(2-len(guest.birth_province))
        record+= f"{guest.birth_country}" + " "*(9-len(guest.birth_country))
        record+= f"{guest.citizenship}" + " "*(9-len(guest.citizenship))
        record+= f"{guest.document_type}" + " "*(5-len(guest.document_type))
        record+= f"{guest.document_number}" + " "*(20-len(guest.document_number))
        record+= f"{guest.document_issue_place}" + " "*(9-len(guest.document_issue_place))
        return record


    @staticmethod
    def _guest_type_to_int(guest_type: GuestType) -> int:
        return {
            GuestType.SINGLE: 16,
            GuestType.HOUSE_HEAD: 17,
            GuestType.GROUP_LEADER: 18,
            GuestType.FAMILY_MEMBER: 19,
            GuestType.GROUP_MEMBER: 20
        }[guest_type]

    @staticmethod
    def _guest_gender_to_str(gender: GuestGender) -> str:
        return {
            GuestGender.MALE: "1",
            GuestGender.FEMALE: "2",
            GuestGender.UNKNOWN: "X"
        }[gender]

    @staticmethod
    def _datetime_to_str(dt: datetime) -> str:
        return dt.strftime("%d/%m/%Y")