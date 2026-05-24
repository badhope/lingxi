"""
DataAgent - 数据导出 API
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, List, Any
from pathlib import Path
from core.exporter import get_exporter
from core.logging import get_logger

logger = get_logger("exporter_api")

router = APIRouter()


@router.get("/formats")
def get_supported_formats() -> Dict:
    """获取支持的导出格式"""
    exporter = get_exporter()
    return {
        "success": True,
        "data": {
            "formats": exporter.get_supported_formats()
        }
    }


@router.post("/export")
def export_data(
    data: List[Dict[str, Any]],
    format: str = Query("json", description="导出格式"),
    filename: str = Query(None, description="文件名"),
    title: str = Query("Data Report", description="PDF标题"),
    sheet_name: str = Query("Data", description="Excel工作表名")
) -> Dict:
    """导出数据"""
    exporter = get_exporter()
    
    try:
        file_path = exporter.export(
            data, 
            format=format,
            filename=filename,
            title=title,
            sheet_name=sheet_name
        )
        
        if file_path:
            return {
                "success": True,
                "data": {
                    "filename": file_path.name,
                    "path": str(file_path),
                    "format": format
                }
            }
        else:
            return {
                "success": False,
                "message": f"Failed to export in {format} format"
            }
            
    except Exception as e:
        logger.error(f"Export error: {e}")
        return {
            "success": False,
            "message": str(e)
        }


@router.post("/export/download")
def download_export(
    data: List[Dict[str, Any]],
    format: str = Query("json"),
    filename: str = Query(None),
    title: str = Query("Data Report"),
    sheet_name: str = Query("Data")
):
    """导出并下载"""
    exporter = get_exporter()
    
    try:
        file_path = exporter.export(
            data, 
            format=format,
            filename=filename,
            title=title,
            sheet_name=sheet_name
        )
        
        if file_path and file_path.exists():
            media_types = {
                "json": "application/json",
                "csv": "text/csv",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf"
            }
            
            return FileResponse(
                path=str(file_path),
                media_type=media_types.get(format, "application/octet-stream"),
                filename=file_path.name
            )
        else:
            raise HTTPException(status_code=400, detail="Export failed")
            
    except Exception as e:
        logger.error(f"Download export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports")
def list_exports() -> Dict:
    """列出导出文件"""
    exporter = get_exporter()
    
    files = []
    for file in exporter.output_dir.glob("*"):
        if file.is_file():
            files.append({
                "name": file.name,
                "size": file.stat().st_size,
                "created": file.stat().st_ctime,
                "modified": file.stat().st_mtime
            })
    
    # 按修改时间倒序
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {
        "success": True,
        "data": {
            "exports": files
        }
    }


@router.get("/export/{filename}")
def get_export_file(filename: str):
    """下载导出的文件"""
    exporter = get_exporter()
    file_path = exporter.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    media_types = {
        ".json": "application/json",
        ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf"
    }
    
    ext = file_path.suffix.lower()
    return FileResponse(
        path=str(file_path),
        media_type=media_types.get(ext, "application/octet-stream"),
        filename=filename
    )


@router.delete("/export/{filename}")
def delete_export(filename: str) -> Dict:
    """删除导出文件"""
    exporter = get_exporter()
    file_path = exporter.output_dir / filename
    
    if file_path.exists():
        file_path.unlink()
        return {
            "success": True,
            "message": f"Deleted {filename}"
        }
    else:
        return {
            "success": False,
            "message": "File not found"
        }
