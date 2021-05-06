**Hello World! Hello CS50!**

My name is Akimov Serhii. I am from Ukraine and this is my project coled "my fridge"
It is a web-application. I am using flask framework, postgresql database and spoonacular API.
At first we get to the login page. Here can provide our login and password or click on the 
"registration" button to register new account.

let's register a new accoun. So, when user is pass the registration form he gets to the main page. Now we don't see any ingredients so far. So we need to add some to our frige... I am using spoonacular API. This is food API that provides me all information that about ingredients and recipes. I am on free plan so i have only 150 requests per day. It's a litle bit slow, but i think it because it is a free plan. 

Add ingredients. lest say "corned beef, potatoes, onion, tomatoes, shallot, canned mushrooms, arborio rice" Now we have some in frige, so we can go to cooking page to look what we can cook whith our ingredients.

In the cooking page we see top 5 recipes. If we need more, we may click on the "more rescipes" button. Here we see that "minumum unused indgredient" option is on by default. But we can change it to the "maximum used" option. Then we see another recipes. If we click on the "resipe details" we see popup window with reside description. Here can add this resipe to favorite. In every recipe we can click on every ingredient, both in "used" and "need to buy" lists. But in "need to buy" list we can add ingredient to shopping list.

Now we go to the "shopping list". Here we see ingredients that we had added in cooking page. Also we can add  new ingredient by clicking add button. If we want to move ingredients from shopping list to the main page, we click on "Bought" button. Also we can delete ingredien from our shopping list or main page by clicking on "close" button.

And the last page is "favorite recipes". Here we see our saved recipes. We can click to see details.
Or click the close button to delete current recipe.

Some form are post directly to the server, some are preven and give post request with AYAX. 


