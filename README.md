# MyGuestHouse
MyGuestHouse aims to be a modular application to help managing a guest house with one or even more apartments.<br>
The project is written in Python and has the following structure:
```
myguesthouse/
│
├── core/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py          # Base SQLAlchemy configuration
│   ├── services/
│   │   ├── __init__.py
│   │   └── database.py      # Common database service
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # Common configuration
│   └── exceptions/
│       ├── __init__.py
│       └── error_handlers.py
│
├── reservation/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── apartment.py
│   │   └── reservation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── apartment_service.py
│   │   └── reservation_service.py
│   └── utils/
│       ├── __init__.py
│       └── availability_calculator.py
│
├── registration/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── guest.py         # Guest personal information
│   │   └── document.py      # ID documents, passports, etc.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── guest_service.py
│   │   └── police_reporting_service.py  # Interface with police systems
│   └── utils/
│       ├── __init__.py
│       └── document_validator.py        # Validate IDs, passports
│
├── accounting/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── invoice.py
│   │   ├── payment.py
│   │   └── expense.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── invoice_service.py
│   │   ├── payment_service.py
│   │   └── reporting_service.py         # Financial reports
│   └── utils/
│       ├── __init__.py
│       └── tax_calculator.py
│
├── api/                     # Optional: API layer if needed
│   ├── __init__.py
│   ├── reservation_api.py
│   ├── registration_api.py
│   └── accounting_api.py
│
├── tests/
│   ├── __init__.py
│   ├── reservation/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── registration/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   └── test_services.py
│   └── accounting/
│       ├── __init__.py
│       ├── test_models.py
│       └── test_services.py
│
├── requirements.txt
├── setup.py
└── README.md
```











 https://helpcenter.avaibook.com/it/articles/6115771-come-posso-ottenere-la-web-key-sul-portale-alloggiati