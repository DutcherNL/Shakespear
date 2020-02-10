// This javascript code accompanies the Insert Module Fillers used in the PageDisplay class

// The onClick event. When clicked the position data needs to be changed in the form
function setInsertLocation() {
    document.getElementById('id_position').value = this.dataset.insertPosition;
    try {
        document.getElementById('id_container').value = this.dataset.insertContainer;
        document.getElementById('id_field_name').value = this.dataset.insertField_name;
    }
    catch(err){}
    document.getElementById('id_position_selected_marker').checked = true;
}

// Get all fillters and create event listeners on the above method
var fillers = document.getElementsByName('insert_module_filler')
for (var i = 0; i < fillers.length; i++) {
    fillers[i].addEventListener('click', setInsertLocation, false);
}