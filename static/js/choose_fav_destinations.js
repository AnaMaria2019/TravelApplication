var selected_destinations = []
var number_destinations_selected = 0;

function selectDestination() {
    // When we click, the target element is either the div with id=target, or the div with class=overlay
    var target_div = event.target;
    var parent = target_div.parentElement;
    var direct_children = parent.children;
    console.log(target_div);
    var is_none = true;

    for(var i = 0; i < direct_children.length; i++){
        if(direct_children[i].getAttribute('id') == 'selected' || direct_children[i].getAttribute('id') == 'selected-icon'){
            if(direct_children[i].style.display == 'none' && number_destinations_selected < 5)
                direct_children[i].style.display = "block";
            else if(direct_children[i].style.display == 'none' && number_destinations_selected == 5){
                alert("You have reached the limit number of choices! You can select maximum 5 destinations!");
                return;
            }
            else{
                direct_children[i].style.display = "none";
                is_none = false;
            }
        }

        if(direct_children[i].classList.contains("destination-2")){
            //console.log(direct_children[i]);
            //console.log(direct_children[i].firstElementChild);
            var destination_name = direct_children[i].firstChild.textContent;
            //console.log(destination_name);
        }
    }
    
    //console.log(is_none);

    if(is_none && number_destinations_selected < 5){
        selected_destinations.push(destination_name);
        number_destinations_selected += 1;
        console.log(selected_destinations);
    }
    else if(!is_none){
        index = selected_destinations.indexOf(destination_name);
        selected_destinations.splice(index, 1);
        number_destinations_selected -= 1;
        console.log(selected_destinations);
    }
}


function csrfSafeMethod(method) {
    // These HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sendSelectedDestinations() {

    if (number_destinations_selected < 5){
        alert("You have to select 5 destinations");
        return;
    }
    // START: After the user clicked on the 'Save your favorites' button we can erase the button from the page and display
    // the one that goes to the Search-Form
    var target_a = event.target;
    var parent = target_a.parentElement.parentElement;
    parent.style.display = "none";
    document.getElementById("search-form-button-container").style.display = "block";
    // END

    document.getElementById("refresh-btn-container").style.display = "none";

    // START: After the chosen destinations are saved in the database we can delete from the page the cities
    destinations = document.getElementsByClassName("delete-after-save")

    for(var i = 0; i < destinations.length; i++){
        destinations[i].style.display = "none";
    }
    // END

    var csrftoken = $.cookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $('.ajaxProgress').show();
    $.ajax({
        type: "POST",
        url: "post_fav_cities",
        dataType: "json",
        async: true,
        data: {
            destinations: selected_destinations
        },
        success: function(json) {
            console.log(json.message); // MERGE
            $('.ajaxProgress').hide();
        }
    });
}