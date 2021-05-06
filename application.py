import os
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required, create_ingredient_json, download_image
import spoonacular
import json
from dotenv import load_dotenv


# Load enviroment variables from dotenv file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


# Configure database
engine = create_engine(os.getenv("POSTGRES"))
db = scoped_session(sessionmaker(bind=engine)) 


# Configure application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to spoonacular Api
api= spoonacular.API(api_key=os.getenv("SPOON_API"))

# Make global var for most of functions
ingredients = db.execute("SELECT ing_name, ing_id FROM ingredients ORDER BY ing_name").fetchall()

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session["user_id"]     
    # Update base with new ingredient
    if request.method == "POST":
        # check the validity of form fields
        if not request.form.get("inputIngredient"):
            flash("Must provide ingredient")
            return redirect("/")

        if not request.form.get("select1") or request.form.get("select1") == "Bad ingredient":
            flash("Must provide Unit or no such ingredient in base")
            return redirect("/")

        if not request.form.get("number") or int(request.form.get("number")) <= 0:
            flash("Invalid quantity")
            return redirect("/")

        if request.form.get("inputIngredient") not in dict(ingredients):
            flash(f"Sorry, {request.form.get('inputIngredient')} not in the base of ingredients")
            return redirect("/")

        # Get information from form
        json = request.form.get("json")        
        ing_id = request.form.get("ingId")
        unit = request.form.get("select1")
        quantity = request.form.get("number")       
        # Ensure the ingredien is new for user and find it in buy db
        user_ingredient = db.execute("SELECT * FROM in_frige WHERE user_id=:user_id AND ing_id=:ing_id",
            {"user_id" : user_id, "ing_id" : ing_id}).fetchone()
        user_ingredient_buy = db.execute("SELECT * FROM buy WHERE user_id=:user_id AND ing_id=:ing_id",
            {"user_id" : user_id, "ing_id" : ing_id}).fetchone()
        ing_base = db.execute("SELECT * FROM ingredients WHERE ing_id=:ing_id",
            {"ing_id" : ing_id}).fetchone()
        
        if user_ingredient:
            flash("You already heve such ingredient")
            # if user try to click butto "bought" and such ingredient alredy in "in_fridge" base
            try:
                db.execute("DELETE FROM buy WHERE user_id=:user_id AND ing_id=:ing_id",
                    {"user_id": user_id, "ing_id": ing_id})
                db.commit()
            except Exception as e:
                print(f"Error in index function. Can't delete from buy ingredient {ing_id} \n {e}")
                return jsonify({"status" : "bad"})
            if json:
                return jsonify({"status" : "bad", "error" : "sql"})
            else:
                return redirect("/")
        else:
            # daily limit of free access to api (150 per day)
            api_response = api.get_food_information(ing_id)
            if api_response.status_code != 200:
                flash("Sorry, the daily limit is ended. Try next time")
                if json:
                    return jsonify({"status" : "bad", "error" : "api"})
                else:
                    return redirect("/")
            # Add new ingredient for user
            try:
                db.execute("INSERT INTO in_frige(user_id, ing_id, unit, quantity) VALUES (:user_id, :ing_id, :unit, :quantity)", 
                    {"user_id" : user_id, "ing_id" : ing_id, "unit" : unit, "quantity" : quantity})
                db.commit()
                flash("The ingredient is added")
                               
            except Exception as e:                
                print(f"Error in index function. Can't insert ingredient {ing_id} \n {e}")
                if json:
                    return jsonify({"status" : "bad"})
                else:
                    return redirect("/")
            # remove ingredient from "need to buy" if it exist
            if user_ingredient_buy:
                try:
                    db.execute("DELETE FROM buy WHERE user_id=:user_id AND ing_id=:ing_id",
                        {"user_id": user_id, "ing_id": ing_id})
                    db.commit()
                except Exception as e:
                    print(f"Error in index function. Can't delete from buy ingredient {ing_id} \n {e}")
                    if json:
                        return jsonify({"status" : "bad"})

            # get ingredient 'shoppingListUnits'            
            ingredient = api_response.json()
            try:              
                unit_list = ingredient['shoppingListUnits']
            except:
                unit_list = ['pieces']            
            image = ingredient['image']
            # update table ingredients with units and image
            try:
                db.execute("UPDATE ingredients SET unit_list=:unit_list, image=:image WHERE ing_id=:ing_id",
                    {"unit_list" : unit_list, "image" : image, "ing_id" : ing_id})
                db.commit()
            except Exception as e:
                print(f"Error in index function. Can't update ingredient {ing_id} \n {e}")
            download_image(image)
            if json:
                    return jsonify({"status" : "ok"})                         
            else:
                return redirect("/")

    else:
        # Get from base ingredients         
        ing_base = db.execute("""
            SELECT
                in_frige.ing_id, 
                in_frige.unit, 
                quantity, 
                ing_name, 
                image 
            FROM in_frige 
            INNER JOIN ingredients ON in_frige.ing_id=ingredients.ing_id 
            WHERE user_id=:user_id""",
                 {"user_id": user_id}).fetchall()
        # Create a list of ingredients
        if ing_base:
            key_list = ["id", "unit", "quantity", "name", "image"]
            ingredient_list = create_ingredient_json(ing_base, key_list) 
        else:
            ingredient_list = []       
        return render_template("index.html", 
            ingredient_list = ingredient_list, ingredients = ingredients)


