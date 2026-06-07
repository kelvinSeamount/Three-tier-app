from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, auth
from .database import engine, get_db

# This line creates all database tables on startup.
# Like a chef arriving in the morning and setting up all the prep stations.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="3-Tier Auth API", version="1.0.0")

# CORS = Cross-Origin Resource Sharing.
# Without this, your browser would BLOCK the React app (port 3000) from
# talking to FastAPI (port 8000). It's like a bouncer who only lets in
# guests from the approved guest list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod, replace with your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Kubernetes will call this to know if the app is alive."""
    return {"status": "healthy"}

@app.post("/auth/signup", response_model=schemas.UserResponse, status_code=201)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    The signup counter at the restaurant entrance.
    Takes your name, checks you're not already registered, then adds you to the book.
    """
    # Check if username or email already taken
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password before saving — NEVER save raw passwords
    hashed_pw = auth.hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    The front door check-in. You show your ID (email + password).
    If valid, you get a wristband (JWT token) to use for the rest of the night.
    """
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    A protected route. Show your wristband, get your profile back.
    The frontend calls this to confirm the token is still valid.
    """
    return current_user

@app.post("/auth/logout")
def logout():
    """
    With JWT, logout is handled CLIENT-SIDE (the frontend just deletes the token).
    This endpoint exists for completeness / future token blacklisting.
    """
    return {"message": "Logged out successfully. Delete your token on the client."}
