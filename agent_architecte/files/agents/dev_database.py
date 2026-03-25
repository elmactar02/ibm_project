# ============================================================
# IMPORTS
# ============================================================
import os
import re
import json
import sqlite3
from dotenv import load_dotenv
from typing import TypedDict, Annotated
import operator
from pathlib import Path

# Phoenix (optionnel - pour l'observabilité, mais peut causer des conflits FastAPI)
try:
    import phoenix as px
    from phoenix.otel import register
    from openinference.instrumentation.langchain import LangChainInstrumentor
    PHOENIX_AVAILABLE = True
except (ImportError, AssertionError) as e:
    print(f"⚠️  Phoenix import failed (non-critical): {e}")
    PHOENIX_AVAILABLE = False

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

import requests
import base64

# ============================================================
# CHARGEMENT ENV + PHOENIX
# ============================================================
load_dotenv()

# ── Répertoires (seront définis dynamiquement par le nœud read_blueprint) ──
OUTPUT_DIR = None  # Défini dans read_blueprint_node
DB_PATH = None     # Défini dans read_blueprint_node

# LLM principal (schéma, migrations, indexes)
llm = ChatMistralAI(model="mistral-large-latest", temperature=0, max_tokens=4096)


# ============================================================
# HELPERS
# ============================================================
def remove_newlines_in_strings(s: str) -> str:
    """Supprime les sauts de ligne à l'intérieur des strings JSON."""
    result, in_str, escaped = [], False, False
    for ch in s:
        if escaped:
            result.append(ch); escaped = False
        elif ch == '\\':
            result.append(ch); escaped = True
        elif ch == '"':
            in_str = not in_str; result.append(ch)
        elif in_str and ch in ('\n', '\r', '\t'):
            result.append(' ')
        else:
            result.append(ch)
    return ''.join(result)

def parse_json(content: str) -> dict:
    if not content or not content.strip():
        return {}
    clean = content.strip()
    clean = clean.replace("```json", "").replace("```", "").strip()
    clean = remove_newlines_in_strings(clean)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    try:
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(clean[start:end])
    except json.JSONDecodeError:
        pass
    return {"raw_content": content}

def save_json(filename: str, data: dict):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  💾 Sauvegardé : {path}")

def adapt_sql_for_sqlite(sql: str) -> str:
    replacements = {
        "SERIAL": "INTEGER", "BIGSERIAL": "INTEGER",
        "VARCHAR": "TEXT",   "BOOLEAN": "INTEGER",
        "TIMESTAMP": "TEXT", "TIMESTAMPTZ": "TEXT",
        "NOW()": "datetime('now')"
    }
    for old, new in replacements.items():
        sql = sql.replace(old, new)
    return sql

def create_fk_triggers(schema_data: dict):
    """Crée des triggers FK basés sur le schéma réel."""
    print("\n  🔒 Création des triggers FK...")
    conn   = sqlite3.connect(DB_PATH, isolation_level=None)
    cursor = conn.cursor()

    for table in schema_data.get("tables", []):
        table_name = table["name"]
        for fk in table.get("foreign_keys", []):
            fk_col    = fk.get("column", "")
            ref       = fk.get("references", "")
            if not fk_col or not ref:
                continue
            ref_table = ref.split("(")[0].strip()
            ref_col   = ref.split("(")[1].replace(")", "").strip() if "(" in ref else "id"

            # Trigger FK INSERT
            trigger_name = f"fk_{table_name}_{fk_col}"
            trigger_sql  = f"""CREATE TRIGGER IF NOT EXISTS {trigger_name}
            BEFORE INSERT ON {table_name}
            BEGIN
                SELECT RAISE(ABORT, 'FOREIGN KEY constraint failed: {fk_col} not in {ref_table}')
                WHERE NEW.{fk_col} IS NOT NULL
                AND (SELECT {ref_col} FROM {ref_table} WHERE {ref_col} = NEW.{fk_col}) IS NULL;
            END"""

            # Trigger CASCADE DELETE
            cascade_name = f"fk_cascade_{table_name}_{fk_col}"
            cascade_sql  = f"""CREATE TRIGGER IF NOT EXISTS {cascade_name}
            AFTER DELETE ON {ref_table}
            BEGIN
                DELETE FROM {table_name} WHERE {fk_col} = OLD.{ref_col};
            END"""

            try:
                cursor.execute(trigger_sql)
                print(f"  ✅ Trigger FK      : {trigger_name}")
                cursor.execute(cascade_sql)
                print(f"  ✅ Trigger Cascade : {cascade_name}")
            except sqlite3.Error as e:
                print(f"  ⚠️  Trigger {trigger_name} : {e}")

    conn.close()

