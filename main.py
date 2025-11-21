import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import secrets

from database import db, create_document, get_documents
from schemas import Tournament, Participant, Match

app = FastAPI(title="Free Fire Max Tournament API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Utils ---------

def to_str_id(obj):
    if isinstance(obj, dict) and obj.get("_id"):
        obj["id"] = str(obj.pop("_id"))
    return obj


def serialize_list(items: List[dict]):
    return [to_str_id(i) for i in items]


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


# --------- Health ---------
@app.get("/")
def root():
    return {"message": "Free Fire Max Tournament API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:60]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:60]}"
    return response


# --------- Tournaments ---------
@app.get("/api/tournaments")
def list_tournaments():
    items = get_documents("tournament")
    return serialize_list(items)


class CreateTournamentRequest(Tournament):
    pass


@app.post("/api/tournaments")
def create_tournament(payload: CreateTournamentRequest):
    data = payload.model_dump()
    # generate short share code (6-8 chars)
    data["share_code"] = data.get("share_code") or secrets.token_hex(3)
    new_id = create_document("tournament", data)
    doc = db["tournament"].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)


@app.get("/api/tournaments/{tournament_id}")
def get_tournament(tournament_id: str):
    # allow by id or share code
    query = {"_id": oid(tournament_id)} if len(tournament_id) == 24 else {"share_code": tournament_id}
    doc = db["tournament"].find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return to_str_id(doc)


# --------- Participants ---------
class RegisterRequest(Participant):
    pass


@app.post("/api/tournaments/{tournament_id}/register")
def register_participant(tournament_id: str, payload: RegisterRequest):
    # Ensure tournament exists
    t_query = {"_id": oid(tournament_id)} if len(tournament_id) == 24 else {"share_code": tournament_id}
    t = db["tournament"].find_one(t_query)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")

    data = payload.model_dump()
    data["tournament_id"] = str(t.get("_id"))
    new_id = create_document("participant", data)
    doc = db["participant"].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)


@app.get("/api/tournaments/{tournament_id}/participants")
def list_participants(tournament_id: str):
    t_id = tournament_id if len(tournament_id) == 24 else None
    if not t_id:
        # map share code to real id
        t = db["tournament"].find_one({"share_code": tournament_id})
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        t_id = str(t.get("_id"))
    items = get_documents("participant", {"tournament_id": t_id})
    return serialize_list(items)


# --------- Matches ---------
class CreateMatchRequest(Match):
    pass


@app.post("/api/tournaments/{tournament_id}/matches")
def create_match(tournament_id: str, payload: CreateMatchRequest):
    t_query = {"_id": oid(tournament_id)} if len(tournament_id) == 24 else {"share_code": tournament_id}
    t = db["tournament"].find_one(t_query)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    data = payload.model_dump()
    data["tournament_id"] = str(t.get("_id"))
    new_id = create_document("match", data)
    doc = db["match"].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)


@app.get("/api/tournaments/{tournament_id}/matches")
def list_matches(tournament_id: str):
    t_id = tournament_id if len(tournament_id) == 24 else None
    if not t_id:
        t = db["tournament"].find_one({"share_code": tournament_id})
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        t_id = str(t.get("_id"))
    items = get_documents("match", {"tournament_id": t_id})
    return serialize_list(items)


# --------- Sharing ---------
class ShareLinkResponse(BaseModel):
    share_url: str
    code: str


@app.get("/api/tournaments/{tournament_id}/share", response_model=ShareLinkResponse)
def get_share_link(tournament_id: str):
    query = {"_id": oid(tournament_id)} if len(tournament_id) == 24 else {"share_code": tournament_id}
    t = db["tournament"].find_one(query)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    code = t.get("share_code")
    frontend_origin = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return ShareLinkResponse(share_url=f"{frontend_origin}/?t={code}", code=code)


@app.get("/api/share/{code}")
def get_by_share_code(code: str):
    t = db["tournament"].find_one({"share_code": code})
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return to_str_id(t)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
