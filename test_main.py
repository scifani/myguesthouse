import logging
import os
from tests.registration import test_alloggiatiweb
from tests.registration import test_mrz_reader

logging.basicConfig(level=logging.DEBUG)

this_script_dir = os.path.dirname(os.path.abspath(__file__))
resources_dir = os.path.join(this_script_dir, "resources")

# Test AlloggiatiWeb Api
alloggiatiweb_credentials_file = os.path.join(resources_dir, "alloggiatiweb_credentials.json")
test_alloggiatiweb.test_service( alloggiatiweb_credentials_file)

# Test MRZ Reader
images = [os.path.join(resources_dir, "passport1.jpg"),
          os.path.join(resources_dir, "passport2.jpg"),
          os.path.join(resources_dir, "passport3.jpg")]
test_mrz_reader.test_read_mrz_from_image(images)