@app.route("/update", methods=["POST"])
def update():
    """Update information of user units"""
    user_id = session["user_id"]    
    # Get the form fields       
    ing_id = request.form.get("ingId")
    unit = request.form.get("select1")
    quantity = request.form.get("number")    
    if request.form.get("delete"):
        ing_id = request.form.get("ing_id")
        page = request.form.get("page")
        location = page.split("/")[-1]
        if not location:            
            try:
                db.execute("DELETE FROM in_frige WHERE user_id=:user_id AND ing_id=:ing_id",
                    {"user_id": user_id, "ing_id": ing_id})
                db.commit()            
            except Exception as e:
                flash("Can't remove ingredient")
                print(f"Error in update function. Can't delete ingredient {ing_id} from in_frige \n {e}")        
            return url_for("index")
        else:
            try:
                db.execute("DELETE FROM buy WHERE user_id=:user_id AND ing_id=:ing_id",
                    {"user_id": user_id, "ing_id": ing_id})
                db.commit()            
            except Exception as e:
                flash("Can't remove ingredient")
                print(f"Error in update function. Can't delete ingredient {ing_id} from buy \n {e}")        
            return url_for("buy")   
    
    if not quantity:
        flash("Must provide the quantity")
        return redirect("/") 
    
    if int(quantity) < 1:
        try:
            db.execute("DELETE FROM in_frige WHERE user_id=:user_id AND ing_id=:ing_id",
                {"user_id": user_id, "ing_id": ing_id})
            db.commit()
        except Exception as e:
            flash("Can't remove ingredient")
            print(f"Error in update function. Can't delete ingredient {ing_id} from in_frige \n {e}")
            return redirect("/")     
    
    # Update database    
    if not unit:
        try:
            db.execute("UPDATE in_frige SET quantity=:quantity WHERE user_id=:user_id AND ing_id=:ing_id",
                {"quantity": quantity, "user_id": user_id, "ing_id": ing_id})
            db.commit()
        except Exception as e:
            flash("Can't update ingredient")
            print(f"Error in update function. Can't update ingredient {ing_id} from in_frige \n {e}")
    else:
        try:
            db.execute("UPDATE in_frige SET unit=:unit, quantity=:quantity WHERE user_id=:user_id AND ing_id=:ing_id",
                {"unit": unit, "quantity": quantity, "user_id": user_id, "ing_id": ing_id})
            db.commit()
        except Exception as e:
            flash("Can't update ingredient")
            print(f"Error in update function. Can't update ingredient {ing_id} from in_frige \n {e}")
    return redirect("/")      
   

@app.route("/check", methods=["GET"])
def check():
    """Return ok if username available, else false, in JSON format"""
    username = request.args.get("username")    
    try:
        user = db.execute("SELECT * FROM users WHERE username=:username ", {"username" : username}).fetchone()
    except Exception as e:
        print(f"Error in check function with username={username}\n {e}")
        return jsonify({"username" : "false"})    
    if user:
        return jsonify({"username" : "false"})
    return jsonify({"username" : "ok"})


@app.route("/get_ingredient", methods=["GET"])
def get_ing():
    """ Return ingredient in JSON format """
    user_id = session["user_id"]    
    ing_id = request.args.get("ing_id")
    edit = request.args.get("edit")
    if not edit:
        if ing_id == "undefined":
            return jsonify({'shoppingList': ['Bad ingredient']})    
        api_response = api.get_food_information(ing_id)
        
        if api_response.status_code != 200:
                flash("Sorry, the daily limit is ended. Try next time")
                return redirect("/")
        ingredient = api_response.json()
        
        if 'shoppingListUnits' not in ingredient:
            ingredient['shoppingListUnits'] = ['pieces']
        return jsonify(ingredient)
    else:
        ing_base = db.execute("""
            SELECT
                in_frige.ing_id ing_id, 
                ingredients.unit_list,
                quantity,                
                ing_name, 
                image 
            FROM in_frige 
            INNER JOIN ingredients ON in_frige.ing_id=ingredients.ing_id 
            WHERE user_id=:user_id AND in_frige.ing_id=:ing_id""",
                 {"user_id": user_id, "ing_id": ing_id}).fetchall()
        key_list = ["id", "unit_list", "quantity", "name", "image"]
        ingredient = create_ingredient_json(ing_base, key_list)[0]        
        return jsonify(ingredient)