# ============================================================
# OUTILS MCP SQLite
# ============================================================
@tool
def execute_sql(sql: str) -> str:
    """Exécute une requête SQL sur la base de données SQLite."""
    try:
        conn   = sqlite3.connect(DB_PATH, isolation_level=None)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        sql_clean = adapt_sql_for_sqlite(sql.strip())
        cursor.execute(sql_clean)
        sql_upper = sql_clean.upper().strip()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("PRAGMA"):
            rows   = cursor.fetchall()
            cols   = [d[0] for d in cursor.description]
            result = {"columns": cols, "rows": rows, "count": len(rows)}
        else:
            result = {"status": "success"}
        conn.close()
        return json.dumps(result, ensure_ascii=False)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e), "sql": sql})

@tool
def list_tables() -> str:
    """Liste toutes les tables existantes dans la base de données."""
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return json.dumps({"tables": tables})
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)})

@tool
def get_table_schema(table_name: str) -> str:
    """Retourne le schéma réel d'une table."""
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        fkeys = cursor.fetchall()
        conn.close()
        return json.dumps({"table": table_name, "columns": columns, "foreign_keys": fkeys})
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)})

@tool
def count_rows(table_name: str) -> str:
    """Compte le nombre de lignes dans une table."""
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        conn.close()
        return json.dumps({"table": table_name, "count": count})
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)})

mcp_tools      = [execute_sql, list_tables, get_table_schema, count_rows]
llm_with_tools = llm.bind_tools(mcp_tools)

# ============================================================
# STATE
# ============================================================
class DBAgentState(TypedDict):
    messages:        Annotated[list, operator.add]
    blueprint:       dict
    schema_data:     dict
    migrations_data: dict
    indexes_data:    dict
    seeders_data:    dict
    db_report:       dict

