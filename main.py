from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Пароль администратора для входа в веб-панель
ADMIN_PASSWORD = "supersecretpassword"

def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            hwid TEXT PRIMARY KEY,
            note TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

class HWIDCheck(BaseModel):
    hwid: str

# API для AHK скрипта
@app.post("/api/verify")
def verify_license(data: HWIDCheck):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM users WHERE hwid = ?", (data.hwid,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == 1:
        return {"access": True}
    return {"access": False}

# Страница администратора
@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, key: str = ""):
    if key != ADMIN_PASSWORD:
        return "Неверный ключ доступа."
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT hwid, note, is_active FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "key": key})

# Добавление/Обновление пользователя
@app.post("/admin/add")
def add_user(key: str = Form(...), hwid: str = Form(...), note: str = Form(...)):
    if key != ADMIN_PASSWORD:
        raise HTTPException(status_code=403)
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (hwid, note, is_active) VALUES (?, ?, 1)", (hwid, note))
    conn.commit()
    conn.close()
    return {"status": "ok"}
