from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            hwid TEXT PRIMARY KEY,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

class HWIDRequest(BaseModel):
    hwid: str

# Эндпоинт проверки лицензии AHK-скриптом
@app.post("/api/verify")
def verify_license(data: HWIDRequest):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM users WHERE hwid = ?", (data.hwid,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == 1:
        return {"status": "success", "access": True}
    return {"status": "error", "access": False}

# Эндпоинт для администратора (добавление HWID)
@app.post("/admin/add_user")
def add_user(data: HWIDRequest, admin_key: str = Header(None)):
    if admin_key != "SECRET_ADMIN_KEY":  # Замените на свой секретный ключ
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (hwid, is_active) VALUES (?, 1)", (data.hwid,))
    conn.commit()
    conn.close()
    return {"message": f"HWID {data.hwid} успешно активирован"}