# ============================================================
# NODE 1 — Lecture du blueprint
# ============================================================
def read_blueprint_node(state: DBAgentState) -> DBAgentState:
    print("\n📋 [DB 1/6] Lecture du blueprint...")
    global OUTPUT_DIR, DB_PATH
    
    bp = state["blueprint"]
    project_name = bp.get("project", {}).get("name", "default_project")
    
    # ── Extraire les entités du bon endroit (ils peuvent être dans 2 formats) ──
    # Format 1: blueprint["entities"] (ancien)
    # Format 2: blueprint["tech_stack"]["database"]["models"] (nouveau)
    entities = bp.get("entities", [])
    if not entities:
        db_config = bp.get("tech_stack", {}).get("database", {})
        if isinstance(db_config, dict):
            entities = db_config.get("models", [])
    
    # ── Définir les chemins dynamiques
    OUTPUT_DIR = Path(f"./output/database/{project_name}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = str(OUTPUT_DIR / f"{project_name}.db")
    
    db_context = {
        "project":      bp.get("project", {}),
        "entities":     entities,
        "database":     bp.get("tech_stack", {}).get("database", "PostgreSQL") if isinstance(bp.get("tech_stack", {}).get("database"), str) else bp.get("tech_stack", {}).get("database", {}).get("technology", "PostgreSQL"),
        "instructions": bp.get("dev_instructions", {}).get("database", ""),
        "constraints":  bp.get("constraints", []),
    }
    print(f"  ✅ Projet   : {db_context['project'].get('name')}")
    print(f"  ✅ Entités  : {[e.get('name') for e in db_context['entities']]}")
    print(f"  ✅ DB cible : {db_context['database']}")
    print(f"  ✅ OUTPUT   : {OUTPUT_DIR}")
    print(f"  ✅ DB_PATH  : {DB_PATH}")
    return {
        "messages": [AIMessage(content=json.dumps(db_context, indent=2), name="blueprint_reader")],
        "schema_data": {}, "migrations_data": {}, "indexes_data": {},
        "seeders_data": {}, "db_report": {}
    }

# ============================================================
# NODE 2 — Génération du schéma SQL
# ============================================================
def schema_node(state: DBAgentState) -> DBAgentState:
    print("\n🗄️  [DB 2/6] Génération du schéma SQL...")
    db_context = json.loads(state["messages"][-1].content)

    response = llm.invoke([HumanMessage(content=f"""
    Tu es un expert base de données SQLite.
    Analyse les entités du blueprint et génère le schéma SQL complet.

    ENTITÉS À MODÉLISER :
    {json.dumps(db_context['entities'], indent=2)}

    INSTRUCTIONS DU PROJET :
    {db_context['instructions']}

    CONTRAINTES TECHNIQUES :
    {db_context['constraints']}

    RÈGLES SQLite OBLIGATOIRES :
    1. Types UNIQUEMENT : INTEGER, TEXT, REAL, BLOB
    2. Clé primaire → INTEGER PRIMARY KEY AUTOINCREMENT
    3. Colonnes optionnelles (due_date, deleted_at, bio...) → TEXT DEFAULT NULL
    4. Colonnes obligatoires → NOT NULL
    5. Colonnes avec valeur par défaut → TEXT DEFAULT (datetime('now')) pour les timestamps
    6. Clés étrangères → INTEGER NOT NULL avec référence dans "foreign_keys"
    7. Pas de point-virgule à la fin du SQL
    8. email, name, full_name, title, content → TOUJOURS NOT NULL
    9. hashed_password, password → NOT NULL
    10. is_active → INTEGER DEFAULT 1
    11. Ajoute une colonne 'deleted_at TEXT DEFAULT NULL' sur User et Task pour le soft delete"

    FORMAT DE RÉPONSE — Réponds UNIQUEMENT en JSON valide :
    {{
        "tables": [
            {{
                "name": "nom_de_la_table",
                "sql": "CREATE TABLE IF NOT EXISTS nom_table (...)",
                "columns": [
                    {{"name": "col", "type": "TYPE", "constraints": ["CONTRAINTE1", "CONTRAINTE2"]}}
                ],
                "foreign_keys": [
                    {{"column": "fk_col", "references": "autre_table(id)", "on_delete": "CASCADE"}}
                ]
            }}
        ]
    }}

    IMPORTANT :
    - Analyse TOUTES les entités et leurs relations
    - Crée UNE table par entité
    - Déduis les colonnes depuis les champs de chaque entité
    - Respecte les relations (has many → clé étrangère)
    - Aucun texte avant ou après le JSON
    """)])

    data = parse_json(response.content)
    save_json("schema.json", data)
    return {
        "messages":    [AIMessage(content=response.content, name="db_schema")],
        "schema_data": data
    }

# ============================================================
# NODE 3 — Création DB + Triggers FK
# ============================================================
def create_db_node(state: DBAgentState) -> DBAgentState:
    print("\n🛢️  [DB 3/6] Création de la base de données...")
    tables = state["schema_data"].get("tables", [])

    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
        print("  🗑️  Ancienne DB supprimée")

    created, errors = [], []

    for table in tables:
        sql = table.get("sql", "").strip()
        if not sql:
            continue
        if "IF NOT EXISTS" not in sql.upper():
            sql = sql.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")

        print(f"\n  📝 Table : {table['name']}")
        result = json.loads(execute_sql.invoke({"sql": sql}))

        if "error" in result:
            print(f"  ❌ Erreur : {result['error']}")
            errors.append({"table": table["name"], "error": result["error"]})
            print(f"  🔄 Correction automatique...")
            fix = llm_with_tools.invoke([HumanMessage(content=f"""
            Création table échouée.
            SQL : {sql}
            Erreur : {result['error']}
            RÈGLES : Types SQLite uniquement. Colonnes optionnelles → TEXT DEFAULT NULL.
            Utilise execute_sql pour créer la table corrigée.
            """)])
            if hasattr(fix, 'tool_calls') and fix.tool_calls:
                for tc in fix.tool_calls:
                    if tc['name'] == 'execute_sql':
                        fix_result = json.loads(execute_sql.invoke(tc['args']))
                        if "error" not in fix_result:
                            print(f"  ✅ Correction réussie !")
                            created.append(table["name"])
        else:
            print(f"  ✅ Table {table['name']} créée !")
            created.append(table["name"])

    create_fk_triggers(state["schema_data"])

    tables_list = json.loads(list_tables.invoke({})).get("tables", [])
    print(f"\n  📊 Tables créées : {tables_list}")

    return {
        "messages": [AIMessage(
            content=json.dumps({"created": created, "errors": errors}),
            name="create_db"
        )],
    }


def clean_all_strings(text):
        result, in_dq, in_sq, escaped = [], False, False, False
        for ch in text:
            if escaped:
                result.append(ch); escaped = False
            elif ch == '\\':
                result.append(ch); escaped = True
            elif ch == '"' and not in_sq:
                in_dq = not in_dq; result.append(ch)
            elif ch == "'" and not in_dq:
                in_sq = not in_sq; result.append(ch)
            elif (in_dq or in_sq) and ch in ('\n', '\r', '\t'):
                result.append(' ')
            else:
                result.append(ch)
        return ''.join(result)



def fix_invalid_escapes(s: str) -> str:
    """Remplace les séquences \\X invalides en JSON par \\\\X."""
    VALID_ESCAPES = set(r'"\bfnrtu/')
    result, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            if s[i+1] in VALID_ESCAPES:
                result.append(s[i]); result.append(s[i+1])
                i += 2
            else:
                # Backslash invalide → on le double
                result.append('\\\\'); result.append(s[i+1])
                i += 2
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)

