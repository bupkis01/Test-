import firebase_admin, json
from firebase_admin import credentials, firestore
import config

# Init Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate("config/firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_match_id(match: dict) -> str:
    return f"{match['match_id']}"

def save_match_to_db(match: dict):
    match_id = get_match_id(match)
    doc_ref = db.collection(config.FIRESTORE_COLLECTION).document(match_id)
    if doc_ref.get().exists:
        print(f"⏭️ Match {match_id} already tracked in Firestore.")
        return
    doc_ref.set(match)
    print(f"✅ Match {match_id} saved to Firestore.")

def get_tracked_matches():
    return [doc.to_dict() for doc in db.collection(config.FIRESTORE_COLLECTION).stream()]

def remove_match_from_db(match: dict):
    match_id = get_match_id(match)
    db.collection(config.FIRESTORE_COLLECTION).document(match_id).delete()
    print(f"🗑️ Match {match_id} removed from Firestore.")

# TEAM INFO (Short name + emoji)

def get_team_mapping(team_name: str):
    doc_ref = db.collection("teams").document(team_name)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_team_mapping(team_name: str, short_name: str, emoji: str):
    doc_ref = db.collection("teams").document(team_name)
    doc_ref.set({
        "short_name": short_name,
        "emoji": emoji
    })
    print(f"✅ Saved team: {team_name} -> {emoji} {short_name}")
