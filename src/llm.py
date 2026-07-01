import os
import torch
import json
from crawl4ai import AsyncWebCrawler
from pathlib import Path
from urllib.parse import urlparse
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from .caching import fetch_page, save_crawled_page, set_in_redis
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = Path(os.getenv("MODEL_PATH"))
print("path exists:", MODEL_PATH.exists())

raw_pipe = pipeline(
    "text-generation",
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        local_files_only=True,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
        )
    ),
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        local_files_only=True
    ),
    trust_remote_code=True,
    max_new_tokens=4048,
    do_sample=False,
    repetition_penalty=1.2,
)
llm_pipeline = HuggingFacePipeline(pipeline = raw_pipe)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")
 
__PROMPT_TEMPLATE = (
    "<|im_start|>system\n"
    "You are a precise exam-question generator. You always output a single "
    "valid JSON object and nothing else — no explanations, no markdown fences, "
    "no text before or after the JSON.\n"
    "<|im_end|>\n"
    "<|im_start|>user\n"
    "Using ONLY the information in the Context below, write exam questions on "
    "the given Topic. Do not use outside knowledge or invent facts not present "
    "in the Context.\n\n"
    "Follow this section plan exactly — the number of sections, number of "
    "questions per section, difficulty per question, and marks per question "
    "must all match:\n"
    "{section_plan}\n\n"
    "Output must be valid JSON matching this exact structure:\n"
    "{{\n"
    '  "topics": "string",\n'
    '  "sections": [\n'
    "    {{\n"
    '      "section_number": 1,\n'
    '      "questions": [\n'
    "        {{\n"
    '          "question": "string",\n'
    '          "answer": "string, detailed",\n'
    '          "difficulty": "easy | medium | hard",\n'
    '          "marks": integer\n'
    "        }}\n"
    "      ]\n"
    "    }}\n"
    "  ]\n"
    "}}\n\n"
    "Rules:\n"
    "- Write in formal exam style. Do not copy sentences verbatim from the Context.\n"
    "- Every question and answer must be traceable to the Context.\n"
    "- marks must be a JSON integer, not a string.\n"
    "- Do not use LaTeX notation or backslashes for math (no \\(, \\), \\[, \\], \\frac, etc). "
    "Write math in plain text, e.g. \"40 - 10 = 30\" not \"\\(40 - 10 = 30\\)\".\n"
    "- Return ONLY the JSON object — no preamble, no commentary, no code fences.\n\n"
    "Topic: {input}\n\n"
    "Context:\n"
    "{context}\n"
    "<|im_end|>\n"
    "<|im_start|>assistant\n"
)

#region MAIN PROCESS

async def create(page_urls):
    splitter = RecursiveCharacterTextSplitter(chunk_size= 500, chunk_overlap=50)
    all_splits, failures = [], []

    for url in page_urls:
        try:
            docs = await _load_one(url)
            if not docs:
                failures.append((url, "empty content"))
                continue
            all_splits.extend(splitter.split_documents(docs))
        except Exception as e:
            failures.append((url, repr(e)))      # connection reset, 403, etc. logged, not fatal

    print("loaded chunks:", len(all_splits))
    for url, why in failures:
        print(f"SKIPPED {url} -> \n{why}")

    return all_splits

def process_query(splits , prompt: str, sections_and_questions: dict):

    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    if len(splits) == 0:
        return None

    vectorstore = FAISS.from_documents(splits, embeddings)
    template = PromptTemplate.from_template(__PROMPT_TEMPLATE)
    chain = create_retrieval_chain( 
        vectorstore.as_retriever(search_kwargs={"k": 5}),
        create_stuff_documents_chain(llm_pipeline,template)
    )
    print("created embeddings")

    response = chain.invoke({"input": prompt, 'section_plan': _build_section_plan(sections_and_questions)})
    raw = response["answer"]

    try:
        return _try_extract_json(raw)
    except json.JSONDecodeError:
        raise ValueError(f"No JSON found in model output:\n{raw}")

#endregion

#region HELPER FUNCTIONS

async def _load_one(url):    
    # reading PDF 
    if urlparse(url).path.lower().endswith(".pdf"):
        docs = PyPDFLoader(url).load()
        print("reading PDF")
        await save_crawled_page({
            "url": url,
            "html_content": "",
        })
        return docs
    
    # check redis and db 
    result = await fetch_page(url)
    if result: 
        return result

    # crawl (Redis + DB miss, or force=True) ─────────────────────
    print(f"[CRAWLING] {url}")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        if not result or not getattr(result, "markdown", None):
            return []
        
        page_data = {
            "url": url,
            "title": getattr(result, "title", ""),
            "html_content": result.markdown,
            "status_code": getattr(result, "status_code", 200),
            "etag": (result.response_headers or {}).get("etag", ""),
            "content_type": (result.response_headers or {}).get("content-type", ""),
            "links": [
                link.get("href", "")
                for link in getattr(result, "links", {}).get("internal", [])
                + getattr(result, "links", {}).get("external", [])
                if link.get("href", "").startswith("http")
            ],
        }

        # Save to both DB and Redis
        await save_crawled_page(page_data)
        await set_in_redis(url, page_data)

        return [Document(
            page_content=result.markdown,
            metadata={"source": url},
        )]

def _build_section_plan(questions_per_section: dict):
    return "\n".join(f"- Section {i}: {n[0]} question(s) for {n[1]} marks each" for i, n in questions_per_section.items())

def _try_extract_json(text: str):
    _, _, tail  = text.partition("<|im_start|>assistant")
    start, end = tail.find("{"), tail.rfind("}")
    print("extract result",tail[start:end + 1])
    return json.loads(tail[start:end + 1])

#endregion