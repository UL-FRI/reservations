// Parses URL and return variables in it as a hash map.
function getUrlVars()
{
    var vars = {}, hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        if(hash[0] in vars) {
        	vars[hash[0]].push(hash[1]);
        }
        else {
        	vars[hash[0]] = [hash[1]];
        }        
    }
    return vars;
}


// Add transformation to a given element.
// Add rules to css using javascript, 
// respecting major browser prefixes.
function setTransform($element, base_name, transformation) {
    var prefixes = ['', '-webkit-', '-moz-', '-o-', '-ms-']; 
	for(var i = 0; i < prefixes.length; i++) {
		$element.css(prefixes[i] + base_name, transformation);		
	}
}


// Load data and render table. It loads data (using ajax) and 
// calls renderTable when finished.
// Input:
// - $table: table to render into
// - start: start of the interval
// - zoom: zoom level
function loadDataAndRenderTable($table, start, zoom) {
	return $.when(loadData(start, zoom)).then(	
	  function (data) {
        renderTable($table, data);
        return data;
      }	
    );
}


// Load data used to render a table.
// Input:
// - start: start of the interval.
// - zoom: zoom level, defaults to one.
// - ids: ids of reservables. If it is undefined, all reservables in the reservableset are shown.
// TODO: handle errors gracefully.
function loadData(start, zoom, ids) {
	zoom = (typeof zoom !== 'undefined' ? zoom : 1);
	var link = "?format=json&zoom=" + zoom;
	if (ids !== undefined) {
		for(var i = 0; i < ids.length; i++) {
			link += '&id=' + ids[i];
		}
	}
	if (start !== undefined) {
		var start_date = $.format.date(start, "yyyy-MM-dd HH:mm");
		link += "&start=" + start_date;					
	}
	return $.ajax({
		 url: link,
		 dataType: 'json',
		 success: function( data ) {
			return data;
		 },
		 error: function( data ) {
			 return false;   
		 }
	});
}

// Get details of the given reservation using ajax call.
// The details are written in the element title attribute.
// Input:
// - id: reservation id
// - $element: the element to write received data into.
function getReservationDetails(id, $element) {
	var title = $element.attr('title');	
	if (title === undefined) {
		var link = Urls['reservation-detail'](id)
		
		return $.ajax({
			 url: link,
			 dataType: 'json',
			 success: function( data ) {
				//$element.html(data.reason);
				$element.attr('title', data.reason);
				return data;
			 },
			 error: function( data ) {
				 return false;   
			 }
		});
    }
	return title;
}

// Fill tbody with reservable slugs
function fill_reservable_slugs($tbody, reservables_reservations) {
	for (var i = 0; i < reservables_reservations.length; i++) {
		var slug = reservables_reservations[i].reservable.slug;
		var $tr = $('<tr>', {class: 'tabletd'});
		var $td = $('<td>', {class: 'tabletd'})		
		var url = Urls['reservable-detail'](reservables_reservations[i].reservable.id);
		$td.append($('<a>', {href: url}).text(slug));
		$tr.append($td);
		$tbody.append($tr);			
	}		
}

function sort_reservables(data) {
	// data.custom_sort_order is csv of reservable ids
	// not all ids are included in the custom surt order
	var split = data.custom_sort_order.split(',');
	var custom_sort_order = split.map(Number);
	function indexOf(array, val) {
		for(var i=0; i<array.length; i++) {
			if (array[i] == val) {
				return i;
			}
		}
		return -1;
	}
	function reservable_cmp(row1, row2) {
		// Compare two rows from res_list array
		// Compare them according to the position
		// of reservable id in the custom_sort_order 
		// array.
		var id1 = row1.reservable.id;
		var id2 = row2.reservable.id;
		var i1 = indexOf(custom_sort_order, id1);
		var i2 = indexOf(custom_sort_order, id2);
		if(i1 == -1 && i2 == -1) 
			return row1.reservable.slug.localeCompare(row2.reservable.slug);
		if(i1 == -1)
			return 1;
		if(i2 == -1)
			return -1;
		return i1 - i2
	}
	data.res_list.sort(reservable_cmp);
	if ($('#table_reservables1 > tbody > tr').length == 0) {
		fill_reservable_slugs($('#table_reservables1 > tbody'), data.res_list);
	}
	if ($('#table_reservables > tbody > tr').length == 0) {
		fill_reservable_slugs($('#table_reservables > tbody'), data.res_list);
	}	
}

