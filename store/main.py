from typing import List, Set
from sqlalchemy import Table, Column, Integer, String, Float, DateTime, create_engine, MetaData, select
from config import *
from schema import *
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, HTTPException, Depends
import json
from starlette.websockets import WebSocket, WebSocketDisconnect

DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

app = FastAPI()

subscriptions: Set[WebSocket] = set()

processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.remove(websocket)


async def send_data_to_subscribers(data):
    for websocket in subscriptions:
        await websocket.send_json(json.dumps(data))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI CRUDL endpoints
@app.post("/processed_agent_data/")
async def create_processed_agent_data(data: ProcessedAgentData, db: Session = Depends(get_db)):
    try:
        if not db.is_active:
            raise HTTPException(status_code=500, detail="Database connection is not active")

        road_state = data.road_state
        user_id = data.agent_data.user_id
        accelerometer = data.agent_data.accelerometer
        gps = data.agent_data.gps
        timestamp = data.agent_data.timestamp

        query = processed_agent_data.insert().values(
            road_state=road_state,
            user_id=user_id,
            x=accelerometer.x,
            y=accelerometer.y,
            z=accelerometer.z,
            latitude=gps.latitude,
            longitude=gps.longitude,
            timestamp=timestamp
        )
        db.execute(query)
        db.commit()
        return {"message": "Data created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processed_agent_data/", response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data(db: Session = Depends(get_db)):
    try:
        processed_agent_data_ = db.query(processed_agent_data).all()
        return processed_agent_data_
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int, db: Session = Depends(get_db)):
    try:
        statement = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        result = db.execute(statement)
        data = result.fetchone()

        if not data:
            raise HTTPException(status_code=404, detail="Data not found")

        return ProcessedAgentDataInDB(
            id=data[0],
            road_state=data[1],
            user_id=data[2],
            x=data[3],
            y=data[4],
            z=data[5],
            latitude=data[6],
            longitude=data[7],
            timestamp=data[8]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData, db: Session = Depends(get_db)):
    try:
        # Отримуємо дані для оновлення з бази даних
        statement = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        result = db.execute(statement)
        existing_data = result.fetchone()

        if not existing_data:
            raise HTTPException(status_code=404, detail="Data not found")

        update_data = {
            "road_state": data.road_state,
            "user_id": data.agent_data.user_id,
            "x": data.agent_data.accelerometer.x,
            "y": data.agent_data.accelerometer.y,
            "z": data.agent_data.accelerometer.z,
            "latitude": data.agent_data.gps.latitude,
            "longitude": data.agent_data.gps.longitude,
            "timestamp": data.agent_data.timestamp
        }

        update_statement = (
            processed_agent_data.update()
            .where(processed_agent_data.c.id == processed_agent_data_id)
            .values(**update_data)
        )
        db.execute(update_statement)
        db.commit()

        # Повертаємо оновлені дані
        return ProcessedAgentDataInDB(
            id=processed_agent_data_id,
            road_state=update_data["road_state"],
            user_id=update_data["user_id"],
            x=update_data["x"],
            y=update_data["y"],
            z=update_data["z"],
            latitude=update_data["latitude"],
            longitude=update_data["longitude"],
            timestamp=update_data["timestamp"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int, db: Session = Depends(get_db)):
    try:
        statement = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        result = db.execute(statement)
        data_to_delete = result.fetchone()

        if not data_to_delete:
            raise HTTPException(status_code=404, detail="Data not found")

        delete_statement = processed_agent_data.delete().where(processed_agent_data.c.id == processed_agent_data_id)
        db.execute(delete_statement)
        db.commit()

        return ProcessedAgentDataInDB(
            id=data_to_delete[0],
            road_state=data_to_delete[1],
            user_id=data_to_delete[2],
            x=data_to_delete[3],
            y=data_to_delete[4],
            z=data_to_delete[5],
            latitude=data_to_delete[6],
            longitude=data_to_delete[7],
            timestamp=data_to_delete[8]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
