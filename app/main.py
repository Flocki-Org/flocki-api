from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def index():
    return 'Hello this is the first endpoint of the flocki-api'

