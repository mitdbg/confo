function autocomplete(id) {

	var cache = {},
	lastXhr;
	$( "#" + id ).autocomplete({
		minLength: 2,
		source: function( request, response ) {
			var term = request.term;
			if ( term in cache ) {
				response( cache[ term ] );
				return;
			}

			lastXhr = $.getJSON( "/authors/json/", request, function( data, status, xhr ) {
				cache[ term ] = data;
				if ( xhr === lastXhr ) {
					response( data );
				}
			});
		},
		select : function(event, ui) {
			var name = ui.item.value;
			console.log(name)
			$(location).attr('href',"/author/" + name + "/");//.replace(/ /gi,'_'));
		
		}
	});
}