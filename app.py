"""
EDI 210 AI Summarizer - Backend
--------------------------------
FastAPI server exposing one endpoint that accepts raw EDI 210 text,
parses it into segments, and asks Claude to summarize it.

Run:
    pip install -r requirements.txt
    export GEMINI_API_KEY=your_key_here      (get one free at aistudio.google.com/app/apikey)
    uvicorn app:app --reload --port 8000
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------

app = FastAPI(title="EDI 210 AI Summarizer")

# Allow the local frontend (served separately) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client()  # reads GEMINI_API_KEY from environment

# Free-tier Gemini model. gemini-2.5-flash also works and is free, but
# Google has it scheduled for shutdown on 16 Oct 2026 - flash-lite has
# a longer runway on the free tier.
GEMINI_MODEL = "gemini-3.1-flash-lite"

SEGMENT_MEANINGS = {
    "ISA": "Interchange Control Header",
    "GS": "Functional Group Header",
    "ST": "Transaction Set Header (identifies the doc as a 210)",
    "B2": "Beginning Segment for Invoice",
    "B2A": "Set Purpose (original, cancellation, etc.)",
    "N1": "Name segment (shipper, consignee, carrier, etc.)",
    "N3": "Address",
    "N4": "Geographic location (city/state/zip)",
    "L11": "Reference number (PO, BOL, etc.)",
    "G62": "Date/time",
    "L5": "Description of shipped items",
    "L0": "Line item detail (weight, volume, etc.)",
    "L1": "Rate/charge detail",
    "SE": "Transaction Set Trailer",
    "GE": "Functional Group Trailer",
    "IEA": "Interchange Control Trailer",
}


# ---------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------

class EdiPayload(BaseModel):
    raw_text: str


class Segment(BaseModel):
    id: str
    meaning: str
    elements: list[str]


class SummarizeResponse(BaseModel):
    segments: list[Segment]
    summary: str


# ---------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------

def parse_edi_210(raw_text: str) -> list[Segment]:
    cleaned = raw_text.strip().replace("\n", "")
    raw_segments = [s for s in cleaned.split("~") if s.strip()]

    parsed = []
    for seg in raw_segments:
        elements = seg.split("*")
        seg_id = elements[0].strip()
        parsed.append(Segment(
            id=seg_id,
            meaning=SEGMENT_MEANINGS.get(seg_id, "Unknown segment"),
            elements=elements[1:],
        ))
    return parsed


def build_prompt(segments: list[Segment]) -> str:
    lines = [f"{s.id} ({s.meaning}): {s.elements}" for s in segments]
    joined = "\n".join(lines)
    return f"""You are an EDI expert helping a developer understand a freight
invoice (EDI 210) document. Below is the parsed segment data.

{joined}

Provide:
1. A 2-3 sentence plain-English summary (shipper, consignee, charges, key dates).
2. Any segments that look malformed, missing data, or out of sequence.
3. One beginner-friendly tip about a segment type used here.

Keep it concise, no markdown headers.
"""


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(payload: EdiPayload):
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text is empty")

    segments = parse_edi_210(payload.raw_text)
    if not segments:
        raise HTTPException(status_code=400, detail="No valid EDI segments found")

    prompt = build_prompt(segments)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        summary_text = response.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI request failed: {e}")

    return SummarizeResponse(segments=segments, summary=summary_text)