# ============================================================
# NODE 4 — Migrations + Indexes + Seeders
# ============================================================
def migrations_node(state: DBAgentState) -> DBAgentState:
    print("\n⚙️  [DB 4/6] Migrations, indexes et seeders...")

    schema = json.dumps(state["schema_data"], indent=2)
    db_context = json.loads(state["messages"][0].content)

    # Récupère le vrai schéma de chaque table
    tables_real_schema = {}
    for table in state["schema_data"].get("tables", []):
        real = json.loads(get_table_schema.invoke({"table_name": table["name"]}))
        tables_real_schema[table["name"]] = real
        # Format: (cid, name, type, notnull, default, pk)
        cols = [(col[1], col[3], col[4]) for col in real.get("columns", [])]
        print(f"  📋 {table['name']} : {cols}")

    # ── Migrations ──
    migration_response = llm.invoke([HumanMessage(content=f"""
    Tu es un expert Alembic. Génère la migration initiale.
    SCHEMA : {schema}
    Réponds UNIQUEMENT en JSON :
    {{"revision": "001_initial", "description": "Initial schema", "python_code": "def upgrade():\\n    pass\\n\\ndef downgrade():\\n    pass"}}
    """)])
    migrations_data = parse_json(migration_response.content)
    save_json("migrations.json", migrations_data)

    # ── Indexes ──
    index_response = llm.invoke([HumanMessage(content=f"""
    Tu es un expert SQLite. Génère les indexes optimaux.
    SCHEMA : {schema}
    RÈGLES : SQL sur UNE SEULE LIGNE. Utilise CREATE INDEX IF NOT EXISTS.
    Réponds UNIQUEMENT en JSON :
    {{"indexes": [{{"name": "idx_nom", "table": "table", "columns": ["col"], "reason": "pourquoi", "sql": "CREATE INDEX IF NOT EXISTS idx_nom ON table(col)"}}]}}
    """)])
    indexes_data = parse_json(index_response.content)
    save_json("indexes.json", indexes_data)

    # ── Seeders  ──
    print("\n  🌱 Génération des seeders ...")

    # Construit un résumé clair du schéma pour le prompt
    schema_summary = ""
    for table_name, real in tables_real_schema.items():
        cols = real.get("columns", [])
        col_details = []
        for col in cols:
            # (cid, name, type, notnull, default, pk)
            cid, name, ctype, notnull, default, pk = col
            if pk:
                col_details.append(f"{name}: AUTOINCREMENT (skip)")
            elif notnull and default is None:
                col_details.append(f"{name}: {ctype} NOT NULL (obligatoire)")
            elif default == 'NULL' or (not notnull and default is None):
                col_details.append(f"{name}: {ctype} DEFAULT NULL → mettre NULL")
            else:
                col_details.append(f"{name}: {ctype} DEFAULT {default}")
        schema_summary += f"\nTable '{table_name}':\n" + "\n".join(f"  - {d}" for d in col_details) + "\n"

    seeder_response = llm.invoke([HumanMessage(content=f"""
    Tu es un expert SQLite. Génère des données de test réalistes en français.

    SCHÉMA RÉEL DES TABLES (colonnes exactes) :
    {schema_summary}

    RÈGLES TECHNIQUES OBLIGATOIRES :
    1. N'inclus JAMAIS la colonne "id" (AUTOINCREMENT automatique)
    2. Colonnes DEFAULT NULL → valeur NULL
    3. Colonnes NOT NULL → donne une vraie valeur cohérente
    4. Timestamps et colonnes avec DEFAULT datetime('now') → utilise la valeur littérale 'datetime(''now'')' 
       OU une date fixe comme '2024-01-15 10:00:00' — JAMAIS une valeur vide ou NULL pour ces colonnes
    5. SQL sur UNE SEULE LIGNE, zéro retour à la ligne
    6. Respecte l'ordre des FK : insère d'abord les tables sans FK
    7. Pour les FK (user_id, task_id...) → utilise des IDs existants (1, 2, 3...)
    8. Minimum 5 lignes par table
    9. Valeurs ENUM : utilise EXACTEMENT les valeurs en MAJUSCULES
       - priority → UNIQUEMENT 'LOW', 'MEDIUM' ou 'HIGH'
       - status   → UNIQUEMENT 'TODO', 'IN_PROGRESS' ou 'DONE'
    10. Un seul INSERT par table avec TOUS les VALUES groupés :
        INSERT INTO Task (...) VALUES (...), (...), (...)
        PAS de multiples INSERT séparés par des points-virgules

    CONTRAINTES DE QUALITÉ :
    - Les données doivent être cohérentes avec le contexte du projet : {db_context['project']['description']}
    - Utilise des données variées et réalistes (pas "test1", "test2"...)
    - Les valeurs doivent refléter un vrai usage de l'application
    RÈGLE SEEDERS UNIQUEMENT (pas de production) :
- hashed_password → utilise TOUJOURS la valeur littérale : 'hashed_password_test'
- NE génère JAMAIS un vrai hash bcrypt ($2b$...) — c'est du JSON, pas du Python

    Réponds UNIQUEMENT avec du JSON valide, sans markdown, sans commentaires :
    {{"seeders":[{{"table":"users","description":"5 utilisateurs","sql":"INSERT INTO users (...) VALUES (...), (...)","count":5}},{{"table":"tasks","description":"5 taches","sql":"INSERT INTO tasks (...) VALUES (...), (...)","count":5}},{{"table":"comments","description":"5 commentaires","sql":"INSERT INTO comments (...) VALUES (...), (...)","count":5}}]}}
    """)])

    # Parse la réponse
    raw = seeder_response.content
    raw = raw.replace("```json", "").replace("```", "").strip()
    raw = re.sub(r'\$2[ab]\$\d+\$[A-Za-z0-9./]+', 'hashed_password_test', raw)  # bcrypt
    raw = remove_newlines_in_strings(raw)
    raw = fix_invalid_escapes(raw)   # ← LE FIX PRINCIPAL

    seeders_data = {"seeders": []}
    try:
        seeders_data = json.loads(raw)
        print(f"  ✅ Seeders parsés : {len(seeders_data.get('seeders', []))} tables")
    except json.JSONDecodeError as e:
        print(f"  ❌ Parse échoué : {e}")
        print(f"  📝 Début réponse : {raw[:300]}")
        # Tentative extraction brute
        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            seeders_data = json.loads(raw[start:end])
            print(f"  ✅ Seeders parsés (extraction) : {len(seeders_data.get('seeders', []))} tables")
        except Exception as e2:
            print(f"  ❌ Extraction échouée aussi : {e2}")

    save_json("seeders.json", seeders_data)
    print(f"  📊 Seeders générés : {len(seeders_data.get('seeders', []))}")


    # ── Exécute les indexes ──
    print("\n  📈 Création des indexes...")
    for idx in indexes_data.get("indexes", []):
        result = json.loads(execute_sql.invoke({"sql": idx["sql"]}))
        if "error" not in result:
            print(f"  ✅ Index {idx['name']} créé")
        else:
            print(f"  ⚠️  Index {idx['name']} : {result['error']}")

    # ── Exécute les seeders ──
    print("\n  🌱 Insertion des seeders...")
    
    # Force l'ordre : User en premier, puis tables avec FK
    ORDER = ["User", "Task", "Comment", "History"]
    seeders_sorted = sorted(
        seeders_data.get("seeders", []),
        key=lambda s: ORDER.index(s["table"]) if s["table"] in ORDER else 99
    )
    
    inserted = set()  # tables insérées avec succès
    
    for seeder in seeders_sorted:
        sql = seeder.get("sql", "").strip()
        if not sql:
            continue

        # Vérifie que les tables parentes sont déjà insérées
        table = seeder["table"]
        if table in ("Task", "Comment", "History") and "User" not in inserted:
            print(f"  ⏭️  {table} ignorée (User vide)")
            continue

        print(f"\n  → {table} : {sql[:80]}...")
        result = json.loads(execute_sql.invoke({"sql": sql}))

        if "error" not in result:
            print(f"  ✅ {table} : {seeder.get('count', '?')} lignes insérées")
            inserted.add(table)
        else:
            print(f"  ❌ {table} ÉCHOUÉ : {result['error']}")
            print(f"  🔄 Auto-correction ...")

            fix_response = llm.invoke([HumanMessage(content=f"""
  INSERT échoué.
  SQL    : {sql}
  Erreur : {result['error']}

  Schéma réel :
  {schema_summary}

  Corrige le SQL pour la table {table}.
  RÈGLES STRICTES :
  - Timestamps/dates : utilise '2024-01-15 10:00:00' (jamais datetime('now'), jamais NULL pour NOT NULL)
  - Valeurs ENUM : 'LOW'/'MEDIUM'/'HIGH' et 'TODO'/'IN_PROGRESS'/'DONE' en MAJUSCULES
  - hashed_password → 'hashed_password_test'
  - Un seul INSERT avec tous les VALUES groupés, sur une seule ligne
  - Pas d'id
  Réponds UNIQUEMENT avec le SQL INSERT corrigé, sans markdown.
  """)])
            fixed_sql = fix_response.content.strip().replace("```sql","").replace("```","").strip()
            fixed_sql = fixed_sql.split("\n")[0].strip()
            if fixed_sql.upper().startswith("INSERT"):
                fix_result = json.loads(execute_sql.invoke({"sql": fixed_sql}))
                if "error" not in fix_result:
                    print(f"  ✅ Correction réussie !")
                    inserted.add(table)
                else:
                    print(f"  ❌ Correction échouée : {fix_result['error']}")

    # ── Vérification ──
    print("\n  📊 Vérification des données :")
    for t in json.loads(list_tables.invoke({})).get("tables", []):
        count  = json.loads(count_rows.invoke({"table_name": t})).get("count", 0)
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {t} : {count} ligne(s)")

    return {
    "messages": [
      AIMessage(content=migration_response.content, name="db_migrations"),
      AIMessage(content=index_response.content,    name="db_indexes"),
      AIMessage(content=seeder_response.content,   name="db_seeders"),
    ],
    "migrations_data": migrations_data,
    "indexes_data":    indexes_data,
    "seeders_data":    seeders_data,
    }

