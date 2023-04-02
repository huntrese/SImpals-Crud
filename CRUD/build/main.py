from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from starlette_graphene3 import GraphQLApp
from pydantic import BaseModel
import graphene
from mongoengine import Document, StringField
from graphene_mongo import MongoengineObjectType
import os
import datetime
from pymongo import MongoClient

class UserModel(Document):
    Name = StringField(required=True)
    Surname = StringField(required=True)

class User(MongoengineObjectType):
    class Meta:
        model = UserModel

class Query(graphene.ObjectType):
    users = graphene.List(User)

    def resolve_users(self, info):
        return UserModel.objects.all()

schema = graphene.Schema(query=Query)

app = FastAPI()

app.add_route('/graphql', GraphQLApp(schema=schema), name='graphql')

client = MongoClient("mongodb://mongodb:27017")

db = client["Persons"]
collections = db["important"]


def next():
    ind = list(collections.find({}))
    if ind != []:
        return int(ind[-1]["_id"]) + 1
    else:
        return 0

def makeTable():
    data = collections.find({})
    # print(list(data))
    response = "<table><th>Id</th><th>Name</th><th>Surname</th><th>Date created</th><th>Last Updated</th><th>Actions</th><th></th>"
    for i in data:
        response += "<tr>"
        for j in i:
            response += "<td>" + str(i[j]) + "</td>"
        response += '<td><form method="GET" action="/update.php"><button class="edit-button" type="submit" name="user_id" value="' + str(i["_id"]) + '">Edit</button></form></td>'
        response += '<td><form method="POST" action="/data.php"><input type="hidden" name="user_id" value="' + str(i["_id"]) + '"/><input type="hidden" name="action" value="delete"/><button class="delete-button" type="submit">Delete user</button></form></td>'
        response += "</tr>"
    response += "</table>"

    return response


class Person(BaseModel):
    name: str
    surname: str


@app.get("/index.php")
async def index():
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"index.html"))) as f:
        home_data = f.read()
    return HTMLResponse(content=home_data)


@app.post("/index.php")
async def submit(request: Request, person: Person = Depends(lambda: Person(name="", surname=""))):
    form_data = await request.form()
    name = form_data.get('name', '')
    surname = form_data.get('surname', '')
    if name:
        person.name = name
    if surname:
        person.surname = surname
    document = {"_id": int(next()), "name": person.name, "surname": person.surname, "date created": str(datetime.datetime.today()), "last updated": str(datetime.datetime.today())}
    collections.insert_one(document)
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"index.html"))) as f:
        home_data = f.read()
    return HTMLResponse(content=home_data)
    

@app.get("/data.php")
async def index():
    table = makeTable()
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"data.html"))) as f:
        base_data = f.read()
    base_data = base_data.replace("%s", table)
    return HTMLResponse(content=base_data)

@app.post("/data.php")
async def delete_or_edit_user(request: Request, user_id: str = Form(None), action: str = Form(None)):
    if action == "delete":
        print(user_id,type(user_id))
        # Delete the user with the given ID from the database
        result = collections.delete_one({'_id': int(user_id)})
        if result.deleted_count == 0:
            return {'error': 'User not found'}
    elif action == "edit":
        # Redirect to update.html with the user ID included as a query parameter
        with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"index.html"))) as f:
            home_data = f.read()
        return HTMLResponse(content=base_data)
    
    # Reload the page to see the updated user list
    table = makeTable()
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"data.html"))) as f:
        base_data = f.read()
    base_data = base_data.replace("%s", table)
    return HTMLResponse(content=base_data)




@app.get("/update.php")
async def get_update_user(request: Request,user_id: str):
    print("CC",user_id)

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "update.html"))) as f:
        base_data = f.read()
        base_data=base_data.replace("{{ user_id }}",user_id)
    return HTMLResponse(content=base_data)


@app.post("/update.php")
async def update_user(request: Request):
    form = await request.form()
    user_id = form.get("user_id")
    name = form.get("name")
    surname = form.get("surname")

    print(user_id,name,surname)
    update_fields = {}
    if name:
        update_fields['name'] = name
    if surname:
        update_fields['surname'] = surname

    if update_fields:
        data = collections.find()
        for i in data:
            print(i)

        result = collections.update_one({'_id': int(user_id)}, {"$set": update_fields})
        # res1=collections.find({'_id':user_id})
        print(result.matched_count)
        
        # for i in res1:
        #     print(i)
        if result.modified_count == 0:
            return {"error": "User not found"}

    table = makeTable()
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__),"data.html"))) as f:
        base_data = f.read()
    base_data = base_data.replace("%s", table)
    return HTMLResponse(content=base_data)
    

