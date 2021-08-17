from app import app
from flask import render_template, request, redirect
import users, recipes

@app.route("/search", methods=["POST"])
def search_name():
    name = request.form["search_name"]
    result = recipes.search_by_name(name)
    return render_template("results.html", recipes=result, search_term=name)

# @app.route("/results", methods=["GET"])
# def show_results():
#     return render_template("results.html", recipes=)

@app.route("/delete_recipe/<int:id>", methods=["POST"])
def delete_recipe(id):
    if recipes.delete_recipe(id):
        return redirect("/")
    else:
        return render_template("error.html", message="Reseptin poistaminen epäonnistui.")

@app.route("/<int:user_id>/modify/<int:id>", methods=["GET"])
def show_modify(user_id, id):
    if users.user_id() == user_id:
        recipe_name = recipes.get_name(id)
        old_ingredients = recipes.get_ingredients(id)
        old_instructions = recipes.get_instructions(id)
        return render_template("modify.html", name=recipe_name, id=id, old_ingredients=old_ingredients, old_instructions=old_instructions)
    else:
        return render_template("error.html", message="Ei ole oma reseptisi.")

@app.route("/modify_name/<int:id>", methods=["POST"])
def modify_name(id):
    name = request.form["name"]
    if name.strip() == "":
        return render_template("error.html", message="Reseptillä pitää olla nimi.")
    elif recipes.change_name(id, name):
        return redirect("/profile/recipes/"+str(id))
    else:
        return render_template("error.html", message="Nimen vaihtaminen ei onnisutnut.")

@app.route("/modify_ingredients/<int:id>", methods=["POST"])
def modify_ingredients(id):
    new_ingredients = request.form["ingredients"]
    if recipes.change_ingredients(id, new_ingredients):
        return redirect("/profile/recipes/"+str(id))
    else:
        return render_template("error.html", message="Ei onnistunut. Syötä uudet raaka-aineet muodossa raaka-aine;numero;raaka-aine")

@app.route("/modify_instructions/<int:id>", methods=["POST"])
def modify_instructions(id):
    instructions = request.form["instructions"]
    if instructions.strip() == "":
        return render_template("error.html", message="Reseptillä pitää olla ohjeet.")
    elif recipes.change_instructions(id, instructions):
        return redirect("/profile/recipes/"+str(id))
    else:
        return render_template("error.html", message="Ei onnistunut")

@app.route("/<int:id>/newrecipe", methods=["GET"])
def newrecipe(id):
    if users.user_id() == id:
        return render_template("newrecipe.html")
    else:
        return render_template("error.html", message="Kirjaudu sisään.")

@app.route("/create_recipe", methods=["POST"])
def send():
    name = request.form["name"]
    if name.strip() == "":
        return render_template("error.html", message="Reseptillä pitää olla nimi.")
    ingredients_text = request.form["ingredients"]
    if ingredients_text == "":
        return render_template("error.html", message="Reseptillä pitää olla ainakin yksi ainesosa.")
    steps = request.form["instructions"]
    if steps.strip() == "":
        return render_template("error.html", message="Reseptillä pitää olla ohjeet.")
    recipe_id = recipes.create(name, ingredients_text, steps)
    if recipe_id is not None:
        return redirect("/profile/recipes/"+str(recipe_id))
    else:
        return render_template("error.html", message="Reseptin luominen epäonnistui. Tarkista raaka-aineiden kirjoitusasu.")


@app.route("/profile/recipes/<int:id>", methods=["GET"])
def show_recipe(id):
    allow = False
    user_id  = users.user_id()
    if user_id == recipes.get_user_id(id):
        allow = True
    if not allow:
        return render_template("error.html", message="Ei kuulu omiin resepteihisi.")

    name = recipes.get_name(id)
    ingredients = recipes.get_ingredients(id)
    instructions = recipes.get_instructions(id)
    return render_template("recipe.html", name=name, ingredients=ingredients, instructions=instructions, user_id=user_id , id=id)

@app.route("/")
def index():
    recipes_list = recipes.get_own_recipes()
    user_id = users.user_id()
    return render_template("index.html", own_recipes=recipes_list, user_id=user_id)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST": 
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("error.html", message="Salasanat eivät täsmää.")
        if users.register(username, password1):
            return redirect("/")
        else:
            return render_template("error.html", message="Rekisteröinti ei onnistunut")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("error.html", message="Väärä tunnus tai salasana")

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")