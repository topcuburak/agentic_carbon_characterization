"""
Local mock API server for the http_request tool.
Serves pre-defined REST endpoints with synthetic data for reproducible benchmarking.
Run standalone: python -m tools.mock_api_server
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import MOCK_API_HOST, MOCK_API_PORT

# ─── Synthetic Data ──────────────────────────────────────────────────────────

PRODUCTS = [
    {"id": 1, "name": "Laptop Pro 15", "category": "electronics", "price": 1299.99, "stock": 45},
    {"id": 2, "name": "Wireless Mouse", "category": "electronics", "price": 29.99, "stock": 200},
    {"id": 3, "name": "USB-C Hub", "category": "electronics", "price": 49.99, "stock": 150},
    {"id": 4, "name": "Standing Desk", "category": "furniture", "price": 599.00, "stock": 30},
    {"id": 5, "name": "Ergonomic Chair", "category": "furniture", "price": 449.00, "stock": 25},
    {"id": 6, "name": "Monitor 27in 4K", "category": "electronics", "price": 399.99, "stock": 60},
    {"id": 7, "name": "Mechanical Keyboard", "category": "electronics", "price": 89.99, "stock": 120},
    {"id": 8, "name": "Desk Lamp LED", "category": "furniture", "price": 39.99, "stock": 80},
    {"id": 9, "name": "Webcam HD", "category": "electronics", "price": 69.99, "stock": 90},
    {"id": 10, "name": "Noise Cancelling Headphones", "category": "electronics", "price": 249.99, "stock": 55},
]

USERS = [
    {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "active": True},
    {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user", "active": True},
    {"id": 3, "name": "Carol Williams", "email": "carol@example.com", "role": "user", "active": False},
    {"id": 4, "name": "Dave Brown", "email": "dave@example.com", "role": "manager", "active": True},
    {"id": 5, "name": "Eve Davis", "email": "eve@example.com", "role": "user", "active": True},
]

WEATHER = [
    {"city": "New York", "temperature_f": 72, "humidity": 65, "condition": "Partly Cloudy"},
    {"city": "San Francisco", "temperature_f": 61, "humidity": 78, "condition": "Foggy"},
    {"city": "Chicago", "temperature_f": 68, "humidity": 55, "condition": "Sunny"},
    {"city": "Miami", "temperature_f": 85, "humidity": 80, "condition": "Thunderstorms"},
    {"city": "Seattle", "temperature_f": 58, "humidity": 72, "condition": "Rainy"},
]

ORDERS = [
    {"id": 1, "user_id": 1, "product_id": 1, "quantity": 1, "total": 1299.99, "status": "delivered"},
    {"id": 2, "user_id": 2, "product_id": 2, "quantity": 2, "total": 59.98, "status": "shipped"},
    {"id": 3, "user_id": 1, "product_id": 6, "quantity": 1, "total": 399.99, "status": "processing"},
    {"id": 4, "user_id": 3, "product_id": 5, "quantity": 1, "total": 449.00, "status": "delivered"},
    {"id": 5, "user_id": 4, "product_id": 10, "quantity": 1, "total": 249.99, "status": "shipped"},
    {"id": 6, "user_id": 2, "product_id": 7, "quantity": 1, "total": 89.99, "status": "delivered"},
    {"id": 7, "user_id": 5, "product_id": 3, "quantity": 3, "total": 149.97, "status": "processing"},
    {"id": 8, "user_id": 4, "product_id": 4, "quantity": 1, "total": 599.00, "status": "delivered"},
]

# ─── Route Handling ──────────────────────────────────────────────────────────

ROUTES = {
    "/api/products": PRODUCTS,
    "/api/users": USERS,
    "/api/weather": WEATHER,
    "/api/orders": ORDERS,
}


class MockAPIHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the mock API."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _parse_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            body = self.rfile.read(length).decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return body
        return None

    def _route(self, method):
        path = self.path.split("?")[0].rstrip("/")

        # Check for item-level routes like /api/products/1
        parts = path.rsplit("/", 1)
        if len(parts) == 2 and parts[0] in ROUTES:
            collection_path, item_id = parts
            try:
                item_id = int(item_id)
            except ValueError:
                self._send_json({"error": "Invalid ID"}, 400)
                return

            collection = ROUTES[collection_path]
            item = next((x for x in collection if x.get("id") == item_id), None)
            if item is None:
                self._send_json({"error": "Not found"}, 404)
                return
            self._send_json(item)
            return

        # Collection-level routes
        if path in ROUTES:
            if method == "GET":
                # Support query filtering: /api/products?category=electronics
                query = ""
                if "?" in self.path:
                    query = self.path.split("?", 1)[1]
                data = ROUTES[path]
                if query:
                    for param in query.split("&"):
                        if "=" in param:
                            key, val = param.split("=", 1)
                            data = [d for d in data if str(d.get(key, "")).lower() == val.lower()]
                self._send_json(data)
            elif method == "POST":
                body = self._parse_body()
                self._send_json({"message": "Created", "data": body}, 201)
            else:
                self._send_json({"error": f"Method {method} not supported"}, 405)
            return

        # Health check
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return

        self._send_json({"error": "Not found", "available_endpoints": list(ROUTES.keys())}, 404)

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PUT(self):
        self._route("PUT")

    def do_DELETE(self):
        self._route("DELETE")


def start_mock_server(host=None, port=None, background=True) -> HTTPServer | None:
    """Start the mock API server. If background=True, runs in a daemon thread."""
    host = host or MOCK_API_HOST
    port = port or MOCK_API_PORT
    server = HTTPServer((host, port), MockAPIHandler)

    if background:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
    else:
        print(f"Mock API server running on http://{host}:{port}")
        server.serve_forever()
        return None


def stop_mock_server(server: HTTPServer):
    """Shut down the mock API server."""
    server.shutdown()


if __name__ == "__main__":
    start_mock_server(background=False)
