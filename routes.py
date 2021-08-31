from app import app
from flask import render_template, request, redirect
import users, recipes

@app.route("/stars/<int:id>", methods=["POST"])
def rate(id):
    users.check_csrf()
    try: 
        stars = int(request.form["stars"])
    except ValueError:
        return render_template("error.html", message="Arvion on oltava kokonaisluku väliltä 1-5")
    if 1 < stars > 5:
        return render_template("error.html", message="Arvion on oltava kokonaisluku väliltä 1-5")
    user_id=users.user_id()
    recipes.give_stars(id, stars, user_id)
    return redirect("/recipes/"+str(id))

@app.route("/delete_from_library/<int:recipe_id>", methods=["POST"])
def delete_from_library(recipe_id):
    users.check_csrf()
    user_id = users.user_id()
    recipes.delete_from_library(user_id, recipe_id)
    return redirect("/")

@app.route("/add_note/<int:recipe_id>", methods=["POST"])
def add_note(recipe_id):
    users.check_csrf()
    user_id = users.user_id()
    id = recipes.get_library_id(user_id, recipe_id)
    content = request.form["note"]
    recipes.create_note(content, id)
    return redirect("/recipes/"+str(recipe_id))


@app.route("/public_recipes", methods=["GET"])
def public_recipes():
    if users.user_id() == 0:
        return render_template("error.html", message="Et ole kirjautunut sisään.")
    else:
        id = users.user_id()
        public_recipes = recipes.get_public_recipes(id)
        return render_template("public_recipes.html", public_recipes=public_recipes)

@app.route("/add_to_library/<int:id>", methods=["POST"])
def add_recipe(id):
    users.check_csrf()
    user_id = users.user_id()
    if recipes.add_to_library(user_id, id):
        return redirect("/")
    else:
        return render_template("error.html", message="Reseptin lisäys omaan kirjastoon epäonnistui.")

@app.route("/search_ingredient", methods=["POST"])
def search_ingredient():
    users.check_csrf()
    ingredient = request.form["search_ingredient"]
    result = recipes.search_by_ingredient(ingredient)
    return render_template("results.html", recipes=result, search_term=ingredient)

@app.route("/search", methods=["POST"])
def search_name():
    users.check_csrf()
    name = request.form["search_name"]
    result = recipes.search_by_name(name)
    return render_template("results.html", recipes=result, search_term=name)

@app.route("/delete_recipe/<int:id>", methods=["POST"])
def delete_recipe(id):
    users.check_csrf()
    if recipes.delete_recipe(id):
        return redirect("/")
    else:
        return render_template("error.html", message="Reseptin poistaminen epäonnistui.")

@app.route("/modify_public/<int:id>", methods=["POST"])
def modify_public(id):
    users.check_csrf()
    status = request.form["public_status"]
    recipes.set_public(id, status)
    return redirect("/recipes/"+str(id))

@app.route("/modify/<int:id>", methods=["GET"])
def show_modify(id):
    if users.user_id() == 0:
        return render_template("error.html", message="Kirjaudu sisään.")
    creator_id = recipes.get_user_id(id)
    user_id = users.user_id()
    if user_id == creator_id:
        recipe_name = recipes.get_name(id)
        old_ingredients = recipes.get_ingredients(id)
        old_instructions = recipes.get_instructions(id)
        if recipes.get_public(id):
            public_status = "julkinen"
        else:
            public_status = "yksityinen" 
        return render_template("modify.html", name=recipe_name, id=id, old_ingredients=old_ingredients, old_instructions=old_instructions, public=public_status)
    else:
        return render_template("error.html", message="Ei ole oma reseptisi.")

@app.route("/modify_name/<int:id>", methods=["POST"])
def modify_name(id):
    users.check_csrf()
    name = request.form["name"]
    if name.strip() == "":
        return render_template("error.html", message="Reseptillä pitää olla nimi.")
    elif recipes.change_name(id, name):
        return redirect("/recipes/"+str(id))
    else:
        return render_template("error.html", message="Nimen vaihtaminen ei onnisutnut.")

@app.route("/modify_ingredients/<int:id>", methods=["POST"])
def modify_ingredients(id):
    users.check_csrf()
    new_ingredients = request.form["ingredients"]
    if recipes.change_ingredients(id, new_ingredients):
        return redirect("/recipes/"+str(id))
    else:
        return render_template("error.html", message="Ei onnistunut. Syötä uudet raaka-aineet muodossa raaka-aine;numero;raaka-aine")

@app.route("/modify_instructions/<int:id>", methods=["POST"])
def modify_instructions(id):
    users.check_csrf()
    instructions = request.form["instructions"]
    if instructions.strip() == "":
        return render_template("error.html", message="Reseptillä pitää olla ohjeet.")
    elif recipes.change_instructions(id, instructions):
        return redirect("/recipes/"+str(id))
    else:
        return render_template("error.html", message="Ei onnistunut")

@app.route("/newrecipe", methods=["GET"])
def newrecipe():
    if users.user_id() == 0:
        return render_template("error.html", message="Kirjaudu sisään.")
    else:
        return render_template("newrecipe.html")
        

@app.route("/create_recipe", methods=["POST"])
def send():
    users.check_csrf()
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
        return redirect("/recipes/"+str(recipe_id))
    else:
        return render_template("error.html", message="Reseptin luominen epäonnistui. Tarkista raaka-aineiden kirjoitusasu.")


@app.route("/recipes/<int:id>", methods=["GET"])
def show_recipe(id):
    if users.user_id() == 0:
        return render_template("error.html", message="Kirjaudu sisään.")
    
    allow = False
    is_own = False
    in_library = False
    user_id  = users.user_id()
    library_id = None
    notes = None
    if user_id == recipes.get_user_id(id): 
        allow = True 
        is_own = True 
        library_id = recipes.get_library_id(user_id, id)
        notes = recipes.get_notes(library_id)
    elif  recipes.in_library(user_id, id):
        allow = True 
        in_library = True 
        library_id = recipes.get_library_id(user_id, id)
        notes = recipes.get_notes(library_id)
    elif recipes.get_public(id):
        allow = True
    if not allow:
        return render_template("error.html", message="Ei katseluoikeutta.")

    name = recipes.get_name(id)
    ingredients = recipes.get_ingredients(id)
    instructions = recipes.get_instructions(id)
    added_by = recipes.get_creator(id)
    stars = recipes.get_stars(id)

    if recipes.get_public(id):
        public = "julkinen"
    else:
        public = "yksityinen"
    return render_template("recipe.html", name=name, ingredients=ingredients, instructions=instructions, user_id=user_id , id=id, 
                                        public_status=public, added_by=added_by, is_own=is_own, in_library=in_library, notes=notes,
                                        stars=stars)

@app.route("/")
def index():
    recipes_list = recipes.get_own_recipes()
    user_id = users.user_id()
    others_recipes = recipes.get_others(user_id)
    return render_template("index.html", own_recipes=recipes_list, user_id=user_id, others_recipes=others_recipes)

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