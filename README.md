
---

# DDR AI Report Generator

An AI-powered system that automatically converts inspection and thermal PDFs into structured Damage Detection Reports (DDR).

---

## What It Does

* Extracts text and images from PDFs
* Uses AI (CLIP) to map images to relevant areas (hall, bedroom, etc.)
* Generates structured insights:

  * Issues and locations
  * Severity and root cause
  * Recommended actions
* Displays results in a clean UI
* Exports final report as a PDF

---

## Tech Stack

* FastAPI (Backend)
* Streamlit (Frontend)
* OpenCLIP (Image-Text Matching)
* PyMuPDF, ReportLab (PDF Processing)

---

## Run Locally

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
streamlit run app.py
```

Add your Groq API key in `.env`:

```
GROQ_API_KEY=your_key_here
```

---

## Current Limitations

* Thermal images are not mapped accurately
* Some duplicate image assignments may occur

---

## Next Improvements

* Caption-based matching (BLIP)
* Optimal assignment using Hungarian algorithm
* Better thermal image handling

---
