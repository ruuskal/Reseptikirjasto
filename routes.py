from flask import render_template, request, redirect
from app import app
import users, recipes

@app.route("/make_recipe", methods=["GET"])
def get_make_recipe():
    if users.user_id() == 0:
        return render_template("error.html", message="Kirjaudu sisään.")
    return render_template("create_recipe.html")

@app.route("/make_recipe", methods=["POST"])
def create_recipe():
    users.check_csrf()
    name = request.form["name"]
    if less_or_more(name, 3, 30):
        return render_template("error.html", message="Nimen tulee olla 3-30 merkkiä pitkä.")

    lines = int(request.form["lines"])
    if lines == -1 or lines > 50:
        return render_template("error.html",
                               message="Reseptillä pitää olla 1-50 riviä aineksia.")
    ingredients = []
    row = 0
    while row <= lines:

        i_index = "ingredient"+str(row)
        u_index = "unit"+str(row)
        a_index = "amount"+str(row)

        ingredient = request.form[i_index]
        if less_or_more(ingredient, 3, 50):
            return render_template("error.html",
                                   message="Raaka-aineen tulee käyttää 3-50 merkkiä.")

        try:
            amount_f = float(request.form[a_index])
        except ValueError:
            return render_template("error.html", message="Anna määrä numeroina, esim 0.5")

        amount = request.form[a_index]
        if less_or_more(amount, 1, 4):
            return render_template("error.html",
                                   message="Määrän tulee käyttää 1-4 merkkiä.")

        unit = request.form[u_index]
        if less_or_more(unit, 1, 50):
            return render_template("error.html",
                                   message="Yksikön tulee käyttää 1-50 merkkiä.")

        new_row = [ingredient, amount_f, unit]
        ingredients.append(new_row)
        row += 1

    inst = request.form["instructions"]
    if less_or_more(inst, 1, 3000):
        return render_template("error.html",
                               message="Ohjeiden tulee käyttää 1-3000 merkkiä.")

    recipe_id = recipes.create(name, ingredients, inst)
    return redirect("/recipes/"+str(recipe_id))

@app.route("/delete_note/<int:r_id>", methods=["POST"])
def delete_note(r_id):
    users.check_csrf()
    if "note_id" in request.form:
        note_id = request.form["note_id"]
        recipes.delete_note(note_id)
    return redirect("/recipes/"+str(r_id))

@app.route("/stars/<int:r_id>", methods=["POST"])
def rate(r_id):
    users.check_csrf()
    try:
        stars = int(request.form["stars"])
    except ValueError:
        return render_template("error.html", message="Arvion on oltava kokonaisluku väliltä 1-5")
    if 1 < stars > 5:
        return render_template("error.html", message="Arvion on oltava kokonaisluku väliltä 1-5")
    recipes.give_stars(r_id, stars)
    return redirect("/recipes/"+str(r_id))

@app.route("/delete_from_library/<int:recipe_id>", methods=["POST"])
def delete_from_library(recipe_id):
    users.check_csrf()
    recipes.delete_from_library(recipe_id)
    return redirect("/")

@app.route("/add_note/<int:recipe_id>", methods=["POST"])
def add_note(recipe_id):
    users.check_csrf()
    content = request.form["note"]
    if less_or_more(content, 1, 1000):
        return render_template("error.html",
                               message="Muistiinpanon pitää olla 1-1000 merkkiä pitkä.")

    library_id = recipes.get_library_id(recipe_id)

    recipes.create_note(content, library_id)
    return redirect("/recipes/"+str(recipe_id))


@app.route("/public_recipes", methods=["GET"])
def show_public():
    if users.user_id() == 0:
        return render_template("error.html", message="Et ole kirjautunut sisään.")

    public_recipes = recipes.get_public_recipes()
    visible_amount = recipes.get_visible_amount()
    best = recipes.get_best()
    return render_template("public_recipes.html", public_recipes=public_recipes,
                           visible_amount=visible_amount, best=best)

