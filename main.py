from fastapi import FastAPI, Depends,Request
import requests
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
import models
from pydantic import BaseModel;
from twelvedata import TDClient
from datetime import datetime, timedelta
from database import SessionLocal, engine
import joblib
import numpy as np
import tensorflow as tf

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
phash = CryptContext(schemes=["bcrypt"], deprecated="auto")
scheduler = BackgroundScheduler()
origins = [
    "https://aiforexpredictor.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

td = TDClient(apikey="f00c068b148d4b98808601c219e1260e")
SECRET_KEY = "k0rrscb0cggasdada1c219e1260e"
ALGORITHM = "HS256"
lstm_model = tf.keras.models.load_model("Forex_Model.keras")
scaler = joblib.load("scaler.save")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

class Prediction(BaseModel):
    date: str
    open_time: str
    close_time: str

@app.post("/predict")
async def predict(data: Prediction,r:Request,db:Session=Depends(get_db)):
    auth_header = r.headers.get("Authorization")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        cformat=changedatetimeformat(data.date,data.open_time)
        ohlc =get_past_24h_ohlc(cformat["date"],cformat["open_time"])
        predictedclose=predictclose(ohlc)
        openat=ohlc[23][0]
        trend=findtrend(openat,predictedclose)
        hdetails = models.Historyfalse(
            user_id=username,
            date=data.date,
            open_at=openat,
            close_at=predictedclose,
            open_time=data.open_time,
            close_time=data.close_time,
            predicted_trend=trend
        ) 
        db.add(hdetails)   
        db.commit()       
        db.refresh(hdetails)
        return {"open": openat,"close":predictedclose,"trend":trend}
    except JWTError:
        return {"status": False}

@app.post("/history")
def gethistory(r:Request,db:Session=Depends(get_db)):
    auth_header = r.headers.get("Authorization")
    if not auth_header:
        return [] 
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        historytrue = db.query(models.Historytrue).filter(models.Historytrue.user_id == username).all()
        historyfalse = db.query(models.Historyfalse).filter(models.Historyfalse.user_id == username).all()
        res = []
        for h in historytrue:
            res.append({
            "date": h.date,
            "open_at": h.open_at,
            "close_at": h.close_at,
            "open_time": h.open_time,
            "close_time": h.close_time,
            "predicted_trend": h.predicted_trend,
            "actual_trend": h.actual_trend
            })
        for h in historyfalse:
            res.append({
            "date": h.date,
            "open_at": h.open_at,
            "close_at": h.close_at,
            "open_time": h.open_time,
            "close_time": h.close_time,
            "predicted_trend": h.predicted_trend,
            "actual_trend": h.actual_trend
            })
        return res
    except JWTError:
        return {"status": False}

class Signup(BaseModel):
    username:str
    password:str

@app.post("/signup")
def signup(s:Signup,db:Session=Depends(get_db)):
    user=db.query(models.User).filter(models.User.username==s.username).first()
    if(user):
        return{"status":False,"message":"Username already exist"}
    hpass=hash_password(s.password)
    data=models.User(
        username=s.username,
        password=hpass
    )
    db.add(data)
    db.commit()
    db.refresh(data)
    return{"status":True}

class Login(BaseModel):
    username:str
    password:str

@app.post("/login")
def login(l:Login,db: Session = Depends(get_db)):
    user=db.query(models.User).filter(models.User.username==l.username).first()
    if(user):
        if verify_password(l.password,user.password):
            token=jwt.encode({"username":l.username},SECRET_KEY,algorithm=ALGORITHM)
            return{"status":True,"token":token}
        else:
            return{"status":False,"message":"Invalid Credentials"}
    else:
        return{"status":False,"message":"Invalid Credentials"}

@app.post("/protected")
async def protected(request: Request,db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"status": False}

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if not username:
            return {"status": False}
        print("auth user")
        return {"status": True}
    except JWTError:
        return {"status": False}
    
def predictclose(ohlc):
    n_input = np.array(ohlc)

    new_scaled = scaler.transform(n_input).reshape(1,n_input.shape[0], 4)

    prediction = lstm_model.predict(new_scaled)

    predicted_full = scaler.inverse_transform(np.concatenate((np.zeros((1, 3)), prediction), axis=1))

    predicted_bc = predicted_full[0, -1]

    return f"{predicted_bc:.5f}"

def get_past_24h_ohlc(date_str, time_str):


    end_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")


    ts = td.time_series(
        symbol="EUR/USD",
        interval="1h",      
        timezone="Asia/Kolkata",
        end_date=end_str,
        order="asc",
        outputsize=24
    ).as_json()


    ni = []
    for candle in ts:
        o = float(candle['open'])
        h = float(candle['high'])
        l = float(candle['low'])
        c = float(candle["close"])
        ni.append([o, h, l, c])

    return ni


def changedatetimeformat(date,opentime):
    date_obj = datetime.strptime(date, "%a %b %d %Y")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    open_time_obj = datetime.strptime(opentime, "%I:%M:%S %p")
    formatted_open_time = open_time_obj.strftime("%H:%M:%S")
    return{
        "date":formatted_date,
        "open_time":formatted_open_time,
    }

def closetimeformat(closetime):
    close_time_obj = datetime.strptime(closetime, "%I:%M:%S %p")
    formatted_close_time = close_time_obj.strftime("%H:%M:%S")
    return{
        "close_time":formatted_close_time
    }    

def findtrend(openprice: str, closeprice: str) -> str:
    open_val = float(openprice)
    close_val = float(closeprice)
    if open_val == close_val:
        return "NEUTRAL"
    elif open_val > close_val:
        return "BEAR"
    else:
        return "BULL"



def historyupdate():
    res = requests.post("https://aiforexpredictor.vercel.app/")
    db = SessionLocal()
    now = datetime.now()
    histories = db.query(models.Historyfalse).all()
    updated_count = 0
    for h in histories:

        history_dt_str = f"{h.date} {h.close_time}"

        history_dt = datetime.strptime(history_dt_str, "%a %b %d %Y %I:%M:%S %p")

        if history_dt < now:
            date=h.date
            time=h.close_time
            cformat=changedatetimeformat(date,time)
            ohlc =get_past_24h_ohlc(cformat["date"],cformat["open_time"])
            openat=h.open_at
            closeat=ohlc[23][3]
            trend=findtrend(openat,closeat)
            htruedetails = models.Historytrue(
            user_id=h.user_id,
            date=h.date,
            open_at=h.open_at,
            close_at=h.close_at,
            open_time=h.open_time,
            close_time=h.close_time,
            predicted_trend=h.predicted_trend,
            actual_trend=trend
            )
            db.add(htruedetails)
            db.delete(h)
            updated_count += 1

    db.commit()
    db.close()
    print(f"update success :{updated_count},{res}")

scheduler.add_job(historyupdate, "interval", minutes=1) 
scheduler.start()

def hash_password(password: str) -> str:
    return phash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return phash.verify(plain_password, hashed_password)