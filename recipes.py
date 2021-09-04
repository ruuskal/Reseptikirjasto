from db import db
import users

def delete_note(note_id):
    sql = """DELETE FROM notes
          WHERE id=:id"""
    db.session.execute(sql, {"id":note_id})
    db.session.commit()

# Return number of recipes, that user can see
def get_visible_amount(user_id):
    sql = """SELECT COUNT (DISTINCT id) FROM recipes
          WHERE added_by=:id OR public='true'"""
    result = db.session.execute(sql, {"id":user_id})
    return result.fetchone()[0]

def get_rated_amount(r_id):
    sql = """SELECT COUNT(user_id) FROM library
          WHERE stars > 0 AND recipe_id=:id"""
    result = db.session.execute(sql, {"id":r_id})
    return result.fetchone()[0]

def get_best(user_id):
    sql = """SELECT id, name, stars FROM recipes
          WHERE (added_by=:user_id OR public='true') 
          AND stars = (SELECT MAX (stars) FROM recipes)"""
    result = db.session.execute(sql, {"user_id":user_id})
    return result.fetchall()

def give_stars(recipe_id, stars, user_id):
    sql = """UPDATE library
            SET stars=:stars
            WHERE recipe_id=:recipe_id AND user_id=:user_id"""
    db.session.execute(sql, {"stars":stars, "user_id":user_id, "recipe_id":recipe_id})
    sql2 = """UPDATE recipes
            SET stars=(SELECT ROUND(AVG(stars), 1) FROM library
                WHERE recipe_id=:recipe_id)
            WHERE id=:recipe_id"""
    db.session.execute(sql2, {"recipe_id":recipe_id})
    db.session.commit()

def get_stars(r_id):
    sql = """SELECT stars FROM recipes
            WHERE id=:id"""
    result = db.session.execute(sql, {"id":r_id})
    return result.fetchone()[0]

def delete_from_library(user_id, recipe_id):
    sql = """DELETE FROM library
            WHERE user_id=:user_id AND recipe_id=:recipe_id"""
    db.session.execute(sql, {"user_id":user_id, "recipe_id":recipe_id})
    db.session.commit()

def get_notes(lib_id):
    sql = """SELECT content, id FROM notes
            WHERE library_id=:id"""
    result = db.session.execute(sql, {"id":lib_id})
    return result.fetchall()

def create_note(content, lib_id):
    sql = """INSERT INTO notes (content, library_id)
                VALUES (:content, :id)"""
    db.session.execute(sql, {"content":content, "id":lib_id})
    db.session.commit()

def get_library_id(user_id, recipe_id):
    sql = """SELECT id from library
            WHERE user_id=:user_id AND recipe_id=:recipe_id"""
    result = db.session.execute(sql, {"user_id":user_id, "recipe_id":recipe_id})
    return result.fetchone()[0]

# Check if recipe is in library
def in_library(user_id, recipe_id):
    sql = """SELECT 1 FROM library
            WHERE user_id=:user_id AND recipe_id=:recipe_id"""
    result = db.session.execute(sql, {"user_id":user_id, "recipe_id":recipe_id})
    if result.fetchone() == None:
        return False

    return True

# Return recipes, that are in library and not created by current user
def get_others(user_id):
    sql = """SELECT DISTINCT r.id, r.name FROM recipes r
            INNER JOIN library l ON l.recipe_id=r.id
            WHERE r.added_by NOT IN (:user_id) AND l.user_id =:user_id
            ORDER BY r.name"""
    result = db.session.execute(sql, {"user_id":user_id})
    return result.fetchall()

# Search recipe by partially matching ingredient
def search_by_ingredient(ingredient):
    ingr = "%"+ingredient+"%"
    user_id = users.user_id()
    sql = """SELECT DISTINCT r.id, r.name
            FROM recipes r
            WHERE r.id IN 
                        (SELECT DISTINCT r.id FROM recipes r 
                        INNER JOIN ingredients i ON i.recipe_id=r.id 
                        WHERE i.ingredient ILIKE :ingredient) 
            AND (r.public='true' OR r.added_by=:user_id)
            ORDER BY r.name"""
    result = db.session.execute(sql, {"ingredient":ingr, "user_id":user_id})
    return result.fetchall()

# Search recipe with partially matching name
def search_by_name(name):
    user_id = users.user_id()
    name = "%" + name + "%"
    sql = """SELECT id, name
            FROM recipes
            WHERE name ILIKE :name 
            AND (added_by=:user_id OR public='true')
            ORDER BY name"""
    result = db.session.execute(sql, {"name":name, "user_id":user_id})
    return result.fetchall()

# Returns name of the recipes creator
def get_creator(r_id):
    sql = """SELECT u.username FROM users u, recipes r
             WHERE r.id=:id AND u.id=r.added_by"""
    result = db.session.execute(sql, {"id":r_id})
    return result.fetchone()[0]

