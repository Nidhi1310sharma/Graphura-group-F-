
# backend/routes/analyze.py
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends
)
from typing import Optional

from backend.auth import get_current_user_optional
from backend.ml_utils.analysis_service import analyze_content

router = APIRouter(prefix="/analyze", tags=["Analysis"])

@router.post("/")
async def analyze(
    source_type: str = Form(...),
    content: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user_optional)
):
    try:
        user_id = (current_user["user_id"] if current_user else None)
        file_bytes = None

        if file:
            file_bytes = await file.read()

        result = await analyze_content(
            source_type=source_type.upper(),
            user_id=user_id,
            content=content,
            url=url,
            file_bytes=file_bytes
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Analysis failed: {str(e)}")
    
    
@router.post("/compare")
async def compare_analysis(
    source_type: str = Form(...),

    content_a: Optional[str] = Form(None),
    content_b: Optional[str] = Form(None),

    url_a: Optional[str] = Form(None),
    url_b: Optional[str] = Form(None),

    file_a: Optional[UploadFile] = File(None),
    file_b: Optional[UploadFile] = File(None),

    current_user=Depends(get_current_user_optional)
):
    try:
        user_id = current_user["user_id"] if current_user else None

        file_a_bytes = None
        file_b_bytes = None

        if file_a:
            file_a_bytes = await file_a.read()

        if file_b:
            file_b_bytes = await file_b.read()

        result_a = await analyze_content(
            source_type=source_type.upper(),
            user_id=user_id,
            content=content_a,
            url=url_a,
            file_bytes=file_a_bytes
        )

        result_b = await analyze_content(
            source_type=source_type.upper(),
            user_id=user_id,
            content=content_b,
            url=url_b,
            file_bytes=file_b_bytes
        )

        risk_a = result_a.get("risk_score", 100)
        risk_b = result_b.get("risk_score", 100)

        if risk_a < risk_b:
            winner = "A"
        elif risk_b < risk_a:
            winner = "B"
        else:
            winner = "TIE"

        return {
            "success": True,
            "job_a": result_a,
            "job_b": result_b,
            "winner": winner
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )