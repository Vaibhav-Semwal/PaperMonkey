"""
LangGraph pipeline for generating a paper's questions. Using LangGraph
(rather than a plain Python loop) means each step - ingestion, retrieval,
generation per section - shows up as its own traced node in LangSmith once
LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY are set, giving visibility into
where time is spent and what each LLM call actually saw/returned.
"""
import os
from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from asgiref.sync import sync_to_async

from users.models import Paper, QuestionBank, PaperQuestion, Profile
from llm.ingestion import fetch_link_text, chunk_text
from llm.retrieval import top_passages_for_topic
from llm.llm_client import _parse_questions_json  # reuse the JSON-array parser

QWEN_API_BASE_URL = os.environ.get("QWEN_API_BASE_URL", "http://qwen:11434/v1")
QWEN_MODEL_NAME = os.environ.get("QWEN_MODEL_NAME", "qwen2.5:0.5b")


def _make_llm():
    # Ollama's OpenAI-compatible endpoint doesn't check the API key, but
    # ChatOpenAI requires some non-empty string to be passed.
    return ChatOpenAI(
        base_url=QWEN_API_BASE_URL,
        api_key="ollama",
        model=QWEN_MODEL_NAME,
        temperature=0.7,
        timeout=120.0,
    )


class PipelineState(TypedDict):
    paper_id: int
    external_links: List[str]
    topics: List[str]
    sections: List[dict]
    passages: List[str]
    current_section_index: int
    error: Optional[str]


@sync_to_async
def _get_paper(paper_id):
    return Paper.objects.select_related("teacher").get(id=paper_id)


@sync_to_async
def _save_questions_for_section(paper_id, teacher_id, section_letter, qa_pairs, marks_per_question, source_link):
    teacher = Profile.objects.get(id=teacher_id)
    paper = Paper.objects.get(id=paper_id)
    for order, qa in enumerate(qa_pairs):
        bank_entry = QuestionBank.objects.create(
            teacher=teacher,
            question_text=qa["question"],
            answer_text=qa["answer"],
            marks=marks_per_question,
            source_link=source_link,
        )
        PaperQuestion.objects.create(
            paper=paper, section=section_letter, order=order, question=bank_entry,
        )


@sync_to_async
def _set_paper_status(paper_id, status, error_message=""):
    Paper.objects.filter(id=paper_id).update(status=status, error_message=error_message)


async def ingest_node(state: PipelineState) -> PipelineState:
    passages = []
    for link in state["external_links"]:
        text = await fetch_link_text(link)
        passages.extend(chunk_text(text))
    return {**state, "passages": passages}


async def generate_section_node(state: PipelineState) -> PipelineState:
    i = state["current_section_index"]
    section_def = state["sections"][i]
    topics = state["topics"] or ["general"]
    topic = topics[i % len(topics)]

    relevant = top_passages_for_topic(state["passages"], topic, top_k=3)
    context = "\n\n".join(relevant) if relevant else topic

    prompt = (
        "You are creating exam questions from the reference material below.\n\n"
        f"Reference material:\n\"\"\"\n{context}\n\"\"\"\n\n"
        f"Write exactly {section_def['num_questions']} question-and-answer pairs "
        f"based on the reference material above. Each question is worth "
        f"{section_def['marks_per_question']} marks. Respond with ONLY a JSON "
        'array, no other text, in this exact format:\n'
        '[{"question": "...", "answer": "..."}, ...]'
    )

    llm = _make_llm()
    response = await llm.ainvoke(prompt)
    qa_pairs = _parse_questions_json(response.content, section_def["num_questions"])

    paper = await _get_paper(state["paper_id"])
    source_link = state["external_links"][0] if state["external_links"] else ""
    await _save_questions_for_section(
        state["paper_id"], paper.teacher_id, section_def["section"],
        qa_pairs, section_def["marks_per_question"], source_link,
    )

    return {**state, "current_section_index": i + 1}


async def finalize_node(state: PipelineState) -> PipelineState:
    await _set_paper_status(state["paper_id"], Paper.Status.READY)
    return state


def _has_more_sections(state: PipelineState) -> str:
    return "generate_section" if state["current_section_index"] < len(state["sections"]) else "finalize"


def build_graph():
    workflow = StateGraph(PipelineState)
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("generate_section", generate_section_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "generate_section")
    workflow.add_conditional_edges(
        "generate_section",
        _has_more_sections,
        {"generate_section": "generate_section", "finalize": "finalize"},
    )
    workflow.add_edge("finalize", END)

    return workflow.compile()


graph_app = build_graph()


async def run_generation_pipeline(paper_id: int):
    """Entry point called from FastAPI's BackgroundTasks (same signature as before)."""
    try:
        paper = await _get_paper(paper_id)
        initial_state: PipelineState = {
            "paper_id": paper_id,
            "external_links": paper.external_links,
            "topics": paper.topics,
            "sections": paper.sections,
            "passages": [],
            "current_section_index": 0,
            "error": None,
        }
        await graph_app.ainvoke(initial_state)
    except Exception as e:
        await _set_paper_status(paper_id, Paper.Status.FAILED, error_message=str(e))