@app.route("/add_to_library/<int:r_id>", methods=["POST"])
def add_recipe(r_id):
    users.check_csrf()
    recipes.add_to_library(r_id)
    return redirect("/")

def less_or_more(word, min_length, max_length):
    if word.strip() == "":
        return True
    if len(word) < min_length or len(word) > max_length:
        return True
    return False

@app.route("/search_ingredient", methods=["POST"])
def search_ingredient():
    users.check_csrf()
    ingredient = request.form["search_ingredient"]
    if less_or_more(ingredient, 3, 50):
        return render_template("error.html", message="Hakusanan tulee olla 3-50 merkkiä pitkä.")
    result = recipes.search_by_ingredient(ingredient)

    if not result:
        search_result = "Ei löytynyt yhtään reseptiä haukusanalla '" + ingredient + "'."
        return render_template("results.html", recipes=result, search_result=search_result)

    search_result = "Reseptit hakusanalla " + ingredient + "'."
    return render_template("results.html", recipes=result, search_result=search_result)

@app.route("/search_name", methods=["POST"])
def search_name():
    users.check_csrf()
    name = request.form["search_name"]
    if less_or_more(name, 3, 30):
        return render_template("error.html", message="Hakusanan tulee olla 3-30 merkkiä pitkä.")
    result = recipes.search_by_name(name)

    if not result:
        search_result = "Ei löytynyt yhtään reseptiä haukusanalla '" + name + "'."
        return render_template("results.html", recipes=result, search_result=search_result)
    else:
        search_result = "Reseptit hakusanalla '" + name + "'."

    return render_template("results.html", recipes=result, search_result=search_result)

@app.route("/delete_recipe/<int:r_id>", methods=["POST"])
def delete_recipe(r_id):
    users.check_csrf()
    recipes.delete_recipe(r_id)
    return redirect("/")

@app.route("/modify_public/<int:r_id>", methods=["POST"])
def modify_public(r_id):
    users.check_csrf()
    status = request.form["public_status"]
    recipes.set_public(r_id, status)
    return redirect("/modify/"+str(r_id))

@app.route("/modify/<int:r_id>", methods=["GET"])
def show_modify(r_id):
    user_id = users.user_id()
    if user_id == 0:
        return render_template("error.html", message="Kirjaudu sisään.")
    creator_id = recipes.get_added_by(r_id)
    if user_id == creator_id:
        recipe_name = recipes.get_name(r_id)
        old_ingredients = recipes.get_ingredients(r_id, 1)
        ingr_rows = len(old_ingredients)
        old_instructions = recipes.get_instructions(r_id)
        if recipes.get_public(r_id):
            public_status = "julkinen"
        else:
            public_status = "yksityinen"
        return render_template("modify.html", name=recipe_name, r_id=r_id,
                               old_ingredients=old_ingredients, old_instructions=old_instructions,
                               public=public_status, ingr_rows=ingr_rows)
    else:
        return render_template("error.html", message="Ei ole oma reseptisi, et voi muokata sitä.")

@app.route("/modify_name/<int:r_id>", methods=["POST"])
def modify_name(r_id):
    users.check_csrf()
    name = request.form["name"]
    if less_or_more(name, 3, 50):
        return render_template("error.html", message="Nimen tulee olla 3-50 merkkiä pitkä.")
    recipes.change_name(r_id, name)
    return redirect("/modify/"+str(r_id))


