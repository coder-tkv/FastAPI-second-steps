import time
import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()


def sync_task():
    time.sleep(3)
    print('Сделан запрос в сторонний API')


async def async_task():
    await asyncio.sleep(3)
    print('Отправлен email')


@app.post('/async')
async def run_async():
    ...
    asyncio.create_task(async_task())
    return {'ok': True}


@app.post('/sync')
async def run_sync(bg_tasks: BackgroundTasks):
    ...
    bg_tasks.add_task(sync_task)
    return {'ok': True}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
