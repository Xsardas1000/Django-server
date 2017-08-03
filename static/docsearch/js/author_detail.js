$(document).ready(function() {
            $("#id_like").click(function(event) {
                $.ajax({
                    type: 'GET',
                    url: '/docsearch/author_detail/',
                    dataType: "json",
                    data: {'value': 10},
                    success: function(data) {
                        alert(1);
                    });
                }
            });
});