// Render table from the given data.
// Input: 
// - $table: element to render into.
// - data: data used to render table.
function renderTable($table, data) {
	$table.find('thead').remove();
	$table.find('tbody').remove();
	
	var time_span = [moment(data.time_list[0].start), moment(data.time_list[data.time_list.length - 1].end)];
	
	// Custom sort reservables for each user
	sort_reservables(data);
	var reservables_reservations = data.res_list;
		
	// Add cols for column highligthing
	var $colgroup = $( '<colgroup>' );
	for (var i = 0; i < data.time_list.length; i++) {
		$colgroup.append($( '<col>' ));
	}
	$colgroup.prependTo($table);
	
	var $th = $( '<thead>' );
	var $tr = $( '<tr>' );
	
	var start_time_format = data.label_fmts.start;
	var end_time_format = data.label_fmts.end;
	
	// Output header
	for (var i = 0; i < data.time_list.length; i++) {
		var start_time = date(start_time_format, moment(data.time_list[i].start)._d) ;
		var end_time = date(end_time_format, moment(data.time_list[i].end)._d) ;
		$tr.append($( '<th> ').text(start_time + " - " + end_time));
	}
	$th.append($tr);
	$table.append($th);
	
	
	// Output body
	var $tbody = $('<tbody>');
	for (var i = 0; i < reservables_reservations.length; i++) {
		var reservable_reservations = reservables_reservations[i];
		var reservable = reservable_reservations.reservable;	
		 										
		var $tr = $('<tr>');
		
		for (var j = 0; j < reservable_reservations.reservations.length; j++) {				
			var column = reservable_reservations.reservations[j];
			
			// Prepare start and end date for linking
			var start_date = $.format.date(column.start, "yyyy-MM-dd HH:mm");
			var end_date = $.format.date(column.end, "yyyy-MM-dd HH:mm");

			// Prepare links on clik on table cells. If cell in empty, the list view is shown.
			var link = Urls['reservation-list']() + '?start=' + start_date + '&end=' + end_date + '&reservables=' + reservable.id;
			
			// Prepare cell css. Defaults to empty cell.
			var st = "tableempty";
			var $td = $('<td>').addClass("tabletd");
			
			// Every reservation gets css class reservation_id_#id. 
			// Used to highligth entire reservation on mouse hover.
			for(var tmp=0; tmp < column.reservations.length; tmp++) {
				var reservation_id = column.reservations[tmp];
				$td.addClass('reservation_id_' + reservation_id);				
			}
			
			if (column.reservations.length > 0) {
				// Is there only one reservation for this reservable in this column?
				st = ((column.reservations.length == 1) ? "tablesingle":"tablemulti");

				// When there in only one reservation in column open 
				// its detail view on click.
				if (column.reservations.length == 1) {
					link = Urls['reservation-detail'](column.reservations[0])
				}
				
				// Add reservations data to the column, used for details retrieval on mouse hover 
				// over the cell. I gues angularjs would really shine here.
				$td.data('reservation_ids', column.reservations);
				$td.mouseenter( 
						  function() { 					
							  var reservation_ids = $(this).data('reservation_ids');
							  for(var tmp = 0; tmp < reservation_ids.length; tmp++) {
								  var reservation_id = reservation_ids[tmp];							  
								  getReservationDetails(reservation_id, $(this));
								  $('.reservation_id_' + reservation_id).css('background', '#BCBFE8');
							  }
						  } )
					   .mouseleave( 
						  function() {
							  var reservation_ids = $(this).data('reservation_ids');
							  $(this).html("&nbsp");
							  for(var tmp = 0; tmp < reservation_ids.length; tmp++) {
								  var reservation_id = reservation_ids[tmp];
								  $('.reservation_id_' + reservation_id).css('background', '');
							  }
						  } 
				);
			}
			// Add attribute link to the cell
			$td.attr('link', link);
            $td.click(
                function() {
                	// Open modal dialog on click. 
                	$this = $(this);
                	$('#myModal').foundation('reveal', 'open', $(this).attr('link'));
                }
            );			
			$td.addClass(st).html('&nbsp');
			$tr.append($td);
		}
		$tbody.append($tr);
	}	
	$table.append($tbody);

	
	// Set *selected class to cells that need hightligth
	$table.find('td').hover(function() {
		 //var cells = $(this).parents('table').find('col:eq('+$(this).index()+')');
		var $td = $(this);
		var $row = $(this).parent();
		var colindex = $(this).index() + 1;
		 
		var cells = $table.find('tr td.tablesingle:nth-child(' + colindex + ')').add($row.find('td'));
		cells.toggleClass('tablesingleselected');

		var cells = $table.find('tr td.tableempty:nth-child(' + colindex + ')').add($row.find('td'));
		cells.toggleClass('tableemptyselected');
	});
	
	// Append entire data to the table. Maybe we will need it later.
	$table.data('json', data);
}

