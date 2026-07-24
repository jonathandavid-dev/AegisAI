from fastapi import APIRouter
from app.api.v1.auth.router import router as auth_router
from app.api.v1.health.router import router as health_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.documents.router import router as doc_router
from app.api.v1.search.router import router as search_router
from app.api.v1.conversations.router import router as conversations_router
from app.api.v1.organizations.router import router as organizations_router
from app.api.v1.workspaces.router import router as workspaces_router
from app.api.v1.evaluation.router import router as evaluation_router

router = APIRouter()

# Include sub-routers with prefixes and tagging
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(health_router, prefix="/health", tags=["System Health"])
router.include_router(chat_router, prefix="/chat", tags=["Agent Chat"])
router.include_router(doc_router, prefix="/documents", tags=["Knowledge Base"])
router.include_router(search_router, prefix="/search", tags=["Semantic Retrieval"])
router.include_router(conversations_router, prefix="/conversations", tags=["Conversations Memory"])
router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
router.include_router(evaluation_router, prefix="/evaluation", tags=["AI Evaluation"])

