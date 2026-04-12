from slowapi import Limiter
from slowapi.util import get_remote_address

# We use the remote IP address to identify users
limiter = Limiter(key_func=get_remote_address)