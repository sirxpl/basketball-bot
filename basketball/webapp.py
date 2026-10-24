"""Public status/NBA pages and a private Discord OAuth2 identity dashboard."""
from datetime import timedelta
import hmac
import secrets
import time

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

from basketball.oauth import DiscordOAuthClient, OAuthError, OAuthSettings
from basketball.schedule import ScheduleService


def create_app(registry, schedule=None, *, oauth_settings=None, oauth_client=None):
    app = Flask(__name__)
    schedule = schedule if schedule is not None else ScheduleService(registry)
    settings = oauth_settings if oauth_settings is not None else OAuthSettings.from_env()
    oauth = oauth_client if oauth_client is not None else DiscordOAuthClient(settings)
    login_enabled = settings.enabled
    if login_enabled:
        app.secret_key = settings.session_secret
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        # Local HTTP OAuth callbacks need a non-Secure cookie; production HTTPS
        # redirects always use a Secure, HTTP-only session cookie.
        SESSION_COOKIE_SECURE=not settings.redirect_uri.startswith(
            ("http://localhost:", "http://127.0.0.1:")
        ),
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    def signed_in():
        if not login_enabled:
            return None
        user = session.get("discord_user")
        if not isinstance(user, dict) or not isinstance(user.get("id"), str):
            return None
        issued_at = session.get("signed_in_at", 0)
        if not isinstance(issued_at, (int, float)) or time.time() - issued_at > 12 * 3600:
            session.clear()
            return None
        return user

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' https://cdn.discordapp.com data:; "
            "style-src 'self'; script-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        )
        return response

    @app.get("/")
    def home():
        return render_template(
            "index.html", login_enabled=login_enabled, signed_in=bool(signed_in())
        )

    @app.get("/api/status")
    def api_status():
        return jsonify(registry.snapshot())

    @app.get("/api/schedule")
    def api_schedule():
        # Intentional public read-only route: usable even if Discord OAuth is rate-limited.
        return jsonify(schedule.snapshot())

    @app.get("/health")
    def health():
        # Website liveness only; not Discord gateway readiness.
        return jsonify({"status": "ok", "service": "status-website"})

    @app.get("/login")
    def login():
        if not login_enabled:
            return render_template("auth_problem.html",
                title="Discord sign-in is not configured",
                explanation="Add Discord OAuth2 variables in Render to enable the private dashboard."), 503
        if signed_in():
            return redirect(url_for("dashboard"))
        session.clear()
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        session["oauth_started"] = time.time()
        session.permanent = True
        return redirect(oauth.authorize_url(state), code=302)

    @app.get("/oauth/callback")
    def callback():
        if not login_enabled:
            abort(404)
        supplied_state = request.args.get("state", "")
        expected_state = session.pop("oauth_state", "")
        started = session.pop("oauth_started", 0)
        fresh = isinstance(started, (int, float)) and 0 <= time.time() - started <= 600
        if not (isinstance(expected_state, str) and expected_state
                and isinstance(supplied_state, str)
                and hmac.compare_digest(supplied_state, expected_state)
                and fresh):
            session.clear()
            return render_template("auth_problem.html", title="Sign-in session expired",
                                   explanation="Please try logging in again."), 400
        if request.args.get("error"):
            return render_template("auth_problem.html", title="Discord sign-in was cancelled",
                                   explanation="No account was connected. You can try again."), 400
        code = request.args.get("code")
        if not code:
            return render_template("auth_problem.html", title="Missing sign-in response",
                                   explanation="Discord did not return an authorization code."), 400
        try:
            user = oauth.authenticate(code)
        except OAuthError as error:
            return render_template("auth_problem.html", title="Discord login unavailable",
                                   explanation=str(error)), 502
        session.clear()
        session.permanent = True
        session["discord_user"] = user
        session["signed_in_at"] = time.time()
        session["logout_csrf"] = secrets.token_urlsafe(24)
        return redirect(url_for("dashboard"))

    @app.get("/dashboard")
    def dashboard():
        if not login_enabled:
            return render_template("auth_problem.html",
                                   title="Dashboard sign-in is not configured",
                                   explanation="Configure OAuth2 environment variables on Render."), 503
        user = signed_in()
        if not user:
            return redirect(url_for("login"))
        return render_template("dashboard.html", user=user,
                               csrf_token=session["logout_csrf"])

    @app.post("/logout")
    def logout():
        if not login_enabled:
            abort(404)
        token = request.form.get("csrf", "")
        stored = session.get("logout_csrf", "")
        if not stored or not isinstance(token, str) or not hmac.compare_digest(stored, token):
            abort(403)
        session.clear()
        return redirect(url_for("home"), code=303)

    return app
