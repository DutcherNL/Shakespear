function toggleTab(evt, tabId) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("skp_progress_button");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabId).style.display = "block";
    evt.currentTarget.className += " active";
}


function showTitle(evt, tech_name) {
    tablinks = document.getElementsByClassName("skp_progress_hover_display");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].innerHTML = tech_name;
    }
}

function hideTitle(evt){
    tablinks = document.getElementsByClassName("skp_progress_hover_display");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].innerHTML = "";
    }
}