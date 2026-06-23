from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
import co2meter as co2
import asyncio
from typing import Annotated
from pydantic import BaseModel

type monitor_type = tuple[datetime, int, float] | None

class MonitorData(BaseModel):
    datatime: datetime
    ppm: int
    temperature: float

class Monitor: 
    _data: monitor_type = None
    _is_loop: bool = True

    @classmethod
    async def loop(cls):
        while cls._is_loop:
            try: 
                mon = co2.CO2monitor(bypass_decrypt=True)
                # type: ignore
                cls._data = mon.read_data(max_requests=200)
            finally:
                await asyncio.sleep(15)

    @classmethod
    def stop_loop(cls):
        cls._is_loop = False

    @classmethod
    def get_data(cls) -> tuple[datetime, int, float]:
        if cls._data is None:
            raise Exception()
        return cls._data

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(Monitor.loop())

    yield
    # cleanup
    Monitor.stop_loop()
    await task

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def get_monitor(data: Annotated[monitor_type, Depends(Monitor.get_data)]) -> MonitorData:
    assert data is not None
    return MonitorData(datatime=data[0], ppm=data[1], temperature=data[2])
