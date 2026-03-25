"""
package_installer.py
--------------------
Nœud LangGraph `installer` : installe les packages requis avant la génération
du code Streamlit.

Logique :
  1. Lit la liste `required_packages` identifiée par le nœud `analyzer`.
  2. Si repo_config indique un dépôt privé (enabled=true), construit la
     commande pip avec --index-url ou --extra-index-url vers Artifactory/Nexus.
  3. Sinon, installe depuis PyPI.
  4. Ajoute toujours les packages de `extra_packages` définis dans repo_config.
  5. Logue le résultat et met à jour l'état avec un rapport d'installation.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_REPO_CONFIG_PATH = Path(__file__).parent / "repo_config.yaml"


# ---------------------------------------------------------------------------
# Chargement de la configuration dépôt
# ---------------------------------------------------------------------------

def load_repo_config(config_path: str | Path = DEFAULT_REPO_CONFIG_PATH) -> dict[str, Any]:
    """Charge repo_config.yaml. Retourne un dict vide si le fichier est absent."""
    path = Path(config_path)
    if not path.exists():
        logger.info("[installer] repo_config.yaml absent — installation PyPI uniquement")
        return {}

    with path.open(encoding="utf-8") as f:
        cfg: dict = yaml.safe_load(f) or {}

    logger.info("[installer] repo_config.yaml chargé")
    return cfg


# ---------------------------------------------------------------------------
# Construction de la commande pip
# ---------------------------------------------------------------------------

def _build_pip_command(
    packages: list[str],
    repo_cfg: dict[str, Any],
) -> list[str]:
    """
    Construit la commande pip install adaptée à la config du dépôt.

    Paramètres
    ----------
    packages    : liste des noms de packages à installer
    repo_cfg    : contenu de repo_config.yaml

    Retourne
    --------
    list[str]
        Commande shell complète sous forme de liste (pour subprocess).
    """
    if not packages:
        return []

    cmd = [sys.executable, "-m", "pip", "install", "--quiet"]

    private = repo_cfg.get("private_repo", {})
    enabled: bool = private.get("enabled", False)

    if enabled:
        index_url: str = private.get("index_url", "")
        fallback: bool = private.get("fallback_to_pypi", True)
        auth_method: str = private.get("auth", {}).get("method", "env")
        verify_ssl: bool = private.get("verify_ssl", True)
        ca_bundle: str = private.get("ca_bundle", "")
        extra_opts: list[str] = private.get("extra_pip_options", [])

        # ── Authentification ──────────────────────────────────────────────
        authed_url = _inject_auth(index_url, private.get("auth", {}), auth_method)

        # ── Index URL ─────────────────────────────────────────────────────
        if fallback:
            cmd += ["--extra-index-url", authed_url]
        else:
            cmd += ["--index-url", authed_url]

        # ── SSL ───────────────────────────────────────────────────────────
        if not verify_ssl:
            cmd.append("--trusted-host")
            cmd.append(_extract_host(index_url))
        elif ca_bundle:
            cmd += ["--cert", ca_bundle]

        # ── Options supplémentaires ───────────────────────────────────────
        cmd.extend(extra_opts)

        logger.info(
            "[installer] Dépôt privé activé : %s (fallback PyPI=%s)",
            _mask_url(authed_url),
            fallback,
        )
    else:
        logger.info("[installer] Installation depuis PyPI public")

    cmd.extend(packages)
    return cmd


def _inject_auth(url: str, auth_cfg: dict, method: str) -> str:
    """Insère les credentials dans l'URL si la méthode le requiert."""
    if method == "env":
        username = os.environ.get(auth_cfg.get("username_env", ""), "")
        password = os.environ.get(auth_cfg.get("password_env", ""), "")
        if username and password:
            proto, rest = url.split("://", 1)
            return f"{proto}://{username}:{password}@{rest}"
        else:
            logger.warning(
                "[installer] Credentials env non trouvés (%s / %s) — tentative sans auth",
                auth_cfg.get("username_env"),
                auth_cfg.get("password_env"),
            )

    elif method == "basic":
        username = auth_cfg.get("username", "")
        password = auth_cfg.get("password", "")
        if username and password:
            proto, rest = url.split("://", 1)
            return f"{proto}://{username}:{password}@{rest}"

    elif method == "token":
        # Artifactory accepte token comme password avec utilisateur vide
        token = auth_cfg.get("token", "")
        if token:
            proto, rest = url.split("://", 1)
            return f"{proto}://token:{token}@{rest}"

    return url