// Resize tables.
function resize_tables() {
	var names = ['#row_yesterday2',  '#row_yesterday', '#row_today', '#row_tomorrow', '#row_tomorrow2', '#row_reservables', '#row_reservables1'];
	var width = $('#row_anchor').width();
	
	// Get the maximum height of the title row
	// for all tables. 
	// Then set it to the that value.
	var max_row_height = 0;
	for(var i = 0; i < names.length; i++) {
		var name = names[i];
		var current_height = $(name + ' tr').eq(0).height();
		if (current_height > max_row_height) {
			max_row_height = current_height;
		}
	}
	for(var i = 0; i < names.length; i++) {
		var name = names[i];
		$(name + ' tr').eq(0).height(max_row_height);
	}
	
	// Set the heigth of the two static rows (reservables on the left and
	// right hand side of the tables) to be the same as the
	// height of the main table.
	$('#wush_tables').height($('#row_today').height());	
	$('#row_reservables').height($('#row_today').height());
	$('#row_reservables').width($('#table_reservables').width());
	$('#row_reservables1').height($('#row_today').height());
	$('#row_reservables1').width($('#table_reservables1').width());
}


// Position tables
function position_tables() {	
	//necessary since ids change
	var row_elements = row_ids.reduce(function (array, id) { array.push($('#' + id)); return array; }, []);
	var row_widths = row_elements.reduce(function(combined, $element) { combined.push($element.width()); return combined;  }, []);
	var row_width = $('#row_anchor').width();
	var table_elements = row_elements.reduce(
			function(combined, $row) { 
				combined.push($row.find('table')); 
				return combined;  
				}, []);	
	// First take care of the resizing.
	resize_tables();
		
	var position = $('#row_anchor').offset();
	var base_x_position = position.left;	
	var reservables_width = $('#table_reservables').width();
	var minimim_remaining_width = 400;
	var window_width = $(window).width();
	var remaining_width = window_width - row_width;
	var centered_index = 2;
		
	var widths = table_elements.reduce(function(combined, $element) { combined.push($element.width()); return combined;  }, []);
	
	// Hide row_yesterday2 and row_tomorrow2
 	setTransform($('#row_yesterday2'), 'transform', 'translate3d(' + (- 2 * widths[0]) + 'px,0,0)');
 	setTransform($('#row_tomorrow2'), 'transform', 'translate3d(' + (2 * window_width) +'px,0,0)');	

 	// Middle tree tables (today, yesterday, tomorrow)
	var tables = [table_elements[centered_index-1], table_elements[centered_index], table_elements[centered_index+1]];
	var rows = [row_elements[centered_index-1], row_elements[centered_index], row_elements[centered_index+1]];
	
	// positions of all rows
	var left_row_left = 10;	
	// Remove yesterday table out of view if there is not enough space.
	if (remaining_width < minimim_remaining_width) {
		left_row_left = - row_widths[centered_index-1] - 20;
    }
	var right_row_left = base_x_position + 10 + row_width;	
	// Remove tomorrow table out of view if there is not enough space.
	if (remaining_width < minimim_remaining_width) {
		right_row_left = window_width + 20;
	}
	// Calculated positions of yesterday, today and tomorrow table
	var positions = [left_row_left, base_x_position + reservables_width, right_row_left];
	var calculated_row_widths = [base_x_position - 20, row_width - 2*reservables_width, base_x_position - 20];
	var row_scales = [calculated_row_widths[0]/row_width, calculated_row_widths[1]/row_width, calculated_row_widths[2]/row_width];
	var table_scales = [row_width/widths[centered_index-1], row_width/widths[centered_index], row_width/widths[centered_index+1]];
	// all transform origins //	
	var rows_transform_origin = ['0 0 0', '0 0 0', '0 0 0'];
	var tables_transform_origin = ['0 0 0', '0 0 0', '0 0 0'];
	
	// Position static tables
	$('#row_reservables').css('left', base_x_position);	
	$('#row_reservables1').css('left', base_x_position + row_width - reservables_width);
	
	// Set scale transformations
	for (var i = 0; i < tables.length; i++) {
		setTransform(rows[i], 'transform-origin', rows_transform_origin[i]);
		setTransform(rows[i], 'transform', 'translate3d(' + positions[i] + 'px, 0, 0)  scaleX(' + row_scales[i] +')');
		setTransform(tables[i], 'transform-origin', tables_transform_origin[i]);
		setTransform(tables[i], 'transform', 'scaleX(' + table_scales[i] +')');		
	}
	
	// Create zoom in and zoom out modal dialogs.
	// This does not belong to this function, move out of the way!
	var data = $('#row_today table').data('json');
	if (data != undefined) {
		var $zoom_in_modal = $('#zoom_in_modal div');
		var $zoom_out_modal = $('#zoom_out_modal div');
		$zoom_in_modal.text('');
		$zoom_out_modal.text('');
		
		$close = $( '<a>' ).attr('href', '#close').addClass('close').text('X');		
		$zoom_out_modal.append($close).append($('<br>'));
		
		$close = $( '<a>' ).attr('href', '#close').addClass('close').text('X');
		$zoom_in_modal.append($close).append($('<br>'));
		
		if (data.label_fmts.zoom_out) { 
	    	for (var i = 0; i < data.zoom_out_list.length; i++) {
	    		var entry = data.zoom_out_list[i];
	    		for(var j = 0; j < entry.ranges.length; j++) {
	    			var range = entry.ranges[j];    			
	    			var baseurl = Urls['time_view'](data.reservable_set_slug, data.reservable_type);
	    			var range_start_time = date("Y-m-d H:i:s", moment(range.start)._d);
	    			var range_end_time = date("Y-m-d H:i:s", moment(range.end)._d);
	    			var urlargs = 'start=' + range_start_time + '&end=' + range_end_time + '&zoom=' + data.zoom_out;     			
	    			var text = date(data.label_fmts.zoom_out, moment(range.start)._d) + ' - ' + 
	    			           date(data.label_fmts.zoom_out, moment(range.end)._d);
	    			var $a = $( '<a>' ).attr('href', baseurl + '?' + urlargs).text(text);
	    			$zoom_out_modal.append($a);
	    		}
	    	}
		}

		if (data.label_fmts.zoom_in) { 
	    	for (var i = 0; i < data.zoom_in_list.length; i++) {
	    		var entry = data.zoom_in_list[i];
	    		for(var j = 0; j < entry.ranges.length; j++) {
	    			var range = entry.ranges[j];    			
	    			var baseurl = Urls['time_view'](data.reservable_set_slug, data.reservable_type);
	    			var range_start_time = date("Y-m-d H:i:s", moment(range.start)._d);
	    			var range_end_time = date("Y-m-d H:i:s", moment(range.end)._d);
	    			var urlargs = 'start=' + range_start_time + '&end=' + range_end_time + '&zoom=' + data.zoom_in;     			
	    			var text = date(data.label_fmts.zoom_in, moment(range.start)._d) + ' - ' + 
	    			           date(data.label_fmts.zoom_in, moment(range.end)._d);
	    			var $a = $( '<a>' ).attr('href', baseurl + '?' + urlargs).text(text);
	    			$zoom_in_modal.append($a).append($('<br>'));
	    		}
	    	}
		}
	}
}

