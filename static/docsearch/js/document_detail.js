function textCounter(field, id) {
 var id = "hidden-place" + id;
 //alert(id);
 var hidden_place = document.getElementById(id);
 var maxlimit = 20;

 if ( field.value.length > maxlimit ) {
  //field.value = field.value.substring( 0, maxlimit );


  var html = [
        '<div>',
        '<div class="alert alert-danger warning-panel" role="alert">Exceeded the number of allowed character!</div>',
        '</div>',
      ].join("\n");

  hidden_place.innerHTML = html;

  return false;
 } else {

    //countfield.value = maxlimit - field.value.length;
    hidden_place.innerHTML = "";
    return false;

 }
};

function make_comment(doc_url) {
          $(".ajaxform").submit(function(e) {
                //alert(e.target.id);
                var text = $('textarea#comment-text').val();
                //alert(text);
                $.ajax({
                    type: 'GET',
                    url: doc_url,
                    dataType: "json",
                    data: {
                            'value': text,
                             'type': 'comment'
                          },
                    success: function(data) {
                        //alert(data.value.comment_text);
                        if (Object.keys(data.value).length === 0) {

                        } else {

                        var contest = document.getElementById("comment-div");
                        var published_at = data.value.published_at;
                        var text = data.value.comment_text;

                        var new_block_html = [
                            '<div class="well">',
                            '<span class="label label-default">Comment</span>',
                            '<p><b>Published at: </b>' + published_at + ' </p>',
                            '<p><b>Text:</b></p>',
                            '<div class="well">',
                            '<p>' + text + '</p>',
                            '</div>',
                            '</div>',
                        ].join("\n");

                        contest.innerHTML = new_block_html + contest.innerHTML;

                        document.getElementById("comment-text").value = "";

                        }
                    }
                });
                e.preventDefault();

          });
};