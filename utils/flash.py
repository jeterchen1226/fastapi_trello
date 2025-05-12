import urllib.parse
from starlette.requests import Request
from starlette.responses import Response

def set_flash_message(response: Response, message: str, category: str = "success"):
    encoded_message = urllib.parse.quote(message)
    response.set_cookie(
        key = "flash_message", 
        value = f"{category}:{encoded_message}", 
        max_age = 30, 
        httponly = True,
    )

def get_flash_message(request: Request):
    flash_cookie = request.cookies.get("flash_message")
    if not flash_cookie:
        return None, None
    
    parts = flash_cookie.split(":", 1)
    if len(parts) != 2:
        return None, None
    
    category, encoded_message = parts
    message = urllib.parse.unquote(encoded_message)
    return category, message