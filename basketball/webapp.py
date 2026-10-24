"""Public introduction, component status JSON, and independent HTTP liveness."""
from flask import Flask, jsonify, render_template


def create_app(registry):
    app = Flask(__name__)

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/status")
    def api_status():
        return jsonify(registry.snapshot())

    @app.get("/health")
    def health():
        # Always reports website liveness, not Discord readiness.
        # Bot failures should remain visible on the status page.
        return jsonify({"status": "ok", "service": "status-website"})

    return app
