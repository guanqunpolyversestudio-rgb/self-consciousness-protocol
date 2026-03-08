"""Credit System — /api/v1/credits"""
from fastapi import APIRouter
from .. import db

router = APIRouter()


@router.post("/{user_id}/init")
def init_credits(user_id: str):
    balance = db.get_balance(user_id)
    if balance > 0:
        return {"ok": True, "message": "Already initialized", "balance": balance}
    result = db.add_credit(user_id, "init", 500, "Initial credit on first registration")
    return {"ok": True, "message": "Initialized with 500 credits", "balance": result["balance"]}


@router.get("/{user_id}/balance")
def get_balance(user_id: str):
    return {"user_id": user_id, "balance": db.get_balance(user_id)}


@router.get("/{user_id}/transactions")
def get_transactions(user_id: str, limit: int = 20):
    txns = db.get_transactions(user_id, limit)
    return {"user_id": user_id, "transactions": txns, "count": len(txns)}
