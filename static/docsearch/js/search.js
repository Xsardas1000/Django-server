function func_scroll(request_id) {
       $.ajax({
            type: 'GET',
            url: '/docsearch/search/scroll',
            dataType: "json",
            data: {'value': request_id},
            success: function(data) {
                for (var i = 0; i < data.value.length; i++) {
                    //alert(data.value[i].title);
                    var article = data.value[i];
                    var title = article.title;
                    var description = article.description;
                    var curr = article.prior_value + 1;
                    var weight = article.weight;
                    var archive_id = article.archive_id;
                    var published_at = article.published_at;
                    var article_url = '/docsearch/document/' + article.id.toString();

                    var par1 = "#" + curr.toString();
                    var par2 = curr.toString();



                    var html = [
                        '<div class="container-fluid doc-preview">',
                            '<div class="panel panel-default">',
                                '<div class="panel-heading"> <h3>' + title + '</h3></div>',
                                '<div class="panel-body"> </div>',
                                '<div>',
                                    '<button class="btn btn-primary descr-btn" type="button" data-toggle="collapse"',
                                         'data-target="#' + curr + '"',
                                         'aria-expanded="false" aria-controls="' + curr + '">',
                                         'Show document detail',
                                    '</button>',
                                    '<div class="collapse" id="' + curr + '">',
                                        '<div class="well descr-text">',
                                            '<p>' + description + '</p>',
                                        '</div>',
                                    '</div>',
                                '</div>',

                                '<ul class="list-group">',
                                    '<li class="list-group-item"><b>Weight: </b> ' + weight + '</li>',
                                    '<li class="list-group-item"><b>Archive id: </b> ' + archive_id +' </li>',
                                    '<li class="list-group-item"><b>Published_at: </b> ' + published_at + '</li>',
                                    '<li class="list-group-item"><a href="' + article_url + '"><b>Detail</b></a></li>',
                                '</ul>',
                            '</div>',
                        '</div>',
                    ].join("\n");

                    $("body").append(html);

                    var QUEUE = MathJax.Hub.queue;
                    var math = null;
                    var curr_id = "MathOutput" + curr.toString();

                    var math = document.getElementById(curr_id);
                    MathJax.Hub.Queue(["Typeset",MathJax.Hub,math]);
                }
            }
       });
};