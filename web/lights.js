(function(){

    var matcher = /\s*(?:((?:(?:\\\.|[^.,])+\.?)+)\s*([!~><=]=|[><])\s*("|')?((?:\\\3|.)*?)\3|(.+?))\s*(?:,|$)/g;

    function resolve(element, data) {

	data = data.match(/(?:\\\.|[^.])+(?=\.|$)/g);

	var cur = jQuery.data(element)[data.shift()];

	while (cur && data[0]) {
	    cur = cur[data.shift()];
	}

	return cur || undefined;

    }

    jQuery.expr[':'].data = function(el, i, match) {

	matcher.lastIndex = 0;

	var expr = match[3],
	    m,
	    check, val,
	    allMatch = null,
	    foundMatch = false;

	while (m = matcher.exec(expr)) {

	    check = m[4];
	    val = resolve(el, m[1] || m[5]);

	    switch (m[2]) {
	    case '==': foundMatch = val == check; break;
	    case '!=': foundMatch = val != check; break;
	    case '<=': foundMatch = val <= check; break;
	    case '>=': foundMatch = val >= check; break;
	    case '~=': foundMatch = RegExp(check).test(val); break;
	    case '>': foundMatch = val > check; break;
	    case '<': foundMatch = val < check; break;
	    default: if (m[5]) foundMatch = !!val;
	    }

	    allMatch = allMatch === null ? foundMatch : allMatch && foundMatch;

	}

	return allMatch;

    };

}());

function addFrame() {
    var parent = $("#animation-editor-form");
    var frames = $("#animation-editor").data('frames');
    $("#animation-editor").data('frames', frames+1);
    parent.append(
	$("<div>").addClass("frame-container").data("frame", frames+1).append(
	    $("<div>").addClass("frame-options").data("frame", frames+1).append(
		$("<span>").addClass("frame-number").data("frame", frames+1).text("Frame #" + (frames+1)),
		document.createTextNode("&bull;"),
		$("<label>").append(
		    document.createTextNode("Duration: "),
		    $("<input>").attr("type", "number").val(1).attr("max", 3600).attr("min", .042).data("frame", frames+1),
		    document.createTextNode("s")
		),
		$("<input>").attr('type', 'button').data('frame', frames+1).val("+").click(function() {
		    addSegment($(this).data('frame'));
		})
	    ),
	    $("<div>").addClass("frame-segment-list").data("frame", frames+1).data('segments', 0)
	)
    );
}

function addSegment(frame) {
    var segmentList = $(".frame-segment-list:data(frame==" + frame + ")");
    var segment = segmentList.data('segments') + 1;
    segmentList.data('segments', segment);

    var checkboxes = [];
    for (var i = 0; i < 50; i++) {
	checkboxes.push($("<label>").append(
	    document.createTextNode((i < 9 ? "0" : "") + (i + 1)),
	    $("<input>").attr('type', 'checkbox').addClass('light-control').data('frame', frame).data('segment', segment).data('light', i).change(function() {
		$("input[type=checkbox]:data(frame==" + frame + ",light==" + $(this).data("light") + ",segment!=" + $(this).data("segment") + ")").prop('disabled', $(this).is(':checked'));
	    })
	));

	if (i == 24) checkboxes.push($("<br>"));
    }
    
    segmentList.append(
	$("<div>").addClass("segment-container").data('frame', frame).data('segment', segment).append(
	    $("<div>").addClass('segment-settings').append(
		$("<input>").attr('type', 'button').val('X').click(function(){
		    $(".segment-container:data(frame==" + frame + ",segment==" + segment + ")").remove();
		}),
		$("<input>").attr('type', 'color').val('#FFFFFF').data('frame', frame).data('segment', segment),
		$("<input>").addClass('segment-brightness').attr('type', 'range').attr('min', 0).attr('max', 255).val(255).data('frame', frame).data('segment', segment),
		$("<input>").attr('type', 'checkbox').addClass('segment-all-brightness').data('frame', frame).data('segment', segment)
	    ),
	    $("<div>").addClass('segment-lights').append(checkboxes)
	)
    );
}

$(function() {
    $("#add-frame").click(function(){addFrame();});
});