# ============================================================
# NODE 5 — Tests automatiques
# ============================================================
def test_db_node(state: DBAgentState) -> DBAgentState:
    print("\n🧪 [DB 5/6] Tests automatiques...")
    results  = {"passed": [], "failed": []}
    tables   = json.loads(list_tables.invoke({})).get("tables", [])
    expected = [t["name"] for t in state["schema_data"].get("tables", [])]

    # TEST 1 : Tables existent
    print("\n  📋 Test 1 : Existence des tables")
    for t in expected:
        if t in tables:
            print(f"  ✅ '{t}' existe")
            results["passed"].append(f"Table '{t}' existe")
        else:
            print(f"  ❌ '{t}' manquante !")
            results["failed"].append(f"Table '{t}' manquante")

    # TEST 2 : Données insérées
    print("\n  📋 Test 2 : Données de test")
    for t in expected:
        count = json.loads(count_rows.invoke({"table_name": t})).get("count", 0)
        if count > 0:
            print(f"  ✅ '{t}' : {count} ligne(s)")
            results["passed"].append(f"'{t}' contient {count} lignes")
        else:
            print(f"  ❌ '{t}' est vide !")
            results["failed"].append(f"'{t}' est vide")

    # TEST 3 : Contraintes UNIQUE
    print("\n  📋 Test 3 : Contraintes UNIQUE")
    for table in state["schema_data"].get("tables", []):
        for col in table.get("columns", []):
            if "UNIQUE" in col.get("constraints", []):
                row = json.loads(execute_sql.invoke({
                    "sql": f"SELECT {col['name']} FROM {table['name']} LIMIT 1"
                }))
                if row.get("rows"):
                    val     = row["rows"][0][0]
                    val_str = f"'{val}'" if isinstance(val, str) else str(val)
                    real    = json.loads(get_table_schema.invoke({"table_name": table["name"]}))
                    needed  = {c[1]: c for c in real.get("columns", []) if c[3] == 1 and c[5] == 0}
                    ins_cols = [col['name']]
                    ins_vals = [val_str]
                    for c_name in needed:
                        if c_name != col['name']:
                            ins_cols.append(c_name)
                            ins_vals.append(f"'test_{c_name}'")
                    test_sql = f"INSERT INTO {table['name']} ({', '.join(ins_cols)}) VALUES ({', '.join(ins_vals)})"
                    result   = json.loads(execute_sql.invoke({"sql": test_sql}))
                    if "error" in result and "UNIQUE" in result["error"].upper():
                        print(f"  ✅ UNIQUE {table['name']}.{col['name']}")
                        results["passed"].append(f"UNIQUE {table['name']}.{col['name']} OK")
                    else:
                        print(f"  ❌ UNIQUE {table['name']}.{col['name']} échouée")
                        results["failed"].append(f"UNIQUE {table['name']}.{col['name']} échouée")

    # TEST 4 : Contraintes NOT NULL
    print("\n  📋 Test 4 : Contraintes NOT NULL")
    for table in state["schema_data"].get("tables", []):
        for col in table.get("columns", []):
            if "NOT NULL" in col.get("constraints", []) and "PRIMARY KEY" not in col.get("constraints", []):
                result = json.loads(execute_sql.invoke({
                    "sql": f"INSERT INTO {table['name']} ({col['name']}) VALUES (NULL)"
                }))
                if "error" in result and "NOT NULL" in result["error"].upper():
                    print(f"  ✅ NOT NULL {table['name']}.{col['name']}")
                    results["passed"].append(f"NOT NULL {table['name']}.{col['name']} OK")
                    break

    # TEST 5 : Clés étrangères (triggers)
    print("\n  📋 Test 5 : Clés étrangères (triggers)")
    for table in state["schema_data"].get("tables", []):
        if table.get("foreign_keys"):
            fk     = table["foreign_keys"][0]
            fk_col = fk.get("column", "user_id")
            result = json.loads(execute_sql.invoke({
                "sql": f"INSERT INTO {table['name']} ({fk_col}) VALUES (99999)"
            }))
            if "error" in result and "FOREIGN KEY" in result["error"].upper():
                print(f"  ✅ FK trigger {table['name']}.{fk_col}")
                results["passed"].append(f"FK {table['name']}.{fk_col} OK")
            else:
                print(f"  ⚠️  FK {table['name']}.{fk_col} non bloquante")
                results["failed"].append(f"FK {table['name']}.{fk_col} non vérifiée")

    # TEST 6 : Soft delete
    print("\n  📋 Test 6 : Soft delete")
    soft_delete_found = False
    for table in state["schema_data"].get("tables", []):
        cols = [c["name"] for c in table.get("columns", [])]
        if "deleted_at" in cols:
            soft_delete_found = True
            result = json.loads(execute_sql.invoke({
                "sql": f"SELECT * FROM {table['name']} WHERE deleted_at IS NULL LIMIT 1"
            }))
            if "error" not in result:
                print(f"  ✅ deleted_at sur {table['name']}")
                results["passed"].append(f"Soft delete {table['name']} OK")
    
    if not soft_delete_found:
        print("  ⏭️  Aucune table avec deleted_at (soft delete non implémenté)")
    # TEST 7 : Timestamps
    print("\n  📋 Test 7 : Timestamps")
    for table in state["schema_data"].get("tables", []):
        cols = [c["name"] for c in table.get("columns", [])]
        if "created_at" in cols:
            result = json.loads(execute_sql.invoke({
                "sql": f"SELECT created_at FROM {table['name']} LIMIT 1"
            }))
            if "error" not in result and result.get("count", 0) > 0:
                ts = result["rows"][0][0]
                if ts:
                    print(f"  ✅ Timestamp {table['name']} : {ts}")
                    results["passed"].append(f"Timestamp {table['name']} OK")
                    break

    # TEST 8 : JOINs
    print("\n  📋 Test 8 : Requêtes JOIN")
    for table in state["schema_data"].get("tables", []):
        for fk in table.get("foreign_keys", []):
            ref_table = fk.get("references", "").split("(")[0].strip()
            fk_col    = fk.get("column", "")
            if ref_table and fk_col:
                result = json.loads(execute_sql.invoke({
                    "sql": f"SELECT t.*, r.id FROM {table['name']} t LEFT JOIN {ref_table} r ON r.id = t.{fk_col} LIMIT 3"
                }))
                if "error" not in result:
                    print(f"  ✅ JOIN {table['name']} ↔ {ref_table} ({result.get('count', 0)} résultats)")
                    results["passed"].append(f"JOIN {table['name']}↔{ref_table} OK")

    # RÉSUMÉ
    print(f"\n  {'='*40}")
    print(f"  📊 RÉSUMÉ : ✅ {len(results['passed'])} réussis / ❌ {len(results['failed'])} échoués")
    for f in results["failed"]:
        print(f"  → ❌ {f}")

    save_json("test_results.json", results)
    return {"messages": [AIMessage(content=json.dumps(results), name="test_db")]}