# Return list of public recipes not in own library
def get_public_recipes(r_id):
    sql = """SELECT DISTINCT r.id, r.name FROM recipes r
            WHERE r.id NOT IN (SELECT l.recipe_id FROM library l
                                WHERE l.user_id = (:id))
            AND r.public='true'
            ORDER BY r.name"""
    result = db.session.execute(sql, {"id":r_id})
    return result.fetchall()

def set_public(r_id, value):
    sql = """UPDATE recipes 
            SET public=:value
            WHERE id=:id"""
    db.session.execute(sql, {"id":r_id, "value":value})
    db.session.commit()
    
# Return recipe's public-status
def get_public(r_id):
    sql = """SELECT public FROM recipes
            WHERE id=:id"""
    result = db.session.execute(sql, {"id":r_id})
    return result.fetchone()[0]

# Create a new recipe
def create(name, ingredients, steps):
    user_id = users.user_id()
    if user_id == 0:
        return None
    sql = "INSERT INTO recipes (name, added_by) VALUES (:name, :user_id) RETURNING id"
    recipe = db.session.execute(sql, {"name":name, "user_id":user_id})
    recipe_id = recipe.first()[0]

    for line in ingredients:
        sql = """INSERT INTO ingredients (ingredient, amount, unit, recipe_id)
            VALUES (:ingredient, :amount, :unit, :recipe_id)"""
        db.session.execute(sql, {"ingredient":line[0], "amount":line[1], "unit":line[2],
                                 "recipe_id":recipe_id})

    add_instructions(recipe_id, steps)
    db.session.commit()
    add_to_library(user_id, recipe_id)
    return recipe_id

def make_ingredients(ingr_id, ingredient):
    sql = """INSERT INTO ingredients (ingredient, amount, unit, recipe_id)
            VALUES (:ingredient, :amount, :unit, :recipe_id)"""
    db.session.execute(sql, {"ingredient":ingredient[0], "amount":ingredient[1],
                             "unit":ingredient[2], "recipe_id":ingr_id})
    db.session.commit()

# Add instructions to recipe
def add_instructions(r_id, steps):
    sequence = 0
    for step in steps.split(";"):
        step.strip()
        if step != "":
            sequence += 1
            sql = """INSERT INTO instructions (step, sequence, recipe_id)
                VALUES (:step, :sequence, :recipe_id)"""
            db.session.execute(sql, {"step":step, "sequence":sequence, "recipe_id":r_id})

# Change instructions
def change_instructions(inst_id, new_instructions):
    sql_del = """DELETE FROM instructions
                WHERE recipe_id=:inst_id"""
    db.session.execute(sql_del, {"inst_id":inst_id})
    add_instructions(inst_id, new_instructions)
    db.session.commit()

# Add recipe to library
def add_to_library(user_id, recipe_id):
    sql = "INSERT INTO library (user_id, recipe_id) VALUES (:user_id, :recipe_id)"
    db.session.execute(sql, {"user_id":user_id, "recipe_id":recipe_id})
    db.session.commit()

def delete_ingredient(ingr_id):
    sql = """DELETE FROM ingredients
            WHERE id=:id"""
    db.session.execute(sql, {"id": ingr_id})
    db.session.commit()

# Return list of own recipes' names and ids
def get_own_recipes():
    user_id = users.user_id()
    sql = """SELECT id, name FROM recipes 
            WHERE  added_by=:user_id
            ORDER BY name"""
    result = db.session.execute(sql, {"user_id": user_id})
    return result.fetchall()

# Return recipe's name
def get_name(r_id):
    sql = "SELECT name FROM recipes WHERE id=:id"
    result = db.session.execute(sql, {"id": r_id})
    return result.fetchone()[0]

# Return list of ingredients
def get_ingredients(recipe_id, coef):
    if coef == 1:
        sql_f = """SELECT ingredient, amount, unit, id FROM ingredients
            WHERE recipe_id=:id"""
        result = db.session.execute(sql_f, {"id": recipe_id})
        return result.fetchall()
    
    sql_t = """SELECT ingredient, amount * :coef, unit, id FROM ingredients
            WHERE recipe_id=:id"""
    result = db.session.execute(sql_t, {"id": recipe_id, "coef":coef})
    users.session["coef"] = 1
    return result.fetchall()

#Return ordered list of instrctions
def get_instructions(recipe_id):
    sql = """SELECT step FROM instructions
            WHERE recipe_id=:id
            ORDER BY sequence"""
    result = db.session.execute(sql, {"id": recipe_id})
    return result.fetchall()

#Return id of the creator
def get_user_id(recipe_id):
    sql = """SELECT added_by FROM recipes
            WHERE id=:recipe_id"""
    result = db.session.execute(sql, {"recipe_id": recipe_id})
    return result.fetchone()[0]

#Change recipe's name
def change_name(r_id, name):
    sql = """UPDATE recipes
            SET name=:name
            WHERE id=:id"""
    db.session.execute(sql, {"name": name, "id": r_id})
    db.session.commit()

#Delete recipe
def delete_recipe(r_id):
    sql = """DELETE FROM recipes
                WHERE id=:id"""
    db.session.execute(sql, {"id": r_id})
    db.session.commit()