from flask import Blueprint, render_template

from registration.models import Apartment
from web.db import Session

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    with Session() as session:
        apartments = [
            a.to_dict()
            for a in session.query(Apartment).order_by(Apartment.name).all()
        ]
    return render_template('public/index.html', apartments=apartments)
