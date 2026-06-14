
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