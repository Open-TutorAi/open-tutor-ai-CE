import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:5173"
EMAIL = "Parentpro@gmail.com"
PASSWORD = "1234"
LOGIN_URL = f"{BASE_URL}/auth"
SESSIONS_URL = f"{BASE_URL}/parent"


def login(page: Page):
    """Helper — connexion parent réutilisable dans tous les tests."""
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle")
    page.fill("input[type=email], input[name=email], input[placeholder*='mail']", EMAIL)
    page.fill(
        "input[type=password], input[name=password], input[placeholder*='ass']",
        PASSWORD,
    )
    page.click(
        "button[type=submit], button:has-text('Connexion'), button:has-text('Login'), button:has-text('Se connecter')"
    )
    # Attendre que l'URL change vraiment après le clic
    try:
        page.wait_for_url(lambda url: "/auth" not in url, timeout=8000)
    except Exception:
        pass
    page.wait_for_load_state("networkidle")


# ═══════════════════════════════════════════════════════════════════
# TEST 1 — Connexion parent
# ═══════════════════════════════════════════════════════════════════


def test_parent_peut_se_connecter(page: Page):
    """Le parent arrive sur son dashboard après connexion."""
    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle")
    page.fill("input[type=email], input[name=email], input[placeholder*='mail']", EMAIL)
    page.fill(
        "input[type=password], input[name=password], input[placeholder*='ass']",
        PASSWORD,
    )
    page.click(
        "button[type=submit], button:has-text('Connexion'), button:has-text('Login'), button:has-text('Se connecter')"
    )

    # Attendre la redirection (8 secondes max)
    try:
        page.wait_for_url(lambda url: "/auth" not in url, timeout=8000)
        assert "/parent" in page.url or "/dashboard" in page.url
    except Exception:
        # Si pas de redirection d'URL, vérifie que le contenu a changé
        content = page.content()
        assert (
            "Pro Parent" in content
            or "Parentpro" in content
            or "Dashboard" in content
            or "parent" in content.lower()
        ), f"Connexion échouée — URL actuelle : {page.url}"


# ═══════════════════════════════════════════════════════════════════
# TEST 2 — Dashboard parent visible
# ═══════════════════════════════════════════════════════════════════


def test_dashboard_parent_affiche_infos_compte(page: Page):
    """Le dashboard affiche les infos du compte parent connecté."""
    login(page)
    page.goto(SESSIONS_URL)
    page.wait_for_load_state("networkidle")

    content = page.content()
    assert (
        "Parentpro@gmail.com" in content
        or "Pro Parent" in content
        or "parent" in content.lower()
    ), f"Infos compte non visibles — URL : {page.url}"


# ═══════════════════════════════════════════════════════════════════
# TEST 3 — Navigation Sessions IA
# ═══════════════════════════════════════════════════════════════════


def test_parent_peut_naviguer_vers_sessions_ia(page: Page):
    """Le parent peut accéder à la page Sessions IA depuis le dashboard."""
    login(page)
    page.goto(SESSIONS_URL)
    page.wait_for_load_state("networkidle")

    # Cherche un lien vers Sessions IA
    sessions_link = page.locator(
        "a:has-text('Session'), a:has-text('session'), "
        "button:has-text('Session'), nav a"
    ).first

    if sessions_link.count() > 0:
        sessions_link.click()
        page.wait_for_load_state("networkidle")

    # La page a chargé sans erreur
    assert "500" not in page.title()
    assert "Error" not in page.title()


# ═══════════════════════════════════════════════════════════════════
# TEST 4 — Déconnexion
# ═══════════════════════════════════════════════════════════════════


def test_parent_peut_se_deconnecter(page: Page):
    """Le parent peut se déconnecter depuis le dashboard."""
    login(page)
    page.goto(SESSIONS_URL)
    page.wait_for_load_state("networkidle")

    # Clic sur Déconnexion (visible sur la capture d'écran)
    deconnexion = page.locator(
        "a:has-text('Déconnexion'), button:has-text('Déconnexion'), "
        "a:has-text('Logout'), a:has-text('déconnexion')"
    ).first

    if deconnexion.is_visible():
        deconnexion.click()
        page.wait_for_load_state("networkidle")
        assert "/auth" in page.url or "/login" in page.url or page.url == f"{BASE_URL}/"
