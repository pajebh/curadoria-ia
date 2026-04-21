from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/sessoes", tags=["lgpd"])


@router.delete("/me", status_code=204)
async def deletar_dados_sessao() -> None:
    # TODO: implementar deleção LGPD com audit em lgpd_deletions
    raise HTTPException(status_code=501, detail="Não implementado")
