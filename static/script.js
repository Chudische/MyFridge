// Function run after page is fully downloaded
$( document ).ready(function() {
    // Alert function
    function showMassage (massage, status){
      $(".alert-fixed").text(massage);
      if (status == "err") {
        $(".alert-fixed").addClass("alert-danger").removeClass("alert-success");
        $(".alert-fixed").fadeIn(400).delay(2000).fadeOut(400);
      } else {
        $(".alert-fixed").addClass("alert-success").removeClass("alert-danger");
        $(".alert-fixed").fadeIn(400).delay(2000).fadeOut(400);
      }     
    };  
    // Username verification
    var allowSubmit = false;
    $("form#register").on("submit", function (e){    
      if (!allowSubmit) {
        e.preventDefault();
        let userName = $("input[name=username]").val();
        let userUrl = "/check?username=" + userName;
        var user = $.getJSON(userUrl, function(resp){
          if (resp.username == "ok"){
            allowSubmit = true;
            $("form#register").submit();
          } else {
            showMassage("Current username already registred", "err");
          }
        });
      }       
        return allowSubmit;      
    });

    var select = $("#selectUnits");
    function reload(){
      $(".img-modal").attr("src", "/static/img/ingredients/default.jpg");
      $("input[name=inputIngredient]").val("").attr('readonly', false);
      select.find("option").remove();
      select.append($('<option></option>').attr('value','default').attr('disabled', true).attr('selected', true).text('Select'));
      $("#inputNumber").val("")
      if($("form").attr("action") === "/update"){
        $("form").attr("action", '/');
      };
    }
    

    var imgModal = $(".img-modal").attr("src");
    reload();
    // Focus on imput in modal window
    $('#addIngredientModal').on('shown.bs.modal', function () {
      $('#inputIngredient').trigger('focus');      
    });

    // Get the unist of ingredient    
       
    $("input[name=inputIngredient]").on("change", function(){ 
      let ingID = $("#ingredients option[value='" + $(this).val()+ "']").attr("id");
      $("#hiddenInput").val(ingID); 
      let userUrl = '/get_ingredient?ing_id=' + ingID;
      select.find("option").remove();
      let ingJson = $.getJSON(userUrl, function(e){
        
        $.each(e.shoppingListUnits, function(key, entry){
          select.append($('<option></option>').attr('value', entry).text(entry));
        });      
        
        if (typeof e.image !== "undefined"){
          $(".img-modal").attr("src", imgModal + e.image);
        }           
      });
        
    });

    // Edit inggredient number or units
    $(".chenge-button").on("click", function(){
         
        $("form").attr("action", "/update")            
        let ingID = $(this).attr("id");
        let userUrl = '/get_ingredient?ing_id=' + ingID + '&edit=True';
        let number = $('input[id='+ $(this).attr("id") + ']').val();
        let ingJson = $.getJSON(userUrl, function(ing){
            $("input[name=inputIngredient]").val(ing.name).attr("readonly", true);          
            $(".img-modal").attr("src", "/static/img/ingredients/" + ing.image);
            select.find("option").remove();
            if (!number) {                
                $.each(ing.unit_list, function(key, value) {
                select.append($('<option></option>').attr("value", value).text(value));
                });
                $("#addIngredientModal").modal("show");
            }
            else {                
                $("#inputNumber").val(number);
                $("form#modalForm").submit();                
            }
        });   
    });

    $(".content-item .close-button").on("click", function(){
        let ingID = $(this).attr("id");
        let page = $(location).attr("href");               
        let data = {ing_id: ingID, delete : "True", page : page}; 
        $.post("/update", data, function(resp){
            window.location = resp;
        });
    });

    $("#newItem").on("click", function() {
      reload();      
    });
    
    $('#newBuyItem').on('click', function(){
      reload();
      $('#selectUnits').hide();
      $('#inputNumber').hide();      
    });
    // Bought button on ingredient (shopping list)
    $(".buy-button").on("click", function(){
      reload();            
      $("form").attr("action", "/");
      $('#selectUnits').show();
      $('#inputNumber').show();
      let ingID = $(this).attr("id") 
      let ingName = $('#ingredients option[id='+ ingID + ']').val();           
      let userUrl = '/get_ingredient?ing_id=' + ingID;
      let ingJson = $.getJSON(userUrl, function(e){
        $("#hiddenInput").val(ingID);
        $("input[name=inputIngredient]").val(ingName).attr("readonly", true);
        $.each(e.shoppingListUnits, function(key, entry){
          select.append($('<option></option>').attr('value', entry).text(entry));
        });          
        if (typeof e.image !== "undefined"){
          $(".img-modal").attr("src", imgModal + e.image);
        }
        $("#addIngredientModal").modal("show");          
      });        
      
    });
    $("form").on("submit", function(event){ 
      let id = $("#hiddenInput").val();          
      let url = document.URL.split("/");
      let position = url[url.length - 1];
      let destination = $("form").attr("action");       
      if (position == "buy" & destination == "/") {
        event.preventDefault();
        data = $("form").serialize() + "&json=true";
        $.post("/", data, function(response){
          if (response.status == "ok"){
            showMassage("Ingredient is added to fridge");
            $("." + id).remove();
            $("#addIngredientModal").modal("hide");
          } else if (response.status == "bad" & response.error == "sql"){
            showMassage("Ingredient alredy in fridge", "err");
            $("." + id).remove();
            $("#addIngredientModal").modal("hide");
          } else if (response.status == "bad" & response.error == "api"){
            showMassage("Error! Daily limit is ended. Try next time", "err");
          } else {
            showMassage("Error! Ingredient is not added", "err");
          }
        });
      }
    });

    // recipe modals  (used ingredients)
    $("a.usedIng").on("click", function(event) {
      event.preventDefault()
      let ingID = $(this).attr("id");
      let userUrl = '/get_ingredient?ing_id=' + ingID + '&edit=True';
      let ingJson = $.getJSON(userUrl, function(ing){
        reload();        
        $("#submit-button").hide();
        $("#inputNumber").hide();
        $("#selectUnits").hide();
        $("input[name=inputIngredient]").val(ing.name).attr("readonly", true);
        select.find("option").remove();
        $.each(ing.unit_list, function(key, entry){
          select.append($('<option></option>').attr('value', entry).text(entry));
        });
        $("#hiddenInput").val(ingID);          
        if (typeof ing.image !== "undefined"){
          $(".img-modal").attr("src", imgModal + ing.image);
        }
        $("#addIngredientModal").modal("show"); 
                 
      });
    });

    // recipe modals  (unused ingredients)
    $("a.unusedIng").on("click", function(event) {      
      event.preventDefault(); 
      $("form").attr("action", "/buy?json=true");
      $("#inputNumber").hide();
      $("#selectUnits").hide();
      $("#submit-button").text("Add to shopping list");
      $("#submit-button").show();      
      let ingID = $(this).attr("id");
      let userUrl = '/get_ingredient?ing_id=' + ingID ;
      let ingJson = $.getJSON(userUrl, function(e){
        $("#hiddenInput").val(ingID);
        $("input[name=inputIngredient]").val(e.name).attr("readonly", true);
        $.each(e.shoppingListUnits, function(key, entry){
          select.append($('<option></option>').attr('value', entry).text(entry));
        });          
        if (typeof e.image !== "undefined"){
          $(".img-modal").attr("src", imgModal + e.image);
        }
        $("#addIngredientModal").modal("show");     
            
        });        
      });
    // Add ingredient in "Cooking" location
    $("form").on("submit", function (e){
      if ($("#submit-button").text() == "Add to shopping list"){      
        var request = $("form").serialize() + "&json=True";
        $.post("/buy", request, function (response){
          if (response.status == "ok"){
            showMassage("Ingredient is added to shopping list");
          } else if (response.status == "bad" & response.error == "sql"){
            showMassage("Ingredient alredy in shopping list", "err");
          } else {
            showMassage("Error! Ingredient is not added", "err");
          }
        });
        $("#addIngredientModal").modal("hide");
        e.preventDefault();
      }
    });

    $("#more-button").on("click", function() {
      $(".hidden-recipe").removeClass(["hidden-recipe"])
      $("#more-button").attr("disabled", true)
    });

    // Show recipe descriplion
    
    $(".button-recipe").on("click",function(){
      var id = $(this).attr("id");      
      var img = $('#' + id + ' img').attr("src");
      var title = $('#' + id + ' h4').text();      
      $("img.recipe-modal-img").attr("src", img);
      $("#showrecipeModalTitle").text(title);
      $(".modal-hidden").attr("id", id).val(title);
      var recipeUrl = "/get_recipe_details?recipe_id=" + id;
      $("ol.recipe-steps").find("li").remove();
      var recipe = $.getJSON(recipeUrl, function(recipe){             
        $.each(recipe[0].steps, function(key, val){                   
          $("ol.recipe-steps").append($("<li></li>").text(val.step));
        });
        $("#showrecipeModal").modal("show");        
      });      
      
    });   


    $(".button-add-fav").on("click", function(){        
        var id = $(".modal-hidden").attr("id");                
        $.post("/favorite", {recipe_id : id}, function(response){
          console.log(response.status);
          if (response.status == "ok") {
            showMassage("Recipe added to favorite", "ok")
          } else if (response.status == "bad" & response.error == "sql") {
            showMassage("Recipe alredy in favorite", "err")

          } else {
            showMassage("Recipe is not added", "err")
          }                    
        });                    
      });

    $(".show-recipe").on("click", function(event){
      event.preventDefault();
      let id =$(this).attr("id");
      userUrl = '/get_recipe_details?recipe_id=' + id;
             
      $(".hidden-recipe.openned").slideUp(400).removeClass("openned");
      $("#" + id + ".hidden-recipe").slideDown(400).addClass("openned");
    });


    $(".btn-group .close-button").on("click", function() {
      let id = ($(this).attr("id"));
      $(".delete." + id).hide();
      let data = {recipe_id : id, delete : true}
      $.post("/favorite", data, function(response){
        if (response.status == "ok"){
          showMassage("Successfuly deleted")
        } else {
          showMassage("Can't delete recipe", "err")
          $("." + id).show();
        }

      });
    });
});


