function getUrlVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        if(!(hash[0] in vars)) {
        	vars[hash[0]] = [];
        }
        vars[hash[0]].push(hash[1]);
    }
    return vars;
}

function get_number_of_filters() 
{
	return $('#search_form div.data_row').length;
}

function get_template_row()
{
	return $('#search_form div.data_row:first');
}

function extract_resources()
{
	var $row = get_template_row();
	var $options = $row.find('option');
	var resources = new Array();
	for (var i = 0; i < $options.length; i++) {
		var $option = $options[i];
		resources.push({'name': $option.label, 'value': $option.value });
	}
	return resources;
}

function remove_row(element) {
	var $row = $(element).parents('div.data_row:first');
	$row.remove();
	
	if (get_number_of_filters() == 1) {
		$('#search_form div.data_row div.cancel-icon').attr('hidden', '');	
	}    	
}

function add_extra_row(resource, value)
{
	var $form = $('#search_form');
	var $row = get_template_row();
	var $last_row = $form.find('div.data_row:last');
	$clone = $last_row.clone();

	if (resource !== undefined && value !== undefined) {
    	$clone.find('select').val(resource);
		$clone.find('input').val(value);    	    		
	}
	else {
		$clone.find('input').val('');
	}
	$last_row.after($clone);
	$('#search_form div.data_row div.cancel-icon').removeAttr('hidden');    	
}

$(document).ready(function() {
	var arguments = getUrlVars();   
	resources = extract_resources();
	
	if ('resource' in arguments && 'value' in arguments) { 
		url_resources = arguments.resource;
		url_values = arguments.value;			
		if (url_resources.length == url_values.length && url_resources.length > 0) {
			
			$row = get_template_row();
	    	$row.find('select').val(url_resources[0]);
    		$row.find('input').val(url_values[0]);    	    		
			
	    	for (var i = 1; i < url_resources.length; i++) {
	    		var resource = url_resources[i];
	    		var value = url_values[i];
	    		add_extra_row(resource, value);
	    	}    	    	
		}
	}
});