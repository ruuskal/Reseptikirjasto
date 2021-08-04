from app import app
from flask import render_template, request, redirect
import users, recipes


@app.route("/newrecipe")
def newrecipe():
    return render_template("newrecipe.html")

@app.route("/send", methods=["POST"])
def send():
    name = request.form["name"]
    ingredients_text = request.form["ingredients"]
    steps = request.form["instructions"]
    recipe_id = recipes.create(name, ingredients_text, steps)
    if recipe_id is not None:
        return redirect("/profile/recipes/"+str(recipe_id))
    else:
        return render_template("error.html", message="Reseptin luominen epäonnistui.")

@app.route("/profile/recipes/<int:id>")
def show_recipe(id):
    allow = False
    if users.user_id() == recipes.get_user_id(id):
        allow = True
    if not allow:
        return render_template("error.html", message="Ei kuulu omiin resepteihisi.")

    name = recipes.get_name(id)
    ingredients = recipes.get_ingredients(id)
    instructions = recipes.get_instructions(id)
    return render_template("recipe.html", name=name, ingredients=ingredients, instructions=instructions)

@app.route("/")
def index():
    recipes_list = recipes.get_own_recipes()
    return render_template("index.html", own_recipes=recipes_list)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html") # palauttaa sivun uuden tunnuksen tekemiseen
    if request.method == "POST": 
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("error.html", message="Passwords don't match.")
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