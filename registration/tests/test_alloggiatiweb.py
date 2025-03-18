from registration.services.alloggiatiweb_api import AlloggiatiWebApi
from registration.models.guest import GuestType, GuestGender, Guest
from datetime import datetime
import json
import os
import unittest

class TestAlloggiatiWeb(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestAlloggiatiWeb, self).__init__(*args, **kwargs)
        this_dir = os.path.dirname(os.path.realpath(__file__))
        credentials_file= os.path.join(this_dir, "resources/alloggiatiweb_credentials.json")
        with open(credentials_file) as f:
            self.credentials = json.load(f)

    def test_auth(self):
        api = AlloggiatiWebApi(self.credentials["user"], self.credentials["password"], self.credentials["ws_key"])
        result = api.authentication_test()
        if not result.success:
            print(result)
        assert result.success == True

    def test_schedine(self):
        api = AlloggiatiWebApi(self.credentials["user"], self.credentials["password"], self.credentials["ws_key"])
        birth_place= api.get_location("ROMA")
        birth_country = api.get_location("ITALIA")

        guest1 = Guest( GuestType.GROUP_LEADER,
                        datetime.now(),
                        3,
                        "Rossi",
                        "Mario",
                        GuestGender.MALE,
                        "01/01/1980",
                        birth_place[0],
                        birth_place[2],
                        birth_country[0],
                        birth_country[0],
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
                        birth_place[0],
                        birth_place[2],
                        birth_country[0],
                        birth_country[0],
                        "","","")
        guests = [guest1, guest2]
        result = api.test_schedine(guests)
        assert result.success == True

    def test_tabella(self):
        api = AlloggiatiWebApi(self.credentials["user"], self.credentials["password"], self.credentials["ws_key"])
        result = api.tabella(AlloggiatiWebApi.TableType.LOCATIONS)
        assert result.success == True

    def test_ricevuta(self):
        api = AlloggiatiWebApi(self.credentials["user"], self.credentials["password"], self.credentials["ws_key"])
        result = api.ricevuta(datetime.now())
        if not result.success:
            print(result)
        assert result.success == True or result.err_code == '51'


if __name__ == '__main__':
    unittest.main()