from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

# password = quote_plus("Ashwin@01012004") 
engine = create_engine(
    "mysql+mysqlconnector://B4eBKyw6HzmNeYc.root:01CceXjf0EhDag6d@gateway01.us-east-1.prod.aws.tidbcloud.com:4000/forexprediction",
    connect_args={
        "ssl_ca": r"C:\Forexprediction\forex_ser\ca.pem",
        "ssl_verify_cert": True,
        "ssl_verify_identity": True
    }
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