// Move tables left or right (depending on the direction).
function wush(direction) {	
	$('#wush_right').off('click');
	$('#wush_left').off('click');	
	
	var width = $('#row_anchor').width();

	var row_elements = row_ids.reduce(function (array, id) { array.push($('#' + id)); return array; }, []);

	var selector = {'1': ['#row_yesterday2 table', 'prev_time', '#row_tomorrow2 table', 4], 
			       '-1': ['#row_tomorrow2 table', 'next_time', '#row_yesterday2 table', 0]};
		
	// Get the data of the today table.
	// Data is appended to the table (done when rendering).
	var json_data = $(selector[direction][0]).data('json');
	
	// Which data to load?
	var load_date = moment(json_data[selector[direction][1]])._d;
	var new_current_moment = moment($('#row_today table').data('json')[selector[direction][1]]);
	
	var load_table_selector = selector[direction][2];
	var load_row_index = selector[direction][3];
	
	var $load_table = $(load_table_selector); 	
	// necessary since ids change
	for(var i = 0; i < row_ids.length; i++) {
	  var new_id_index = (i + direction + row_ids.length) % row_ids.length; 		
 	  var new_id = row_ids[new_id_index];
	  row_elements[i].attr('id', new_id);
	}	 
	$('#ajax_loader').css( "display", "block");	
	set_current_moment(new_current_moment)	
	load_promise = loadData(load_date, zoom);

	setTransform(row_elements[load_row_index], 'transition', 'visibility 0s');
	row_elements[load_row_index].css('visibility', 'hidden');
	
	position_tables();
	
	var deffs= [$.Deferred(), $.Deferred(),$.Deferred(), $.Deferred(), $.Deferred()];
	deffs[load_row_index].resolve(); // resolve hidden row
	
	for(var i = 0; i < row_elements.length; i++) {
	  (function (j) {		  
 		setTimeout(function() {
		        deffs[j].resolve(); //aborts the request when timed out
		      }, 1100); 

	    row_elements[j].one("transitionend webkitTransitionEnd oTransitionEnd MSTransitionEnd",	    		  
  	      function()
		  { 
		    deffs[j].resolve();
		  }
	    );
	  })(i);
	}

	$.when( load_promise, deffs[0], deffs[1], deffs[2], deffs[3], deffs[4], deffs[5]).then(
	  function (data) {
	    row_elements[load_row_index].css('visibility', 'visible');
	    setTransform(row_elements[load_row_index], 'transition', '');
		data = data[0];
		
	    setTimeout( 
		  function() {
 	    renderTable($load_table, data);
 	  	$('#ajax_loader').css( "display", "none");
 	  	// Make sure only one handler is attached
 		$('#wush_right').off('click');
 		$('#wush_left').off('click');
	  	$('#wush_right').on('click', function(e) { wush(-1); } );
	  	$('#wush_left').on('click', function(e) { wush(1); } );
		  }, 100);
	  }
	);    
 }	