@app.route("/cook", methods=["GET"])
@login_required
def cook():
    request_ranking = request.args.get("ranking")    
    user_id = session["user_id"]
    # 1 - for maximize used ingredients; 2 - for minimize unused    
    ranking = 1 if request_ranking else 2           
    ing_db = db.execute("""
        SELECT 
            ingredients.ing_name 
        FROM in_frige 
        INNER JOIN ingredients ON in_frige.ing_id=ingredients.ing_id
        WHERE user_id=:user_id""",
            {"user_id" : user_id}).fetchall()
    ing_list = ",".join([ing[0] for ing in ing_db])     
    api_response = api.search_recipes_by_ingredients(ing_list, number=10, ranking=ranking)
    # daily limit of free access to api (150 per day)
    if api_response.status_code != 200:
        flash("Sorry, the daily limit is ended. Try next time")
        return redirect("/")

    recipes = api_response.json()    
    max_used = 0 
    if ranking == 1:
        max_used = 1               
    return render_template("cook.html", recipes = recipes, ingredients = ingredients, max_used = max_used)       


@app.route("/get_recipe_details", methods=["GET"])
def get_recipe_details():    
    recipe_id = request.args.get("recipe_id")    
    api_response = api.get_analyzed_recipe_instructions(recipe_id)
    if api_response.status_code != 200:
        flash("Sorry, the daily limit is ended. Try next time")
        return redirect("/")
    recipe = api_response.json()
    if not recipe:
        recipe.append({"steps" : [{"step" : "Sorry, recipe is corently unavaible"}]})
    return jsonify(recipe)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    user_id = session["user_id"]
    if request.method == "POST":
        if not request.form.get("inputIngredient"):
            flash("Must provide ingredient")
            return redirect("/buy") 
        json = request.form.get("json")
        ing_id = request.form.get("ingId")
        ing_base = db.execute("SELECT * FROM ingredients WHERE ing_id = :ing_id",
            {"ing_id": ing_id}).fetchone()
        if not ing_base:
            flash(f"Sorry, {request.form.get('inputIngredient')} not in base of ingredients")
            if json:
                return jsonify({"status" : "bad"})
            return redirect("/buy")
        # Check the picture in local storage
        if ing_base[3] is None:
            api_response = api.get_food_information(ing_id)
            if api_response.status_code != 200:
                flash("Sorry, the daily limit is ended. Try next time")
                return redirect("/")
            ingredient = api_response.json()
            try:              
                unit_list = ingredient['shoppingListUnits']
            except:
                unit_list = ['pieces']              
            image = ingredient['image']
            # update table ingredients with units and image
            try:
                db.execute("UPDATE ingredients SET unit_list=:unit_list, image=:image WHERE ing_id=:ing_id",
                    {"unit_list" : unit_list, "image" : image, "ing_id" : ing_id})
                db.commit()
            except Exception as e:
                print(f"Error in buy function. Can't update ingredient. \n {e}")
            download_image(image)
        buy_ing = db.execute("SELECT * FROM buy WHERE user_id=:user_id AND ing_id=:ing_id",
            {"user_id" : user_id, "ing_id" : ing_id}).fetchone()
        if buy_ing:
            if json:
                return jsonify({"status" : "bad", "error" : "sql"})
            else:
                flash("You already have this ingredient")
                return redirect("/buy")
        else:
            try:
                db.execute("INSERT INTO buy (user_id, ing_id) VALUES (:user_id, :ing_id)",
                    {"user_id" : user_id, "ing_id": ing_id})
                db.commit()
            except Exception as e:
                print(f"Error in buy function. Can't insert ingredient into buy. \n {e}")
                return jsonify({"status" : "bad"})       
        if json:
            return jsonify({"status" : "ok"})
        else:
            return redirect("/buy")

    else:
        # Get from base ingredients         
        ing_base = db.execute("""
            SELECT
                buy.ing_id,               
                ing_name, 
                image 
            FROM buy 
            INNER JOIN ingredients ON buy.ing_id=ingredients.ing_id 
            WHERE user_id=:user_id""",
                 {"user_id": user_id}).fetchall()
        # Create a list of ongredients
        if len(ing_base):
            key_list = ["id", "name", "image"]
            ingredient_list = create_ingredient_json(ing_base, key_list)
        else:
            ingredient_list = []
        return render_template("buy.html", 
            ingredient_list = ingredient_list, ingredients = ingredients, path = "buy")


