"""Knowledge-base routes: list/create/delete KB, add/search/QA documents."""
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import logging

from services.file_validator import validate_file, sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter()

knowledge_manager = None

def get_knowledge_manager():
    """Get or create the knowledge manager singleton."""
    global knowledge_manager
    if knowledge_manager is None:
        from app.knowledge import KnowledgeManager
        knowledge_manager = KnowledgeManager()
    return knowledge_manager

@router.get("/api/knowledge/bases")
async def list_knowledge_bases():
    """List all knowledge bases."""
    km = get_knowledge_manager()
    return JSONResponse(km.list_knowledge_bases())

@router.post("/api/knowledge/bases")
async def create_knowledge_base(request: Request):
    """Create a new knowledge base."""
    data = await request.json()
    name = data.get('name', 'default')

    km = get_knowledge_manager()
    kb = km.create_knowledge_base(name)

    return JSONResponse({
        'success': True,
        'name': kb.name,
        'document_count': kb.count()
    })

@router.delete("/api/knowledge/bases/{name}")
async def delete_knowledge_base(name: str):
    """Delete a knowledge base."""
    km = get_knowledge_manager()
    success = km.delete_knowledge_base(name)

    return JSONResponse({
        'success': success
    })

@router.get("/api/knowledge/bases/{name}/stats")
async def get_knowledge_base_stats(name: str):
    """Get knowledge base statistics."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    return JSONResponse(kb.get_stats())

@router.post("/api/knowledge/bases/{name}/documents")
async def add_document_to_knowledge_base(name: str, request: Request):
    """Add a document to a knowledge base."""
    data = await request.json()
    content = data.get('content', '')
    metadata = data.get('metadata', {})

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    doc_id = kb.add_document(content, metadata)

    return JSONResponse({
        'success': True,
        'document_id': doc_id
    })

@router.post("/api/knowledge/bases/{name}/files")
async def upload_files_to_knowledge_base(name: str, files: List[UploadFile] = File(...)):
    """Upload files to a knowledge base."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    results = []
    for file in files:
        try:
            file_content = await file.read()
            file_size = len(file_content)

            is_valid, error_msg = validate_file(file.filename, file_size)
            if not is_valid:
                logger.warning(f"File validation failed for {file.filename}: {error_msg}")
                results.append({
                    'success': False,
                    'filename': file.filename,
                    'error': error_msg
                })
                continue

            safe_filename = sanitize_filename(file.filename)

            temp_path = f"/tmp/{safe_filename}"
            with open(temp_path, 'wb') as f:
                f.write(file_content)

            result = kb.add_file(temp_path)
            result['filename'] = file.filename
            result['safe_filename'] = safe_filename

            try:
                os.remove(temp_path)
            except OSError:
                pass

            results.append(result)
            logger.info(f"Successfully uploaded file: {file.filename}")

        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            results.append({
                'success': False,
                'filename': file.filename,
                'error': f'File processing failed: {str(e)}'
            })

    return JSONResponse({
        'success': True,
        'results': results
    })

@router.get("/api/knowledge/bases/{name}/documents")
async def get_documents(name: str, page: int = 1, page_size: int = 10):
    """List documents in a knowledge base."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    documents = kb.get_all_documents()
    total = len(documents)

    start = (page - 1) * page_size
    end = start + page_size
    paginated = documents[start:end]

    return JSONResponse({
        'success': True,
        'documents': paginated,
        'total': total,
        'page': page,
        'page_size': page_size
    })

@router.get("/api/knowledge/bases/{name}/documents/{doc_id}")
async def get_document(name: str, doc_id: str):
    """Get a single document."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    doc = kb.get_document(doc_id)

    if not doc:
        return JSONResponse({'success': False, 'error': 'Document not found'}, status_code=404)

    return JSONResponse(doc)

@router.delete("/api/knowledge/bases/{name}/documents/{doc_id}")
async def delete_document(name: str, doc_id: str):
    """Delete a document."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    success = kb.delete_document(doc_id)

    return JSONResponse({
        'success': success
    })

@router.post("/api/knowledge/bases/{name}/search")
async def search_knowledge_base(name: str, request: Request):
    """Search a knowledge base."""
    data = await request.json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    results = kb.search(query, top_k)

    return JSONResponse({
        'success': True,
        'results': results,
        'count': len(results)
    })

@router.post("/api/knowledge/bases/{name}/query")
async def query_knowledge_base(name: str, request: Request):
    """Query a knowledge base (QA mode)."""
    data = await request.json()
    question = data.get('question', '')
    llm_config = data.get('llm', None)

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    from app.knowledge import QAEngine

    qa_engine = QAEngine(kb)
    result = await qa_engine.answer(question, llm_config)

    return JSONResponse(result)

@router.post("/api/knowledge/bases/{name}/chat")
async def chat_with_knowledge_base(name: str, request: Request):
    """Chat with a knowledge base (conversational QA)."""
    data = await request.json()
    question = data.get('question', '')
    llm_config = data.get('llm', None)

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    from app.knowledge import ConversationalQAEngine

    qa_engine = ConversationalQAEngine(kb)
    result = await qa_engine.answer(question, llm_config)

    return JSONResponse(result)

@router.post("/api/knowledge/bases/{name}/export")
async def export_knowledge_base(name: str):
    """Export a knowledge base."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    data = kb.export()
    return JSONResponse(data)

@router.post("/api/knowledge/bases/{name}/import")
async def import_to_knowledge_base(name: str, request: Request):
    """Import documents into a knowledge base."""
    data = await request.json()

    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    result = kb.import_documents(data)
    return JSONResponse(result)

@router.delete("/api/knowledge/bases/{name}/clear")
async def clear_knowledge_base(name: str):
    """Clear all documents from a knowledge base."""
    km = get_knowledge_manager()
    kb = km.get_knowledge_base(name)

    if not kb:
        return JSONResponse({'success': False, 'error': 'Knowledge base not found'}, status_code=404)

    kb.clear()

    return JSONResponse({
        'success': True
    })
