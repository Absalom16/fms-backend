import random
import string
import uuid
from datetime import datetime


def generate_pnr():
    """Generate a 6-character alphanumeric Passenger Name Record code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        pnr = ''.join(random.choices(chars, k=6))
        # Avoid ambiguous characters
        if not any(c in pnr for c in ['0', 'O', '1', 'I']):
            return pnr


def generate_ticket_number():
    """Generate a unique ticket number in TKT-YYYY-XXXXXX format."""
    year = datetime.utcnow().year
    suffix = ''.join(random.choices(string.digits, k=6))
    return f'TKT-{year}-{suffix}'


def generate_barcode():
    """Generate a unique barcode value (UUID-based)."""
    return str(uuid.uuid4()).replace('-', '').upper()


def paginate_query(query, page, per_page, max_per_page=100):
    """Apply pagination to a SQLAlchemy query and return (items, total)."""
    per_page = min(per_page, max_per_page)
    page = max(page, 1)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_client_ip(request):
    """Extract the real client IP, accounting for reverse proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr
