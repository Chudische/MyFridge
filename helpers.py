import os
import requests
from functools import wraps
from flask import redirect, render_template, request, session
import csv


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_data_from_csv(file_name):
    """
    Get data from csv file into a list
    """
    data = []
    with open(file_name, "r") as file:
        reader = csv.reader(file, delimiter= ";")
        for row in reader:
            data.append([row[0], row[1]])
    return data

def create_ingredient_json(arg_list, key_list):
    """Create a list of dicts from bd select"""
    if len(arg_list[0]) != len(key_list):
        print("Wrong number of key_list")
        return []
    ingredient_list = []
    
    for ingredient in arg_list:            
        ingredient_json ={}
        for item in range(len(ingredient)):
            if key_list[item] == "unit_list":
                 ingredient_json[key_list[item]] = ingredient[item][1:-1].split(",")
            else:
                ingredient_json[key_list[item]] = ingredient[item]
        ingredient_list.append(ingredient_json)
    return ingredient_list

def download_image(image):
    """Download picture to local storage"""
    req = requests.get(f"https://spoonacular.com/cdn/ingredients_100x100/{image}")
    images = os.listdir("./static/img/ingredients")
    
    if image not in images:
        with open(f"./static/img/ingredients/{image}", "wb") as file:
            file.write(req.content)
    return 0    
    
    

    

