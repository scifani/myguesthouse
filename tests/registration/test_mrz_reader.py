from registration.services.mrz_reader import MrzReader

def test_read_mrz_from_image(images: list):
    for image_path in images:
      mrz = MrzReader.read_mrz_from_image(image_path)
      assert mrz is not None

def test_service( mrz_images):
    test_read_mrz_from_image(mrz_images)