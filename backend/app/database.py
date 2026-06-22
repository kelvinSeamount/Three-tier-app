from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load variables from a local .env file (if present) into the environment.
load_dotenv()

# The DATABASE_URL is the "address" of our pantry.
# We read it from an environment variable (Kubernetes will inject this).
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/appdb")

# The engine is the "delivery truck" that physically moves data between
# our app and the database.
engine = create_engine(DATABASE_URL)

# A SessionLocal is like opening a notepad to write down an order.
# Each request gets its own notepad, uses it, then closes it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the "template" all our database table classes will inherit from.
Base = declarative_base()

# This is a "dependency" — FastAPI will call this to get a DB session
# for each request, then automatically close it when done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
