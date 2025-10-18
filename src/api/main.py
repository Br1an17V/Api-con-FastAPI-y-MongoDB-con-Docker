from datetime import date, datetime
from fastapi import FastAPI, HTTPException
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel as Basemodel
from typing import List

class Libro(Basemodel):
    titulo: str
    autor: str
    isbn: str
    editorial: str
    fecha: date # YYYY-MM-DD

app = FastAPI()


MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["testdb"]


@app.get("/")
async def root():
    return {"ok": True, "Colecciones": await db.list_collection_names()}

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["biblioteca"]

# Endpoint para listar todos los libros
@app.get("/libros", response_description="Lista de libros", response_model=List[Libro])
async def list_libros():
    libros = await db["libros"].find().to_list(100)
    return libros

# Endpoint para crear un nuevo libro
@app.post("/libros", response_description="Agregar un nuevo libro", response_model=Libro)
async def create_libro(libro: Libro):
    libro_dict = libro.dict()
    libro_dict["fecha"] = datetime.combine(libro_dict["fecha"], datetime.min.time())
    await db["libros"].insert_one(libro_dict)
    return libro # si quieres ver todos los libros sería return await list_libros()

# Endpoint para obtener los datos de un libro por su ISBN
@app.get("/libro/{isbn}", response_description="Obtener un libro por su ISBN", response_model=Libro)
async def find_by_isbn_libro(isbn: str):
    libro = await db["libros"].find_one({"isbn": isbn})
    if libro is not None:
        return libro
    else:
        raise HTTPException(status_code=404, detail={"error": "Libro no encontrado"})

# Endpoint para borrar un libro por su ISBN
@app.delete("/libro/{isbn}", response_description="Borrar un libro por su ISBN")
async def delete_libro(isbn: str):
    delete_result = await db["libros"].delete_one({"isbn": isbn})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail={"error": "Libro no encontrado"})
    else:
        return {"ok": True, "message": "Libro borrado con éxito"}
    
# Endpoint para actualizar (reemplazo) un libro por su ISBN (permite cambiar el ISBN)
@app.put("/libro/{isbn}", response_description="Actualizar un libro por su ISBN", response_model=Libro)
async def update_libro(isbn: str, libro: Libro):
    # Igual que en create: convertimos date -> datetime para Mongo
    libro_dict = libro.dict()
    libro_dict["fecha"] = datetime.combine(libro_dict["fecha"], datetime.min.time())

    # Actualizamos por el ISBN de la ruta, pero seteamos TODOS los campos del body (incluido el nuevo isbn)
    result = await db["libros"].update_one({"isbn": isbn}, {"$set": libro_dict})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail={"error": "Libro no encontrado"})
    else:
        # Devolvemos el modelo que enviaste (con fecha como date)
        return libro