def _extract_host(url: str) -> str:
    """Extrait l'hostname d'une URL pour --trusted-host."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).hostname or url
    except Exception:
        return url


def _mask_url(url: str) -> str:
    """Masque les credentials dans une URL pour les logs."""
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(url)
        masked = p._replace(netloc=f"***:***@{p.hostname}" if p.password else p.netloc)
        return urlunparse(masked)
    except Exception:
        return "<url masquée>"


# ---------------------------------------------------------------------------
# Nœud LangGraph : installer
# ---------------------------------------------------------------------------

def installer(state: dict[str, Any]) -> dict[str, Any]:
    """
    Nœud LangGraph qui installe les packages nécessaires avant la génération
    du code Streamlit.

    Comportement :
    - Si aucun package requis → skip silencieux
    - Sinon → pip install avec la config dépôt appropriée
    - Le résultat (succès/échec) est loggé et stocké dans l'état

    Paramètres
    ----------
    state : FrontendState

    Retourne
    --------
    dict
        Champ `installation_report` ajouté à l'état.
    """
    from langchain_core.messages import AIMessage
    import re

    repo_cfg: dict = state.get("repo_config", {})

    # Fusion des packages requis + extra_packages de la config
    required: list[str] = list(state.get("required_packages", []))
    extra: list[str] = repo_cfg.get("extra_packages", [])
    private_pkgs: list[str] = repo_cfg.get("private_packages", [])

    all_packages = _deduplicate([*required, *extra, *private_pkgs])
    
    # Filtrer les entrées invalides (en-têtes, texte descriptif, etc.)
    valid_packages = []
    for pkg in all_packages:
        pkg_clean = pkg.strip()
        # Valider que c'est un vrai package (alphanumérique, tiret, point, crochet, opérateurs de version)
        if pkg_clean and re.match(r'^[a-zA-Z0-9\-._\[\]><=~!]+$', pkg_clean):
            valid_packages.append(pkg_clean)
        else:
            logger.warning("[installer] Package invalide ignoré : %s", pkg)
    
    if not valid_packages:
        logger.info("[installer] Aucun package supplémentaire à installer — skip")
        return {
            "messages": [AIMessage(content="[installer] Aucun package à installer.", name="installer")],
            "installation_report": "Aucune installation requise.",
        }

    logger.info("[installer] Packages à installer : %s", valid_packages)
    cmd = _build_pip_command(valid_packages, repo_cfg)

    report_lines: list[str] = [f"Packages installés : {', '.join(valid_packages)}"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,   # 2 minutes max
        )

        if result.returncode == 0:
            logger.info("[installer] ✔ Installation réussie")
            report_lines.append("Statut : ✔ Succès")
            if result.stdout.strip():
                report_lines.append(f"Sortie pip :\n{result.stdout.strip()[:500]}")
        else:
            logger.error("[installer] ✘ Échec pip (code %d)", result.returncode)
            report_lines.append(f"Statut : ✘ Échec (code retour {result.returncode})")
            if result.stderr.strip():
                report_lines.append(f"Erreur pip :\n{result.stderr.strip()[:500]}")

    except subprocess.TimeoutExpired:
        logger.error("[installer] Timeout dépassé (120s)")
        report_lines.append("Statut : ✘ Timeout (120s dépassé)")

    except Exception as exc:
        logger.exception("[installer] Erreur inattendue")
        report_lines.append(f"Statut : ✘ Erreur — {exc}")

    report = "\n".join(report_lines)

    return {
        "messages": [AIMessage(content=report, name="installer")],
        "installation_report": report,
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _deduplicate(packages: list[str]) -> list[str]:
    """Déduplique en préservant l'ordre et en normalisant les noms."""
    seen: set[str] = set()
    result: list[str] = []
    for pkg in packages:
        key = pkg.split(">=")[0].split("==")[0].split("[")[0].strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(pkg)
    return result
