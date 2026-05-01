from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict

from backend.app.services.parser.parser import parse_documents
from backend.app.services.extractor.extractor import extract_structured_data
#from backend.app.services.merger.merger import merge_data
#from backend.app.services.reasoning.reasoning import run_reasoning
#from backend.app.services.report_generator.generator import generate_ddr

router = APIRouter()


@router.post("/generate")
async def generate_ddr_report(
    inspection_file: UploadFile = File(...),
    thermal_file: UploadFile = File(...)
) -> Dict:
    try:
        # 1. Parse PDFs
        parsed_data = await parse_documents(inspection_file, thermal_file)

        # 2. Extract structured info
        structured_data = extract_structured_data(parsed_data)

        # 3. Merge inspection + thermal
        merged_data = merge_data(structured_data)

        # 4. Run reasoning (LLM / logic)
        reasoned_data = run_reasoning(merged_data)

        # 5. Generate final DDR
        ddr_report = generate_ddr(reasoned_data)

        return {
            "status": "success",
            "data": ddr_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))