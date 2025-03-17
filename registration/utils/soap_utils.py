import logging
import requests
import xml.etree.ElementTree as ET

default_headers = {
    'Content-Type': 'application/soap+xml; charset=utf-8'
}

def new_envelope( soap_body: str) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
               <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                                xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                {soap_body}
                </soap12:Envelope>'''

def new_body(soap_body: str) -> str:
    return f'''<soap12:Body>
                {soap_body}
                </soap12:Body>'''

def make_request(url: str, body: str, headers: dict = default_headers) -> ET.Element:
    response = requests.post(url, headers=headers, data=body)
    logging.debug(f"Request: {ET.tostring(ET.fromstring(body), encoding='unicode', method='xml')}")
    if response.status_code != 200:
        raise RuntimeError(f"SOAP request error: {response.status_code} - {response.text}")
    xml_result= ET.fromstring(response.text)
    logging.debug(f"Response: {ET.tostring(xml_result, encoding='unicode', method='xml')}")
    return xml_result

