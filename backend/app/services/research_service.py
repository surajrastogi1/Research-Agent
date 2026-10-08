import os
from typing import Dict, List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime, timezone
import logging

from app.services.search_service import search_web
from app.db.session import SessionLocal
from app.models.models import Research, Source

def extract_text_content(response_content: Any) -> str:
    """
    Safely extracts string content from response.content regardless of whether 
    it is returned as a plain string or a list of content blocks.
    """
    if isinstance(response_content, str):
        return response_content.strip()

    if isinstance(response_content, list):
        text_parts = []
        for block in response_content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
        return "".join(text_parts)

    return str(response_content).strip()

def run_research_pipeline(question: str) -> Dict[str, Any]:
    """
    1. Generates web search queries.
    2. Fetches web search results.
    3. Uses LLM to synthesize findings into a cited report.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2
    )

    # 1. Search Query Generation
    query_prompt = f"Convert the following research topic into a clear web search query. Output ONLY the search query string:\nTopic: {question}"
    raw_query_response = llm.invoke(query_prompt).content
    search_query = extract_text_content(raw_query_response)

    # 2. Fetch Sources from Web
    sources_data = search_web(search_query, max_results=4)

    # Format context for synthesis
    context_blocks = []
    for idx, src in enumerate(sources_data, 1):
        context_blocks.append(f"Source [{idx}]: {src['title']}\nURL: {src['url']}\nContent: {src['content']}\n")

    full_context = "\n---\n".join(context_blocks)

    # 3. Report Synthesis
    synthesis_prompt = f"""
    You are an expert technical researcher. Answer the following user question using ONLY the provided sources.
    Provide a well-structured Markdown report with sections, bullet points, and citations [1], [2], etc.

    User Question: {question}

    Sources:
    {full_context}

    Write a detailed, informative, and concise report:
    """

    raw_report_response = llm.invoke(synthesis_prompt).content
    report_markdown = extract_text_content(raw_report_response)

    return {
        "report": report_markdown,
        "sources": sources_data
    }

def process_research(research_id: str, question: str) -> None:
    """
    Runs the research pipeline in the background.
    Opens its OWN DB session — must NOT reuse the request's session,
    because that one is closed once the HTTP response is sent.
    """
    db = SessionLocal()
    try:
        # 1. Mark as processing
        research = db.query(Research).filter(Research.id == research_id).first()
        if not research:
            return  # row was deleted; nothing to do

        research.status = "processing"
        db.commit()

        # 2. Run the agent
        result = run_research_pipeline(question)

        # 3. Save sources
        for src in result["sources"]:
            db.add(Source(
                research_id=research.id,
                title=src["title"],
                url=src["url"],
                content=src["content"],
            ))

        # 4. Save report + finish
        research.report = result["report"]
        research.status = "completed"
        research.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception:
        db.rollback()
        # Mark as failed so the client can stop polling
        research = db.query(Research).filter(Research.id == research_id).first()
        if research:
            research.status = "failed"
            db.commit()
        # Re-raise so BackgroundTasks logs it (FastAPI won't swallow it silently)
        raise

    finally:
        db.close()


def stream_research_pipeline(question: str):
    """
    Generator version of the pipeline. Yields event dicts:
      {"event": "status", "data": {...}}
      {"event": "token",  "data": {"text": "..."}}
      {"event": "sources","data": [...]}
      {"event": "done",   "data": {"report": "...", "sources": [...]}}
    The caller is responsible for turning these into SSE frames.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2,
    )

    # 1. Query generation
    yield {"event": "status", "data": {"stage": "generating_query"}}
    query_prompt = (
        "Convert the following research topic into a clear web search query. "
        "Output ONLY the search query string:\n"
        f"Topic: {question}"
    )
    raw_query_response = llm.invoke(query_prompt).content
    search_query = extract_text_content(raw_query_response)
    

    # 2. Web search
    yield {"event": "status", "data": {"stage": "searching", "query": search_query}}
    sources_data = search_web(search_query, max_results=4)
    yield {"event": "sources", "data": sources_data}

    # 3. Synthesis — stream tokens
    yield {"event": "status", "data": {"stage": "synthesizing"}}

    context_blocks = []
    for idx, src in enumerate(sources_data, 1):
        context_blocks.append(
            f"Source [{idx}]: {src['title']}\nURL: {src['url']}\nContent: {src['content']}\n"
        )
    full_context = "\n---\n".join(context_blocks)

    synthesis_prompt = f"""
    You are an expert technical researcher. Answer the following user question using ONLY the provided sources.
    Provide a well-structured Markdown report with sections, bullet points, and citations [1], [2], etc.

    User Question: {question}

    Sources:
    {full_context}

    Write a detailed, informative, and concise report:
    """

    full_report = ""
    for chunk in llm.stream(synthesis_prompt):
        text = extract_text_content(chunk.content)
        if not text:
            continue
        full_report += text
        yield {"event": "token", "data": {"text": text}}
        
    full_report = full_report.strip()
    yield {
        "event": "done",
        "data": {"report": full_report, "sources": sources_data},
    }
