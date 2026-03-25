"""
api/main.py — FastAPI application exposing the multi-agent pipeline.

Endpoints:
  POST /generate         — Run the full pipeline synchronously
  POST /generate/stream  — Stream reasoning trace as Server-Sent Events
  GET  /health           — Health check
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── Ajouter le parent au chemin pour les imports relatifs ──────────────────
ROOT = Path(__file__).parent.parent  # remonte de api/ à files/
sys.path.insert(0, str(ROOT))

from graph.workflow import app_graph
from state.schema import AgentState

app = FastAPI(
    title="Multi-Agent SDLC Generator",
    description="Generates a full software project from a text specification.",
    version="1.0.0",
)


# ── Request / Response schemas ────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    specification: str
    project_name:  Optional[str] = "generated-app"


class GenerateResponse(BaseModel):
    project_name:     str
    repo_path:        Optional[str]
    repo_url:         Optional[str]
    validation_passed: bool
    files_generated:  list[str]
    reasoning_trace:  list[str]
    qa_report:        Optional[dict]
    c4_context:       Optional[str]
    c4_containers:    Optional[str]
    c4_components:    Optional[str]
    tech_stack:       Optional[dict]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_initial_state(req: GenerateRequest) -> AgentState:
    project_name = req.project_name or "generated-app"
    repo_path = f"./output/{project_name}"
    
    return AgentState(
        raw_input=req.specification,
        project_name=project_name,
        input_images=None,
        functional_requirements=None,
        reasoning_trace=[],
        c4_context=None,
        c4_containers=None,
        c4_components=None,
        tech_stack=None,
        architecture_doc=None,
        repo_path=repo_path,
        repo_url=None,
        cicd_config=None,
        generated_files=[],
        test_files=[],
        qa_report=None,
        validation_passed=False,
        qa_attempts=0,
        current_phase="orchestrator",
        error=None,
        messages=[],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Run the full multi-agent pipeline synchronously and return all artefacts."""
    initial = _build_initial_state(request)
    try:
        final = await app_graph.ainvoke(initial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return GenerateResponse(
        project_name=request.project_name,
        repo_path=final.get("repo_path", ""),
        repo_url=final.get("repo_url", ""),
        validation_passed=final.get("validation_passed", False),
        files_generated=[f["path"] for f in final.get("generated_files", [])],
        reasoning_trace=final.get("reasoning_trace", []),
        qa_report=final.get("qa_report"),
        c4_context=final.get("c4_context"),
        c4_containers=final.get("c4_containers"),
        c4_components=final.get("c4_components"),
        tech_stack=final.get("tech_stack"),
    )


@app.post("/generate/stream")
async def generate_stream(request: GenerateRequest):
    """
    Stream pipeline events as Server-Sent Events.
    Each event is a JSON object: {node, event_type, data}.
    Useful for live dashboards or watching agent reasoning in real-time.
    """
    initial = _build_initial_state(request)

    async def event_generator():
        try:
            async for event in app_graph.astream_events(initial, version="v2"):
                event_name = event.get("event", "")
                node_name  = event.get("name", "")

                if event_name == "on_chain_start":
                    payload = json.dumps({
                        "node":       node_name,
                        "event_type": "start",
                        "data":       {},
                    })
                    yield f"data: {payload}\n\n"

                elif event_name == "on_chain_end":
                    output     = event.get("data", {}).get("output", {})
                    trace      = output.get("reasoning_trace", [])
                    last_trace = trace[-1] if trace else ""
                    payload    = json.dumps({
                        "node":         node_name,
                        "event_type":   "end",
                        "trace":        last_trace,
                        "phase":        output.get("current_phase", ""),
                    })
                    yield f"data: {payload}\n\n"

                elif event_name == "on_chain_error":
                    payload = json.dumps({
                        "node":       node_name,
                        "event_type": "error",
                        "data":       str(event.get("data", {}).get("error", "")),
                    })
                    yield f"data: {payload}\n\n"

                await asyncio.sleep(0)

        except Exception as e:
            yield f"data: {json.dumps({'event_type': 'fatal', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok", "pipeline": "multi-agent-sdlc"}


# ── Database Management Endpoints ─────────────────────────────────────────────

import sqlite3
from fastapi.responses import FileResponse


@app.get("/databases")
def list_databases():
    """Lister toutes les bases de données créées dans ./output/database/"""
    db_dir = Path("./output/database")
    if not db_dir.exists():
        return {"databases": []}
    
    databases = []
    for db_file in db_dir.rglob("*.db"):
        project_name = db_file.parent.name
        databases.append({
            "project_name": project_name,
            "file_path": str(db_file),
            "file_size_mb": db_file.stat().st_size / (1024 * 1024),
            "created_at": db_file.stat().st_ctime,
        })
    
    return {"databases": databases}


