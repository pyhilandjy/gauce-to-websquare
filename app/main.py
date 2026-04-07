from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import (
    dongwon,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://youtube-study-archive.vercel.app",
        "http://10.200.40.114:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.mount("/videos", StaticFiles(directory="/app/video_storage"), name="videos")

# app.include_router(signup.router, tags=["sign"])
# app.include_router(login.router, tags=["login"])
# app.include_router(category.router, tags=["category"])
# app.include_router(contents_list.router, tags=["contents_list"])
# app.include_router(contents.router, tags=["contents"])
app.include_router(dongwon.router, tags=["dongwon"])


@app.get("/")
def root():
    return {"message": "Gauce to Websquar"}
