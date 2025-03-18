from registration.services.mrz_reader import MrzReader
import os
import unittest

class TestMrzReader(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    super(TestMrzReader, self).__init__(*args, **kwargs)
    this_dir = os.path.dirname(os.path.realpath(__file__))
    self.images_dir= os.path.join(this_dir, "resources")

  def test_read_mrz_from_image(self):
    images = [os.path.join(self.images_dir, "passport1.jpg"),
              os.path.join(self.images_dir, "passport2.jpg"),
              os.path.join(self.images_dir, "passport3.jpg")]
    for image_path in images:
      mrz = MrzReader.read_mrz_from_image(image_path)
      assert mrz is not None