function set_current_moment(moment) {
	// Unbind change event before changing value
    $( "#datepicker" ).unbind('change')
	var current_moment = datepicker.getMoment()
	if (moment.day() != current_moment.day() ||
		moment.month() != current_moment.month() ||
		moment.year() != current_moment.year()) {
		datepicker.setMoment(moment)
	}		
	$('#datepicker_opener').text(moment.format('dddd, Do MMMM  YYYY'))
	$( "#datepicker" ).change(function() {
		reload()
	})	
}

// Load all data.
// Input:
// - start: today table date.
function load_all(start) {
	$('#wush_right').off('click');
	$('#wush_left').off('click');	
	$('#ajax_loader').css( "display", "block");
	$.when(loadDataAndRenderTable($('#row_today table'), start, zoom)).then(
	 	function (data) {			
	 		var start_date = new Date(data.time_list[0].start);
	 		var end_date = new Date(data.time_list[data.time_list.length - 1].end);
			set_current_moment(moment(start_date))
	 		
	 		var tomorrow = moment(data.next_time)._d;
	 		var yesterday = moment(data.prev_time)._d;
	 						
	 		$.when(loadDataAndRenderTable($('#row_yesterday table'), yesterday, zoom),
	 			   loadDataAndRenderTable($('#row_tomorrow table'), tomorrow, zoom)
	 			   ).then(
	 			   function (data_yesterday, data_tomorrow) {
	 			 	   var tomorrow2 = moment(data_tomorrow.next_time)._d;
	 			 	   var yesterday2 = moment(data_yesterday.prev_time)._d;	 				   	 				   
	 			       $.when(loadDataAndRenderTable($('#row_yesterday2 table'), yesterday2, zoom),
	 			              loadDataAndRenderTable($('#row_tomorrow2 table'), tomorrow2, zoom)
	 			       ).then(
	 			           function(data) {
	 			               $('#ajax_loader').css( "display", "none");	        			       
	 			               resize_tables(); 			       
	 			               position_tables();
	 			               $('#wush_right').off('click');
	 			               $('#wush_left').off('click');
	 			               $('#wush_right').on('click', function(e) { wush(-1); } );
	 			               $('#wush_left').on('click', function(e) { wush(1); } );
	 			               // Show tables after 1 second delay
	 			               setTimeout( function () { 
	 			            	   for(var i = 0; i < row_ids.length; i++) {
	 			            		   var $table = $('#' + row_ids[i]).find('table');
	 			            		   $table.css('visibility', 'visible');
	 			            	   }
	 			               }, 1000 )
	 			           }
	 			       );
	 			    }
	 	    ); 			 		
	 	}	
    );
}

