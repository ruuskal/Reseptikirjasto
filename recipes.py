from db import db
import users

def delete_from_library(user_id, recipe_id):
    sql = """DELETE FROM library
            WHERE user_id=:user_id AND recipe_id=:recipe_id"""
    result = db.session.execute(sql, {"user_id":user_id, "recipe_id":recipe_id})
    db.session.commit()
    return True

def get_notes(id):
    sql = """SELECT content FROM notes
            WHERE library_id=:id"""
    result = db.session.execute(sql, {"id":id})
    return result.fetchall()

def create_note(content, id):
    sql = """INSERT INTO notes (content, library_id)
                VALUES (:content, :id)"""
    db.session.execute(sql, {"content":content, "id":id})
    db.session.commit()
    return True

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
    else:
        return True

# Return recipes, that are in library and not created by current user
def get_others(id):
    sql = """SELECT DISTINCT r.id, r.name FROM recipes r
            INNER JOIN library l ON l.recipe_id=r.id
            WHERE r.added_by NOT IN (:user_id) AND l.user_id =:user_id
            ORDER BY r.name"""
    result = db.session.execute(sql, {"user_id":id})
    return result.fetchall()

# Search recipe by partially matching ingredient
def search_by_ingredient(ingredient):
    ingr = "%"+ingredient+"%"
    user_id = users.user_id()
    sql = """SELECT DISTINCT r.id, r.name FROM recipes r
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
    sql = """SELECT DISTINCT id, name FROM recipes
            WHERE name ILIKE :name 
            AND (added_by=:user_id OR public='true')
            ORDER BY name"""
    result = db.session.execute(sql, {"name":name, "user_id":user_id })
    return result.fetchall()

# Returns name of the recipes creator
def get_creator(recipe_id):
    sql = """SELECT u.username FROM users u, recipes r
             WHERE r.id=:id AND u.id=r.added_by"""
    result = db.session.execute(sql, {"id":recipe_id})
    return result.fetchone()[0]

# Return list of public recipes not in own library
def get_public_recipes(id):
    sql = """SELECT DISTINCT r.id, r.name FROM recipes r
            WHERE r.id NOT IN (SELECT l.recipe_id FROM library l
                                WHERE l.user_id = (:id))
            AND r.public='true'
            ORDER BY r.name"""
    result = db.session.execute(sql, {"id":id})
    return result.fetchall()

def set_public(id, value):
    sql = """UPDATE recipes 
            SET public=:value
            WHERE id=:id"""
    db.session.execute(sql, {"id":id, "value":value})
    db.session.commit()
    return True
    
# Return recipe's public-status
def get_public(id):
    sql = """SELECT public FROM recipes
            WHERE id=:id"""
    result = db.session.execute(sql, {"id":id})
    return result.fetchone()[0]

# Create a new recipe
def create(name, ingredients, steps):
    user_id = users.user_id()
    if user_id == 0:
        return None
    sql = "INSERT INTO recipes (name, added_by) VALUES (:name, :user_id) RETURNING id"
    recipe = db.session.execute(sql, {"name":name, "user_id":user_id})
    recipe_id = recipe.first()[0]

    if add_ingredients(recipe_id, ingredients) and add_instructions(recipe_id, steps):
        db.session.commit() # Haittaako, että commit on vain täällä, eikä metodissa add_ingredients?
        if add_to_library(user_id, recipe_id):
            return recipe_id
        else:
            return None
    else:
        return None

# Add instructions to recipe
def add_instructions(id, steps):
    sequence = 0
    for x in steps.split(";"):
        if x.strip() != "":
            sequence += 1
            step = x.strip()
            sql = """INSERT INTO instructions (step, sequence, recipe_id)
                VALUES (:step, :sequence, :recipe_id)"""
            db.session.execute(sql, {"step":step, "sequence":sequence, "recipe_id":id})
    return True

# Change instructions
def change_instructions(id, new_instructions):
    sql_del = """DELETE FROM instructions
                WHERE recipe_id=:id"""
    db.session.execute(sql_del, {"id":id})
    if add_instructions(id, new_instructions):
        db.session.commit()
        return True
    else:
        return False

# Add ingredients to recipe
def add_ingredients(id, ingredients):
    for rows in ingredients.split("\n"):
        if rows.strip() != "":
            if rows.count(";") != 2:
                return False
            else:
                cell = rows.strip().split(";")
                if len(cell) != 3:
                    continue
                try:
                    amount = float(cell[1])
                except ValueError:
                    return False
                    break
                sql = """INSERT INTO ingredients (ingredient, amount, unit, recipe_id)
                    VALUES (:ingredient, :amount, :unit, :recipe_id)"""
                db.session.execute(sql, {"ingredient":cell[0], "amount":amount, "unit":cell[2], "recipe_id":id})
    return True
            
# Add recipe to library
def add_to_library(user_id, recipe_id):
    sql = "INSERT INTO library (user_id, recipe_id) VALUES (:user_id, :recipe_id)"
    db.session.execute(sql, {"user_id":user_id, "recipe_id":recipe_id})
    db.session.commit()
    print(user_id)
    print(recipe_id)
    return True

# Return list of own recipes' names and ids
def get_own_recipes():
    user_id = users.user_id()
    sql = """SELECT id, name FROM recipes  
            WHERE  added_by=:user_id
            ORDER BY name""" 
    result = db.session.execute(sql, {"user_id": user_id})
    return result.fetchall()

# Return recipe's name
def get_name(id):
    sql = "SELECT name FROM recipes WHERE id=:id"
    result = db.session.execute(sql, {"id": id})
    return result.fetchone()[0]

# Return list of ingredients
def get_ingredients(recipe_id):
    sql = """SELECT ingredient, amount, unit FROM ingredients 
            WHERE recipe_id=:id"""
    result = db.session.execute(sql, {"id": recipe_id})
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

#Delete ingredients
def delete_ingredients(id):
    sql = """DELETE FROM ingredients
            WHERE recipe_id=:id"""
    db.session.execute(sql, {"id": id})
    return True


#Change recipe's ingredients
def change_ingredients(id, new_ingredients):
    delete_ingredients(id)
    if add_ingredients(id, new_ingredients):
        db.session.commit()
        return True
    else:
        return False

#Change recipe's name
def change_name(id, name):
    sql = """UPDATE recipes
            SET name=:name
            WHERE id=:id"""
    result = db.session.execute(sql, {"name": name, "id": id})
    db.session.commit()
    return True

#Delete recipe 
def delete_recipe(id):
    sql = """DELETE FROM recipes
                WHERE id=:id"""
    db.session.execute(sql, {"id": id})
    db.session.commit()
    return True
