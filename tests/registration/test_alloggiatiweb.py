from registration.services.alloggiatiweb_api import AlloggiatiWebApi
from registration.models.guest import GuestType, GuestGender, Guest
from datetime import datetime
import json

def test_auth( credentials: dict):
    api = AlloggiatiWebApi(credentials["user"], credentials["password"], credentials["ws_key"])
    result = api.authentication_test()
    assert result.success == True

def test_schedine( credentials: dict):
    guest1 = Guest( GuestType.GROUP_LEADER,
                    datetime.now(),
                    3,
                    "Rossi",
                    "Mario",
                    GuestGender.MALE,
                    "01/01/1980",
                    "412058091",
                    "RM",
                    "100000100",
                    "100000100",
                    "IDELE",
                    "CA91673EW",
                    "412058091")
    guest2 = Guest( GuestType.GROUP_MEMBER,
                    datetime.now(),
                    3,
                    "Rossi",
                    "Maria",
                    GuestGender.FEMALE,
                    "01/01/1980",
                    "412058091",
                    "RM",
                    "100000100",
                    "100000100",
                    "","","")
    guests = [guest1, guest2]
    api = AlloggiatiWebApi(credentials["user"], credentials["password"], credentials["ws_key"])
    result = api.test_schedine(guests)
    assert result.success == True

def test_tabella( credentials: dict):
    api = AlloggiatiWebApi(credentials["user"], credentials["password"], credentials["ws_key"])
    result = api.tabella(AlloggiatiWebApi.TableType.LOCATIONS)
    assert result.success == True

def test_service( alloggiatiweb_credentials_file):
    with open(alloggiatiweb_credentials_file) as f:
        credentials = json.load(f)
    test_auth(credentials)
    test_schedine(credentials)
    test_tabella(credentials)