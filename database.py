from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

password = quote_plus("Ashwin@01012004") 
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://root:{password}@localhost:3306/forexprediction"


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
