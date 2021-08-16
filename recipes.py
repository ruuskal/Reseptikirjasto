from db import db
import users

def create(name, ingredients, steps):
    user_id = users.user_id()
    if user_id == 0:
        return None
    sql = "INSERT INTO recipes (name, added_by) VALUES (:name, :user_id) RETURNING id"
    recipe = db.session.execute(sql, {"name":name, "user_id":user_id})
    recipe_id = recipe.first()[0]

    sql2 = "INSERT INTO library (user_id, recipe_id) VALUES (:user_id, :recipe_id)"
    db.session.execute(sql2, {"user_id":user_id, "recipe_id":recipe_id})
    
    sequence = 0
    for x in steps.split(";"):
        sequence += 1
        step = x.strip()
        sql4 = """INSERT INTO instructions (step, sequence, recipe_id)
            VALUES (:step, :sequence, :recipe_id)"""
        db.session.execute(sql4, {"step":step, "sequence":sequence, "recipe_id":recipe_id})

    if add_ingredients(recipe_id, ingredients):
        db.session.commit() # Haittaako, että commit on vain täällä, eikä metodissa add_ingredients?
        return recipe_id
    else:
        return None
     
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
    return True

# Return recipes' names in library
def get_own_recipes():
    user_id = users.user_id()
    sql = """SELECT r.id, r.name FROM recipes r, library l 
            WHERE l.recipe_id=r.id AND l.user_id=:user_id""" 
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
