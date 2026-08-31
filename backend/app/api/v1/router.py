from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, cluster, datasets, jobs, prompts, workflows

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(prompts.router)
api_router.include_router(workflows.router)
api_router.include_router(jobs.router)
api_router.include_router(datasets.router)
api_router.include_router(cluster.router)
api_router.include_router(admin.router)
