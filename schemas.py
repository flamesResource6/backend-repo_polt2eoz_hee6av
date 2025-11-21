"""
Database Schemas for Free Fire Max Tournament App

Each Pydantic model represents a MongoDB collection. The collection name
is the lowercase of the class name (Tournament -> "tournament").
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class Tournament(BaseModel):
    title: str = Field(..., description="Tournament title")
    description: Optional[str] = Field(None, description="Short description")
    game: str = Field("Free Fire Max", description="Game name")
    mode: Literal["Solo", "Duo", "Squad"] = Field("Squad", description="Match mode")
    prize_pool: Optional[str] = Field(None, description="Prize pool details")
    entry_fee: Optional[str] = Field(None, description="Entry fee details")
    max_participants: int = Field(48, ge=1, le=1000, description="Maximum number of teams/players")
    starts_at: Optional[datetime] = Field(None, description="Scheduled start time (UTC)")
    rules: Optional[str] = Field(None, description="Rules and format")
    status: Literal["upcoming", "ongoing", "completed"] = Field("upcoming")
    banner_url: Optional[str] = Field(None, description="Banner image URL")
    region: Optional[str] = Field("Global", description="Server/Region")
    share_code: Optional[str] = Field(None, description="Short share code for the tournament")

class Participant(BaseModel):
    tournament_id: str = Field(..., description="Linked tournament id")
    name: str = Field(..., description="Player or team representative name")
    ign: Optional[str] = Field(None, description="In-game name (IGN)")
    team_name: Optional[str] = Field(None, description="Team name (if Squad/Duo)")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    region: Optional[str] = Field(None, description="Region/Server")
    notes: Optional[str] = Field(None, description="Additional info")

class Match(BaseModel):
    tournament_id: str = Field(..., description="Linked tournament id")
    round_name: str = Field(..., description="Round name, e.g., Qualifiers, Finals")
    map_name: Optional[str] = Field(None, description="Map name")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time (UTC)")
    room_id: Optional[str] = Field(None, description="Custom room ID")
    room_password: Optional[str] = Field(None, description="Custom room password")
    status: Literal["scheduled", "live", "completed"] = Field("scheduled")
    participants: Optional[List[str]] = Field(None, description="Participant ids/names involved")
    result: Optional[dict] = Field(None, description="Result payload with placements/kills etc.")
