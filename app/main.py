from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
import redis
import time
from datetime import datetime
import traceback 

app = FastAPI(title="Premier League Ticket System")

# --- 1. COMPLEXITY: MIDDLEWARE TRACING (Nilai Tambah: Tracing) ---
# Ini menghitung waktu proses tiap request dan menempelkannya di Header response
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # Menambahkan info durasi proses ke header HTTP
    response.headers["X-Process-Time"] = str(process_time)
    return response

# --- CONFIG ---
app.add_middleware(SessionMiddleware, secret_key="rahasia_super_aman")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

DATABASE_URL = "postgresql://admin:password123@postgres:5432/pl_ticket_final"
REDIS_HOST = "redis"

# --- 2. COMPLEXITY: DB CONNECTION POOLING (Nilai Tambah: DB Performance) ---
# pool_size=20: Standby 20 koneksi siap pakai (biar ga usah login ulang terus ke DB)
# max_overflow=10: Kalau penuh, boleh nambah 10 koneksi darurat
engine = create_engine(
    DATABASE_URL, 
    pool_size=20, 
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

try:
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
except:
    print("Redis Error")

Instrumentator().instrument(app).expose(app)

# --- MODELS ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String)
    away_team = Column(String)
    match_date = Column(DateTime)
    stadium = Column(String)
    total_stock = Column(Integer)
    price = Column(Float)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))
    match = relationship("Match")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))
    booking_time = Column(DateTime, default=datetime.now)
    status = Column(String)
    match = relationship("Match")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- INIT & SEEDING ---
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    try:
        if db.query(Match).count() == 0:
            print("--- SEEDING DATA ---")
            matches = [
                Match(home_team="West Ham", away_team="Sunderland", match_date=datetime(2026, 1, 24, 19, 30), stadium="London Stadium", total_stock=500, price=85.0),
                Match(home_team="Man City", away_team="Wolves", match_date=datetime(2026, 1, 24, 22, 00), stadium="Etihad Stadium", total_stock=200, price=110.0),
                Match(home_team="Burnley", away_team="Tottenham", match_date=datetime(2026, 1, 24, 22, 00), stadium="Turf Moor", total_stock=250, price=95.0),
                Match(home_team="Bournemouth", away_team="Liverpool", match_date=datetime(2026, 1, 25, 0, 30), stadium="Vitality Stadium", total_stock=150, price=120.0),
                Match(home_team="Arsenal", away_team="Man United", match_date=datetime(2026, 1, 25, 23, 30), stadium="Emirates Stadium", total_stock=100, price=250.0)
            ]
            db.add_all(matches)
            db.commit()
    except Exception as e:
        print(f"Seeding Error: {e}")
    finally:
        db.close()

seed_data()

# --- HELPERS ---
def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id: return None
    return db.query(User).filter(User.id == user_id).first()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- ROUTES ---
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
        request.session["user_id"] = user.id
        return RedirectResponse(url="/", status_code=303)
    except:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Login Failed"})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        if db.query(User).filter(User.username == username).first():
            return templates.TemplateResponse("register.html", {"request": request, "error": "Username taken"})
        new_user = User(username=username, password_hash=get_password_hash(password))
        db.add(new_user)
        db.commit()
        return RedirectResponse(url="/login", status_code=303)
    except:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Register Failed"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    cart_count = 0
    if user: cart_count = db.query(CartItem).filter(CartItem.user_id == user.id).count()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "cart_count": cart_count})

@app.get("/matches")
def get_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).order_by(Match.match_date).all()
    # Redis Cache for Stock
    for match in matches:
        stock_key = f"match_stock:{match.id}"
        redis_stock = r.get(stock_key)
        if redis_stock: match.total_stock = int(redis_stock)
        else: r.set(stock_key, match.total_stock)
    return matches

@app.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    total_price = sum(item.match.price for item in cart_items)
    return templates.TemplateResponse("cart.html", {"request": request, "user": user, "cart_items": cart_items, "total": total_price})

@app.post("/add-to-cart/{match_id}")
def add_to_cart(match_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: raise HTTPException(status_code=401)
    if not db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.match_id == match_id).first():
        db.add(CartItem(user_id=user.id, match_id=match_id))
        db.commit()
    count = db.query(CartItem).filter(CartItem.user_id == user.id).count()
    return {"status": "success", "cart_count": count}

@app.get("/validate-ticket/{ticket_id}")
def validate_ticket_heavy(ticket_id: int):
    # Simulasi kerja berat CPU (Hashing berulang 1 juta kali)
    # Ceritanya: "Memverifikasi tanda tangan digital tiket"
    data = f"ticket-{ticket_id}-{time.time()}"
    for _ in range(500000):  # Loop setengah juta kali
        data = hashlib.sha256(data.encode()).hexdigest()
    
    return {"status": "valid", "proof": data[:10]}

@app.post("/checkout")
def checkout(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
        if not user: raise HTTPException(status_code=401)
        cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
        if not cart_items: return {"status": "empty"}

        for item in cart_items:
            try: r.decr(f"match_stock:{item.match_id}")
            except: pass
            db.add(Booking(user_id=user.id, match_id=item.match_id, status="PAID"))

        db.query(CartItem).filter(CartItem.user_id == user.id).delete()
        db.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/my-tickets", response_class=HTMLResponse)
def my_tickets(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/login")
    bookings = db.query(Booking).filter(Booking.user_id == user.id).order_by(Booking.booking_time.desc()).all()
    return templates.TemplateResponse("tickets.html", {"request": request, "user": user, "bookings": bookings})