@app.get("/databases/{project_name}/schema")
def get_database_schema(project_name: str):
    """Obtenir le schéma complet d'une base de données (tables, colonnes, contraintes)"""
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Récupérer toutes les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_info = {}
        for table in tables:
            # Récupérer le schéma de la table
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            schema_info[table] = {
                "columns": [
                    {
                        "id": col[0],
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default": col[4],
                        "pk": bool(col[5]),
                    }
                    for col in columns
                ],
            }
            
            # Récupérer les foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = cursor.fetchall()
            if fks:
                schema_info[table]["foreign_keys"] = [
                    {
                        "id": fk[0],
                        "seq": fk[1],
                        "table": fk[2],
                        "from": fk[3],
                        "to": fk[4],
                        "on_delete": fk[5],
                        "on_update": fk[6],
                    }
                    for fk in fks
                ]
        
        conn.close()
        return {"project_name": project_name, "tables": list(schema_info.keys()), "schema": schema_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture du schéma: {str(e)}")


@app.get("/databases/{project_name}/data/{table_name}")
def get_table_data(project_name: str, table_name: str, limit: int = 100):
    """Récupérer les données d'une table spécifique"""
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Récupérer les résultats comme des dicts
        cursor = conn.cursor()
        
        # Récupérer les colonnes
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Récupérer les données
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Récupérer le nombre total de lignes
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "project_name": project_name,
            "table_name": table_name,
            "columns": columns,
            "rows": rows,
            "count": len(rows),
            "total_count": total_count,
            "limit": limit,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture des données: {str(e)}")


@app.get("/databases/{project_name}/download")
def download_database(project_name: str):
    """Télécharger la base de données SQLite complète"""
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    return FileResponse(
        path=db_path,
        filename=f"{project_name}.db",
        media_type="application/octet-stream",
    )


@app.post("/databases/{project_name}/query")
def execute_query(project_name: str, query_request: dict):
    """Exécuter une requête SQL personnalisée (SELECT uniquement pour la sécurité)"""
    sql = query_request.get("sql", "").strip()
    
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Seules les requêtes SELECT sont autorisées")
    
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "project_name": project_name,
            "sql": sql,
            "rows": rows,
            "count": len(rows),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur SQL: {str(e)}")


# ── Data Mutation Endpoints ───────────────────────────────────────────────────

@app.post("/databases/{project_name}/data/{table_name}")
def insert_row(project_name: str, table_name: str, row_data: dict):
    """Insérer une nouvelle ligne dans une table"""
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Construire la requête INSERT
        columns = ", ".join(row_data.keys())
        placeholders = ", ".join(["?" for _ in row_data])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        cursor.execute(sql, list(row_data.values()))
        conn.commit()
        
        # Récupérer l'ID de la ligne insérée
        last_id = cursor.lastrowid
        
        conn.close()
        
        return {
            "project_name": project_name,
            "table_name": table_name,
            "inserted_id": last_id,
            "data": row_data,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion: {str(e)}")


@app.put("/databases/{project_name}/data/{table_name}/{row_id}")
def update_row(project_name: str, table_name: str, row_id: int, row_data: dict):
    """Mettre à jour une ligne dans une table"""
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Construire la requête UPDATE
        set_clause = ", ".join([f"{col} = ?" for col in row_data.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        
        values = list(row_data.values()) + [row_id]
        cursor.execute(sql, values)
        conn.commit()
        
        rows_affected = cursor.rowcount
        
        conn.close()
        
        if rows_affected == 0:
            raise HTTPException(status_code=404, detail=f"Ligne avec id {row_id} non trouvée")
        
        return {
            "project_name": project_name,
            "table_name": table_name,
            "row_id": row_id,
            "rows_affected": rows_affected,
            "data": row_data,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")


@app.delete("/databases/{project_name}/data/{table_name}/{row_id}")
def delete_row(project_name: str, table_name: str, row_id: int):
    """Supprimer une ligne d'une table"""
    db_path = Path(f"./output/database/{project_name}/{project_name}.db")
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Base de données '{project_name}' non trouvée")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Construire la requête DELETE
        sql = f"DELETE FROM {table_name} WHERE id = ?"
        cursor.execute(sql, [row_id])
        conn.commit()
        
        rows_affected = cursor.rowcount
        
        conn.close()
        
        if rows_affected == 0:
            raise HTTPException(status_code=404, detail=f"Ligne avec id {row_id} non trouvée")
        
        return {
            "project_name": project_name,
            "table_name": table_name,
            "row_id": row_id,
            "rows_affected": rows_affected,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")
