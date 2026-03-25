"""
package_installer.py
--------------------
Installation des packages Python générés dans requirements.txt après
la génération du code backend.

Logique :
  1. Lit le fichier requirements.txt généré
  2. Extrait la liste des packages
  3. Installe via pip dans l'environnement courant
  4. Logue le résultat (succès/échec)
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def parse_requirements(requirements_content: str) -> list[str]:
    """
    Parse le contenu d'un requirements.txt et extrait les packages valides.
    
    Args:
        requirements_content: Contenu du fichier requirements.txt
        
    Returns:
        Liste des packages valides (package>=version)
    """
    packages = []
    for line in requirements_content.strip().split('\n'):
        line = line.strip()
        # Ignorer les lignes vides et les commentaires
        if not line or line.startswith('#'):
            continue
        # Valider que c'est un package (alphanumérique, tiret, point, crochet, opérateurs)
        if any(c.isalnum() or c in '-._[]><=~!' for c in line):
            packages.append(line)
    return packages


def install_packages(packages: list[str], project_path: Optional[str] = None) -> dict:
    """
    Installe une liste de packages via pip.
    
    Args:
        packages: Liste des packages à installer (avec versions)
        project_path: Chemin du projet (optionnel, pour les logs)
        
    Returns:
        dict avec 'success' (bool), 'output' (str), 'error' (str)
    """
    if not packages:
        logger.info("[backend_installer] Aucun package à installer")
        return {
            "success": True,
            "output": "Aucun package à installer",
            "error": "",
        }
    
    logger.info(f"[backend_installer] Installation de {len(packages)} packages...")
    
    cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + packages
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes max pour l'installation
            cwd=project_path,
        )
        
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""
        
        if result.returncode == 0:
            logger.info(f"[backend_installer] ✔ Installation réussie ({len(packages)} packages)")
            return {
                "success": True,
                "output": output or f"Installation de {len(packages)} packages réussie",
                "error": "",
            }
        else:
            logger.error(f"[backend_installer] ✘ Échec pip (code {result.returncode})")
            return {
                "success": False,
                "output": output,
                "error": error or f"Pip a échoué avec le code {result.returncode}",
            }
            
    except subprocess.TimeoutExpired:
        logger.error("[backend_installer] Timeout dépassé (300s)")
        return {
            "success": False,
            "output": "",
            "error": "Timeout dépassé : l'installation a pris trop de temps (> 300s)",
        }
        
    except Exception as exc:
        logger.exception("[backend_installer] Erreur inattendue")
        return {
            "success": False,
            "output": "",
            "error": str(exc),
        }


def backend_package_installer(state) -> dict:
    """
    Nœud LangGraph pour installer les packages du backend après génération.
    
    Cherche requirements.txt dans les fichiers générés et installe les packages.
    
    Args:
        state: État du backend (contient generated_files)
        
    Returns:
        État mis à jour avec installation_status
    """
    # Chercher requirements.txt dans les fichiers générés
    requirements_file = None
    requirements_content = ""
    
    # Accéder à generated_files (state est une dataclass, pas un dict)
    generated_files = getattr(state, "generated_files", [])
    
    for file_info in generated_files:
        if file_info.get("path") == "requirements.txt":
            requirements_file = file_info
            requirements_content = file_info.get("content", "")
            break
    
    if not requirements_file:
        logger.warning("[backend_package_installer] requirements.txt non trouvé dans les fichiers générés")
        state.installation_status = {
            "success": False,
            "error": "requirements.txt non généré",
            "packages_installed": [],
        }
        return state
    
    # Parser les packages
    packages = parse_requirements(requirements_content)
    
    if not packages:
        logger.info("[backend_package_installer] Aucun package à installer (requirements.txt vide)")
        state.installation_status = {
            "success": True,
            "packages_installed": [],
            "message": "requirements.txt vide — aucune installation requise",
        }
        return state
    
    # Installer les packages
    logger.info(f"[backend_package_installer] Packages à installer : {packages}")
    result = install_packages(packages)
    
    state.installation_status = {
        "success": result["success"],
        "packages_installed": packages,
        "output": result["output"],
        "error": result["error"],
    }
    
    if result["success"]:
        if hasattr(state, "logs"):
            state.logs.append(f"[backend_package_installer] ✔ {len(packages)} packages installés avec succès")
    else:
        if hasattr(state, "logs"):
            state.logs.append(f"[backend_package_installer] ✘ Erreur lors de l'installation : {result['error']}")
    
    return state