// Reload all data
function reload() {
	var start_date = datepicker.getDate()
    load_all(start_date);
}

// Initialize the page.
function init() {
	// hide static tables
	moment.locale('sl');
	$('#wush_nonjavascript_row').css('display', 'none');
	$('#table_static_div').hide();
	
	// display javascript tables
	$('#wush_tables').css('display', 'block');
	$('#wush_javascript_row').css('display', 'block');

	// enable wush efect on button click
	$('#wush_right').click( function(e) { wush(-1); } );
	$('#wush_left').click( function(e) {  wush(1); } );
	
	// Show 'loading' wheel
	$('#ajax_loader').css( "display", "block");
	
	datepicker = new Pikaday({ 
		field: document.getElementById('datepicker'),
		format: 'DD.MM.YYYY',
		firstDay: 1,
		i18n: {
		    previousMonth : 'Naslednji mesec',
		    nextMonth     : 'Prejšnji mesec',
		    months        : ['Januar','Februar','Marec','April','Maj','Junij','Julij','Avgust','September','Oktober','November','December'],
		    weekdays      : ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
		    weekdaysShort : ['Ned','Pon','Tor','Sre','Čet','Pet','Sob']
		},
		trigger: document.getElementById('datepicker_opener'),
		onChange: function () {
			document.getElementById('datepicker_opener').val = picker.toString()
		},
	  }
	)
	datepicker.setMoment(moment());

	$( "#datepicker" ).change(function() {
		reload()
	})

	var vars = getUrlVars();
	zoom = vars['zoom'] || '1';
	
	start = (vars['start'] || [undefined])[0];
	end = (vars['end'] || [undefined])[0];
	ids = vars['id'] || [];
	
	if(start != undefined) {
		start = moment(decodeURI(start))._d
	}	
	for(var i = 0; i < row_ids.length; i++) {
		var $table = $('#' + row_ids[i]).find('table');
		$table.css('visibility', 'hidden');
	}
	load_all(start);
}

// Reposition tables on window resize.
$( window ).resize(function() {
	position_tables();	
});


// Global variables. Should go away...
var row_ids = ['row_yesterday2',  'row_yesterday', 'row_today', 'row_tomorrow', 'row_tomorrow2'];
var zoom = 1;
var datepicker = {};
var ids = [];


// Load on document init.
$( document ).ready(function() {
	init();   
});