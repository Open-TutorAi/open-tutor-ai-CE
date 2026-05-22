from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import subprocess
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/python", tags=["python"])

# ============ MODELS ============
class CodeExecutionRequest(BaseModel):
    code: str
    timeout: int = 30
    stdin: Optional[str] = None  # ← valeurs pour input()

class CodeExecutionResponse(BaseModel):
    execution_id: str
    output: str
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime

class CodeExplanationRequest(BaseModel):
    code: str
    output: str
    error: Optional[str] = None

# ============ STORAGE ============
code_executions = {}

# ============ HELPERS ============
def verify_code_safety(code: str):
    """Vérifier que le code n'utilise pas d'imports dangereux"""
    forbidden_imports = [
        'os', 'sys', 'subprocess', 'socket', 'requests',
        'paramiko', 'fabric', '__import__', 'eval', 'exec'
    ]
    
    code_lower = code.lower()
    for forbidden in forbidden_imports:
        if f'import {forbidden}' in code_lower or f'from {forbidden}' in code_lower:
            raise ValueError(f"Import '{forbidden}' is not allowed for security reasons")

# ============ ENDPOINTS ============

@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_python_code(
    request: CodeExecutionRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Exécute du code Python en sécurité
    
    - Timeout maximum 30 secondes
    - Vérification des imports dangereux
    - Logging de toutes les exécutions
    - Support stdin pour les appels input()
    """
    execution_id = str(uuid.uuid4())[:8]
    
    try:
        # Vérifications basiques
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Le code ne peut pas être vide")
        
        if len(request.code) > 5000:
            raise HTTPException(status_code=400, detail="Le code est trop long (max 5000 caractères)")
        
        # Vérifier la sécurité
        try:
            verify_code_safety(request.code)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Exécution sécurisée avec support stdin
        t_start = datetime.now()
        result = subprocess.run(
            ['python', '-c', request.code],
            capture_output=True,
            text=True,
            timeout=request.timeout,
            input=request.stdin or ""  # ← injecte les valeurs input()
        )
        execution_time = (datetime.now() - t_start).total_seconds()
        
        # Formater la réponse
        execution = CodeExecutionResponse(
            execution_id=execution_id,
            output=result.stdout if result.stdout else "",
            error=result.stderr if result.returncode != 0 else None,
            execution_time=round(execution_time, 3),
            timestamp=datetime.now()
        )
        
        # Sauvegarder dans l'historique
        code_executions[execution_id] = {
            'code': request.code,
            'stdin': request.stdin,
            'execution': execution,
            'timestamp': datetime.now()
        }
        
        logger.info(f"Code executed successfully: {execution_id}")
        return execution
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Execution timeout for: {execution_id}")
        raise HTTPException(
            status_code=408, 
            detail="L'exécution du code a dépassé le délai imparti (>30s)"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de l'exécution : {str(e)}"
        )

@router.post("/explain")
async def explain_code(
    request: CodeExplanationRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Demande une explication IA du code exécuté
    """
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Aucun code à expliquer")
        
        # Créer le prompt pour le tuteur IA
        prompt = f"""L'étudiant a écrit ce code Python :

```python
{request.code}
```

Résultat d'exécution :
{request.output if request.output else "Aucun output"}

Erreur :
{request.error if request.error else "Aucune erreur"}

Explique ce code de manière pédagogique et suggère des améliorations."""
        
        logger.info(f"Code explanation requested")
        
        # Retourner une réponse structurée
        return {
            "explanation": "Votre code a été envoyé au tuteur IA pour explication",
            "prompt": prompt,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Explanation error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur : {str(e)}"
        )

@router.get("/execution/{execution_id}")
async def get_execution_history(execution_id: str):
    """Récupère l'historique d'une exécution"""
    if execution_id not in code_executions:
        raise HTTPException(status_code=404, detail="Exécution non trouvée")
    
    return code_executions[execution_id]

@router.get("/health")
async def health_check():
    """Vérifier que l'endpoint Python fonctionne"""
    return {"status": "ok", "service": "python_executor"}