def should_fix(state: DBAgentState) -> str:
    test_results = json.loads(state["messages"][-1].content)
    empty = [f for f in test_results.get("failed", []) if "est vide" in f]
    
    # Compte combien de fois on a déjà tenté (évite boucle infinie)
    fix_attempts = sum(1 for m in state["messages"] if getattr(m, "name", "") == "fix_seeders")
    
    if empty and fix_attempts < 3:
        print(f"\n  ⚠️  {len(empty)} table(s) vide(s), tentative {fix_attempts + 1}/3")
        return "fix"
    return "report"


# ============================================================
# NODE 5b — Auto-correction des seeders échoués
# ============================================================
def fix_seeders_node(state: DBAgentState) -> DBAgentState:
    print("\n🔧 Auto-correction des seeders...")

    test_results = json.loads(state["messages"][-1].content)
    empty_tables = [
        f.split("'")[1]
        for f in test_results.get("failed", [])
        if "est vide" in f
    ]

    if not empty_tables:
        return {"messages": [AIMessage(content=json.dumps({"fixed": []}), name="fix_seeders")]}

    print(f"  🎯 Tables à corriger : {empty_tables}")

    # Reconstruit schema_summary depuis le schéma réel
    schema_summary = ""
    for table in state["schema_data"].get("tables", []):
        name = table["name"]
        real = json.loads(get_table_schema.invoke({"table_name": name}))
        col_details = []
        for col in real.get("columns", []):
            cid, cname, ctype, notnull, default, pk = col
            if pk:
                col_details.append(f"{cname}: AUTOINCREMENT (skip)")
            elif notnull and default is None:
                col_details.append(f"{cname}: {ctype} NOT NULL (obligatoire)")
            else:
                col_details.append(f"{cname}: {ctype} DEFAULT {default}")
        schema_summary += f"\nTable '{name}':\n" + "\n".join(f"  - {d}" for d in col_details) + "\n"

    # Ordre d'insertion basé sur les dépendances FK
    ORDER = [t["name"] for t in state["schema_data"].get("tables", [])]
    empty_tables_sorted = sorted(
        empty_tables,
        key=lambda t: ORDER.index(t) if t in ORDER else 99
    )

    # Tables déjà peuplées
    inserted = {
        t["name"] for t in state["schema_data"].get("tables", [])
        if json.loads(count_rows.invoke({"table_name": t["name"]})).get("count", 0) > 0
    }

    fixed = []
    for table in empty_tables_sorted:
        # Vérifie les dépendances FK dynamiquement
        table_def = next((t for t in state["schema_data"]["tables"] if t["name"] == table), {})
        parents = {fk.get("references","").split("(")[0].strip() for fk in table_def.get("foreign_keys", [])}
        missing = parents - inserted
        if missing:
            print(f"  ⏭️  {table} ignorée (parents manquants : {missing})")
            continue

        print(f"  🔄 Génération INSERT pour '{table}'...")
        fix_response = llm.invoke([HumanMessage(content=f"""
Génère un INSERT SQLite valide pour la table '{table}'.

SCHÉMA :
{schema_summary}

IDs disponibles dans les tables parentes : 1, 2, 3, 4, 5

RÈGLES STRICTES :
1. Pas de colonne 'id' (AUTOINCREMENT)
2. Timestamps NOT NULL → '2024-01-15 10:00:00'
3. Colonnes DEFAULT NULL → NULL
4. hashed_password → 'hashed_password_test'
5. Un seul INSERT avec 5 VALUES groupés, sur UNE SEULE LIGNE
6. FK → utilise les IDs 1, 2, 3... qui existent dans les tables parentes

Réponds UNIQUEMENT avec le SQL INSERT, sans markdown.
""")])

        sql = fix_response.content.strip().replace("```sql","").replace("```","").strip()
        sql = sql.split("\n")[0].strip()

        if not sql.upper().startswith("INSERT"):
            print(f"  ❌ Réponse invalide")
            continue

        result = json.loads(execute_sql.invoke({"sql": sql}))
        if "error" not in result:
            print(f"  ✅ '{table}' corrigée !")
            fixed.append(table)
            inserted.add(table)
        else:
            print(f"  ❌ '{table}' échouée : {result['error']}")

    return {
        "messages": [AIMessage(content=json.dumps({"fixed": fixed}), name="fix_seeders")]
    }
