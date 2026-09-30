from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="AHK License Management Server")
templates = Jinja2Templates(directory="templates")

# Пароль администратора для доступа к веб-панели
ADMIN_PASSWORD = "supersecretpassword"

def get_db():
    conn = sqlite3.connect("licenses.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

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

# 1. Главная страница сервера (решает проблему Not Found)
@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Сервер авторизации AHK</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; text-align: center; padding-top: 100px; }
            .container { background-color: #1e1e1e; padding: 40px; border-radius: 8px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            h1 { color: #4CAF50; }
            p { color: #bbb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Сервер успешно работает</h1>
            <p>API авторизации готово к приему запросов от AHK скрипта.</p>
        </div>
    </body>
    </html>
    """

# 2. API проверка лицензии для AHK
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

# 3. Страница администратора
@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, key: str = ""):
    if key != ADMIN_PASSWORD:
        return HTMLResponse(content="<h2>Доступ запрещен. Неверный ключ администратора.</h2>", status_code=403)
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT hwid, note, is_active FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "key": key})

# 4. Добавление или обновление пользователя
@app.post("/admin/add")
def add_user(key: str = Form(...), hwid: str = Form(...), note: str = Form(...)):
    if key != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (hwid, note, is_active) VALUES (?, ?, 1)", (hwid.strip(), note.strip()))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"/admin?key={key}", status_code=303)

# 5. Переключение статуса (Блокировка / Активация)
@app.post("/admin/toggle")
def toggle_user(key: str = Form(...), hwid: str = Form(...)):
    if key != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE hwid = ?", (hwid,))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"/admin?key={key}", status_code=303)

# 6. Удаление пользователя
@app.post("/admin/delete")
def delete_user(key: str = Form(...), hwid: str = Form(...)):
    if key != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE hwid = ?", (hwid,))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"/admin?key={key}", status_code=303)
