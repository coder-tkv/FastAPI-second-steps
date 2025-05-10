import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

books = [
    {
        'id': 1,
        'title': 'Асинхронность в Python',
        'author': 'Мэттью'
    },
    {
        'id': 2,
        'title': 'Backend разработка в Python',
        'author': 'Егор'
    }
]


class BookSchema(BaseModel):
    title: str
    author: str


@app.get('/books', tags=['Книги 📚'], summary='Получить все книги')
async def read_books():
    return books


@app.get('/books/{book_id}', tags=['Книги 📚'], summary='Получить конкретную книгу')
async def get_book(book_id: int):
    for book in books:
        if book['id'] == book_id:
            return book
    raise HTTPException(status_code=404, detail='Книга не найдена')


@app.post('/books', tags=['Книги 📚'])
async def create_book(new_book: BookSchema):
    books.append({
        'id': len(books) + 1,
        'title': new_book.title,
        'author': new_book.author
    })
    return {'success': True, 'message': 'Книга успешно добавлена'}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
