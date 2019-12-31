import datetime
import dataset
import json
import sys
import time

from starlette.applications import Starlette
from starlette.config import Config
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
import uvicorn


# Configuration from environment variables or '.env' file.
config = Config('.env')
DATABASE_URL = config('DATABASE_URL')

version = f"{sys.version_info.major}.{sys.version_info.minor}"
templates = Jinja2Templates(directory='templates')
db = dataset.connect(DATABASE_URL)


def startup():
    print('Ready to go')


def get_items(table):
    items = []
    for item in db[table]:
        items.append(item)
    return items


app = Starlette(debug=True, on_startup=[startup])
app.mount('/static', StaticFiles(directory='statics'), name='static')


@app.route('/')
async def homepage(request):
    template = "index.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context)


@app.route("/msg")
async def message(request):
    message = f"Hello world! From Starlette running on Uvicorn with Gunicorn in Alpine."
    return JSONResponse({"message": message, "version": version})


@app.route('/dt')
async def my_date_time(request):
    print(datetime.datetime.now())
    return JSONResponse({'hello': 'world', 'now': str(datetime.datetime.now())})


# contact rest api methods

@app.route('/api/contact')
async def get_contact(request):
    return JSONResponse(get_items('contacts'))


@app.route('/api/contact/{item_id}')
async def get_contact_by_id(request):
    cid = request.path_params['item_id']
    contact = db['contacts'].find_one(id=cid)
    return JSONResponse(contact)


@app.route('/api/contact/{item_id}', methods=['PUT'])
async def update_contact_by_id(request):
    cid = request.path_params['item_id']
    req_body = await request.json()
    # data = dict(id=fid, type=req_body.type, count=req_body.count)
    data = dict(id=cid,
                firstName=req_body["firstName"],
                lastName=req_body["lastName"],
                email=req_body["email"],
                company=req_body["company"],
                phone=req_body["phone"],
                creationTime=req_body["creationTime"])

    count = db['contacts'].update(data, ['id'])
    contact = db['contacts'].find_one(id=cid)
    return JSONResponse(contact)


@app.route('/api/contact/{item_id}', methods=['DELETE'])
async def delete_contact_by_id(request):
        fid = request.path_params['item_id']
        cnt = db['contacts'].delete(id=fid)
        return JSONResponse(get_items('contacts'))


@app.route('/api/contact', methods=['POST'])
async def post_contact(request):
    new_contact = await request.json()
    new_contact['creationTime'] = int(time.time())
    print(f"new contact: {new_contact}")
    contact_table = db['contacts']
    contact_table.insert(new_contact)
    return JSONResponse({"created": "ok"})

@app.route('/error')
async def error(request):
    """
    An example error. Switch the `debug` setting to see either tracebacks or 500 pages.
    """
    raise RuntimeError("Oh no")


@app.exception_handler(404)
async def not_found(request, exc):
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=404)


@app.exception_handler(500)
async def server_error(request, exc):
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