# ============================================================
# NODE 6 — Rapport final
# ============================================================
def report_node(state: DBAgentState) -> DBAgentState:
    print("\n📊 [DB 6/6] Rapport final...")

    tables      = json.loads(list_tables.invoke({})).get("tables", [])
    tables_info = []
    for t in tables:
        tables_info.append({
            "name":   t,
            "schema": json.loads(get_table_schema.invoke({"table_name": t})),
            "count":  json.loads(count_rows.invoke({"table_name": t})).get("count", 0)
        })

    report = {
        "status":  "completed",
        "project": state["blueprint"].get("project", {}).get("name"),
        "summary": {
            "tables":     len([t for t in tables if t != "sqlite_sequence"]),
            "indexes":    len(state["indexes_data"].get("indexes", [])),
            "migrations": 1,
            "seeders":    len(state["seeders_data"].get("seeders", []))
        },
        "tables_info": tables_info,
        "for_backend": {
            "schema":   state["schema_data"],
            "full_sql": "\n".join([t.get("sql", "") for t in state["schema_data"].get("tables", [])]),
            "tables":   state["schema_data"].get("tables", [])
        },
        "files_generated": [
            "outputs/schema.json",       "outputs/migrations.json",
            "outputs/indexes.json",      "outputs/seeders.json",
            "outputs/test_results.json", "outputs/db_report.json",
            "outputs/todo_app.db"
        ]
    }

    save_json("db_report.json", report)
    print(f"\n  ✅ {report['summary']['tables']} tables")
    print(f"  ✅ {report['summary']['indexes']} indexes")
    print(f"  ✅ {report['summary']['seeders']} seeders")

    return {
        "messages":  [AIMessage(content=json.dumps(report), name="db_report")],
        "db_report": report
    }



