from langgraph.graph import StateGraph, END

from state import State
from nodes import db_fetcher, plan_agent, task_picker, backend_agent, tester, file_writer, project_analyst
from router import task_router, backend_done_router, analyst_done_router


def build_graph():
    graph = StateGraph(State)

    # ── nodes ──────────────────────────────────────────────────────────────────
    graph.add_node("db_fetcher",       db_fetcher)
    graph.add_node("plan_agent",       plan_agent)
    graph.add_node("task_picker",      task_picker)
    graph.add_node("backend_agent",    backend_agent)
    graph.add_node("tester",           tester)
    graph.add_node("file_writer",      file_writer)
    graph.add_node("project_analyst",  project_analyst)

    # ── entry ──────────────────────────────────────────────────────────────────
    graph.set_entry_point("db_fetcher")

    # db_fetcher → plan_agent (always)
    graph.add_edge("db_fetcher", "plan_agent")

    # plan_agent → task_picker (always, runs once)
    graph.add_edge("plan_agent", "task_picker")

    # task_picker → backend_agent  OR  file_writer (queue exhausted)
    graph.add_conditional_edges(
        "task_picker",
        backend_done_router,
        {
            "continue":    "backend_agent",
            "write_files": "file_writer",
        }
    )

    # backend_agent → tester (always)
    graph.add_edge("backend_agent", "tester")

    # tester → retry same task  |  pass/give_up → next task via task_picker
    graph.add_conditional_edges(
        "tester",
        task_router,
        {
            "retry":   "backend_agent",
            "pass":    "task_picker",
            "give_up": "task_picker",
        }
    )

    # file_writer → project_analyst (always)
    graph.add_edge("file_writer", "project_analyst")

    # project_analyst → END (frontend_agent will plug in here next)
    graph.add_conditional_edges(
        "project_analyst",
        analyst_done_router,
        {
            "frontend": END,   # swap END for "frontend_agent" when ready
        }
    )

    return graph.compile()