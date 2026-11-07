from pathlib import Path
from langchain_ollama import ChatOllama
from repopilot.agents.explorer import build_explorer, make_explorer_tools
from repopilot.agents.implementer import build_implementer


def test_explorer_tools_cannot_write_apply_or_run(tmp_path: Path):
    names = [tool.name for tool in make_explorer_tools(tmp_path)]
    assert names
    assert not any(n.startswith(("apply", "write", "run")) for n in names)


def test_implementer_has_no_write_tool(tmp_path: Path):
    agent_tools = [
        t.name
        for t in make_explorer_tools(tmp_path)
        if t.name in {"read_file_tool", "search_code_tool", "load_skill_tool"}
    ]
    assert sorted(agent_tools) == [
        "load_skill_tool",
        "read_file_tool",
        "search_code_tool",
    ]


def test_agents_build_without_calling_a_model(tmp_path: Path):
    model = ChatOllama(model="qwen2.5:7b")  # construction only; no server is contacted
    assert build_explorer(model, tmp_path) is not None
    assert build_implementer(model, tmp_path, max_llm_calls=40) is not None