@app.route("/add_ingredient/<int:r_id>", methods=["POST"])
def new_ingredient(r_id):
    users.check_csrf()
    ingredient = request.form["ingredient"]

    if less_or_more(ingredient, 3, 50):
        return render_template("error.html", message="Raaka-aineen tulee käyttää 3-50 merkkiä.")
    try:
        float(request.form["amount"])
    except ValueError:
        return render_template("error.html", message="Anna määrä numeroina, esim 0.5")

    amount = request.form["amount"]
    if less_or_more(amount, 1, 4):
        return render_template("error.html",
                               message="Määrä voi käyttää korkeintaan 4 merkkiä.")

    unit = request.form["unit"]
    if less_or_more(unit, 1, 50):
        return render_template("error.html", message="Yksikön tulee käyttää 1-50 merkkiä.")

    new_row = [ingredient, amount, unit]
    recipes.make_ingredients(r_id, new_row)
    return redirect("/modify/"+str(r_id))

@app.route("/delete_ingredient/<int:r_id>", methods=["POST"])
def delete_ingredient(r_id):
    users.check_csrf()
    if int(request.form["ingr_rows"]) < 2:
        return render_template("error.html", message="Et voi poistaa ainoaa ainesriviä."
                               + " Luo uusi rivi ennen vanhan poistamista.")

    if "ingr_id" in request.form:
        ingr_id = request.form["ingr_id"]
    else:
        return render_template("error.html", message="Valitse rivi poistettavaksi.")

    recipes.delete_ingredient(ingr_id)
    return redirect("/modify/"+str(r_id))

@app.route("/modify_instructions/<int:r_id>", methods=["POST"])
def modify_instructions(r_id):
    users.check_csrf()
    instructions = request.form["instructions"]
    if less_or_more(instructions, 1, 3000):
        return render_template("error.html", message="Ohjeiden tulee käyttää 1-3000 merkkiä.")

    recipes.change_instructions(r_id, instructions)
    return redirect("/modify/"+str(r_id))

@app.route("/multiply/<int:r_id>", methods=["POST"])
def multiply(r_id):
    users.check_csrf()
    coef = request.form["coef"]
    try:
        float(coef)
    except ValueError:
        return render_template("error.html", message="Syötä luku.")

    if len(coef) > 4 or float(coef) == 0:
        return render_template("error.html", message="Anna luku välilät 0.01 ja 9999.")

    users.session["coef"] = float(coef)
    return redirect("/recipes/"+str(r_id))

@app.route("/recipes/<int:r_id>", methods=["GET"])
def show_recipe(r_id):
    user_id = users.user_id()
    coef = users.coef()
    if user_id == 0:
        return render_template("error.html", message="Kirjaudu sisään.")

    allow = False
    is_own = False
    in_library = False
    library_id = None
    notes = None
    rated = recipes.get_rated_amount(r_id)
    if user_id == recipes.get_added_by(r_id):
        allow = True
        is_own = True
        library_id = recipes.get_library_id(r_id)
        notes = recipes.get_notes(library_id)
    elif  recipes.in_library(r_id):
        allow = True
        in_library = True
        library_id = recipes.get_library_id(r_id)
        notes = recipes.get_notes(library_id)
    elif recipes.get_public(r_id):
        allow = True
    if not allow:
        return render_template("error.html", message="Ei katseluoikeutta.")

    name = recipes.get_name(r_id)
    ingredients = recipes.get_ingredients(r_id, coef)
    instructions = recipes.get_instructions(r_id)
    added_by = recipes.get_creator(r_id)
    stars = recipes.get_stars(r_id)

    if recipes.get_public(r_id):
        public = "julkinen"
    else:
        public = "yksityinen"
    return render_template("recipe.html", name=name, ingredients=ingredients,
                           instructions=instructions, user_id=user_id, r_id=r_id,
                           public_status=public, added_by=added_by, is_own=is_own,
                           in_library=in_library, notes=notes, stars=stars,
                           rated=rated)

@app.route("/", methods=["GET"])
def index():
    recipes_list = recipes.get_own_recipes()
    others_recipes = recipes.get_others()
    return render_template("index.html", own_recipes=recipes_list,
                           others_recipes=others_recipes)

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

    return render_template("error.html", message="Väärä tunnus tai salasana")

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")