# ============================================================
# GRAPH
# ============================================================
workflow = StateGraph(DBAgentState)
workflow.add_node("read_blueprint", read_blueprint_node)
workflow.add_node("schema",         schema_node)
workflow.add_node("create_db",      create_db_node)
workflow.add_node("migrations",     migrations_node)
workflow.add_node("test_db",        test_db_node)
workflow.add_node("fix_seeders",     fix_seeders_node)
workflow.add_node("report",         report_node)

workflow.set_entry_point("read_blueprint")
workflow.add_edge("read_blueprint", "schema")
workflow.add_edge("schema",         "create_db")
workflow.add_edge("create_db",      "migrations")
workflow.add_edge("migrations",     "test_db")
workflow.add_conditional_edges(       
    "test_db",
    should_fix,
    {"fix": "fix_seeders", "report": "report"}
)
workflow.add_edge("fix_seeders",     "test_db")
workflow.add_edge("report", END)

graph = workflow.compile()

# ── Sauvegarde le graph en PNG ──
def save_graph_png(graph, path="outputs/graph.png"):
    try:
        mermaid  = graph.get_graph().draw_mermaid()
        encoded  = base64.urlsafe_b64encode(mermaid.encode()).decode()
        response = requests.get(f"https://mermaid.ink/img/{encoded}", timeout=10)
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            print(f"📸 Graph sauvegardé : {path}")
    except Exception as e:
        print(f"⚠️  Graph PNG : {e}")


# ============================================================
# EXÉCUTION
# ============================================================
if __name__ == "__main__":
  
    print("🔍 Démarrage de Phoenix sur http://localhost:6006 ...")
    session = px.launch_app()
    tracer_provider = register(
        project_name="db-agent",
        endpoint="http://localhost:6006/v1/traces"
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    save_graph_png(graph)
    with open('outputs/architect_blueprint.json', 'r', encoding='utf-8') as f:
        blueprint_example = json.load(f)
        
        print("=" * 60)
        print("🚀 DB AGENT — LangGraph + Phoenix + SQLite")
        print("=" * 60)

        result = graph.invoke({
            "messages":        [],
            "blueprint":       blueprint_example,
            "schema_data":     {},
            "migrations_data": {},
            "indexes_data":    {},
            "seeders_data":    {},
            "db_report":       {}
        })

        print("\n" + "=" * 60)
        print("✅ FICHIERS GÉNÉRÉS dans ./outputs/")
        print("=" * 60)
        for f in result["db_report"].get("files_generated", []):
            print(f"  📄 {f}")

        print("\n  🛢️  Vérification : sqlite3 outputs/todo_app.db")
        print("  🔍  Traces Phoenix : http://localhost:6006")
        input("\n⏸️  Appuie sur Entrée pour fermer...\n")