@app.route("/favorite", methods=["GET", "POST"])
@login_required
def favorite():
    user_id = session["user_id"]
    if request.method == "POST":        
        recipe_id = request.form.get("recipe_id")       
        if request.form.get("delete"):
            try:
                db.execute("DELETE FROM favorite WHERE user_id=:user_id AND recipe_id=:recipe_id",
                    {"user_id" : user_id, "recipe_id" : recipe_id})
                db.commit()
                return jsonify({"status" : "ok"})
            except Exception as e:
                print(f"Error in favorite function. Can't delete recipe {recipe_id} \n {e}")
                return jsonify({"status" : "bad"})    
        if recipe_id:    
            
            try:
                db.execute("INSERT INTO favorite(user_id, recipe_id) VALUES(:user_id, :recipe_id)",
                    {"user_id" : user_id, "recipe_id" : recipe_id})
                db.commit()
            except Exception as e:
                print(f"ERROR! POST request in favorite with recipe_id = {recipe_id} not valid \n {e}")
                return jsonify({"status" : "bad", "error" : "sql"})
            return jsonify({"status" : "ok"})                              
        else:
            print("ERROR! POST request in favorite not valid. Missed recipe_id ")
            return jsonify({"status" : "bad"})
            
    else:
        recipe_db = db.execute("SELECT * FROM favorite WHERE user_id=:user_id", 
            {"user_id" : user_id}).fetchall()
        if not recipe_db:
            flash("You dont have favorite receps so far")
            return render_template("favorite.html")
        
        string_id = (',').join([str(rec_id[1]) for rec_id in recipe_db])        
        api_response = api.get_recipe_information_bulk(string_id)
        
        if api_response.status_code != 200:
            flash("Sorry, the daily limit is ended. Try next time")
            return render_template("favorite.html")
        recipe_list = api_response.json()      
        return render_template("favorite.html", recipe_list = recipe_list)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("User name is required", category="warning")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password is required", category="warning")
            return render_template("login.html")

        # Ensure user is registred    
        username = request.form.get("username")
        user = db.execute("SELECT * FROM users WHERE username=:username;", 
            {"username" : username}).fetchone()
        
        if user is None or not check_password_hash(user[2], request.form.get("password")):
            flash("Invalid username and/or password", category="warning")
            return render_template("login.html")
        session["user_id"] = user[0]            
        
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("User name is required", category="warning")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password is required", category="warning")
            return render_template("login.html")
        # Check password confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Wrong confirmation")
            return render_template("register.html")
        
        username = request.form.get("username")
        userpass = request.form.get("password")
        # Ensure username is not registred already  
        check_user = db.execute("SELECT * FROM users WHERE username=:username;", 
            {"username" : username}).fetchone()       
        if check_user:
            flash("Current username is already registred")
            return render_template("register.html")
        else:
            db.execute("INSERT INTO users(username, userpass) VALUES (:username, :userpass);",
                {"username" : username, "userpass" : generate_password_hash(userpass)})
            db.commit()

            user_id = db.execute("SELECT id FROM users WHERE username=:username;", 
                {"username" : username}).fetchone()
            
            session["user_id"] = user_id[0]
            return redirect("/")
    else:
        return render_template("register.html")
        

@app.route("/changepass", methods=["POST", "GET"])
@login_required
def changepass():
    """ Chenge user account password"""
    user_id = session["user_id"]
    if request.method == "POST":
        if not request.form.get("oldpassword"):
            flash("Must provide old password")
            return redirect("/changepass")

        elif not request.form.get("password"):
            flash("Must provide new password")
            return redirect("/changepass")

        elif not request.form.get("confirmation") or request.form.get("password") != request.form.get("confirmation"):
            flash("Wrong confirmation!")
            return redirect("/changepass")

        user = db.execute("SELECT * FROM users WHERE id=:id;",
            {"id" : user_id}).fetchone()

        if not check_password_hash(user[2], request.form.get("oldpassword")):
            flash("Wrong old password")
            return redirect("/changepass")

        new_pass = request.form.get("password")

        try:
            db.execute("UPDATE users SET userpass=:userpass WHERE id=:user_id",
                {"userpass" : generate_password_hash(new_pass), "user_id" : user_id})
            db.commit()
        except Exception as e:
            flash("Can't change password")
            print(f"Error in changepass function. Can't update db users with password={new_pass} \n {e}")
            return redirect("/changepass")

        flash("Password successfuly changed")
        return redirect("/")

    else:
        return render_template("changepass.html")