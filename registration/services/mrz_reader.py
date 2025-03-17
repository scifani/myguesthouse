import logging
from passporteye import read_mrz

class MrzReader:
    @staticmethod
    def read_mrz_from_image(image_path: str) -> dict:
        logging.info(f"Reading MRZ from image: {image_path}")
        mrz = read_mrz(image_path, save_roi=True)
        logging.info(f"MRZ: {mrz}")
        return mrz