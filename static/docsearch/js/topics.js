
      // Callback that creates and populates a data table,
      // instantiates the pie chart, passes in the data and
      // draws it.
      function drawChart(sections) {

        // Create the data table.
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'Topping');
        data.addColumn('number', 'Slices');
        //var sections = "{{sections}}";
        //alert(sections);

         var data_sections = new Array();
         var i = 0;
         {% for section in sections %}

          var name = '{{section.0}}';
          var number = {{section.1}};
          var section_array = new Array();
          section_array[0] = name;
          section_array[1] = number;
          //alert(name);
          //alert(forloop.counter);
          data_sections[i] = section_array;
          i = i + 1;

          {% endfor %}


        data.addRows(data_sections);

        // Set chart options

        var options = {
            'legend':'left',
            'title':'What sections are presented in the corpus',
            'is3D':false,
            'width':1000,
            'height':700
        }


        // Instantiate and draw our chart, passing in some options.
        var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
        chart.draw(data, options);


        var barchart_options = {title:'Barchart: How Much Pizza I Ate Last Night',
                       width:1000,
                       height:700,
                       legend: 'none'};
        var barchart = new google.visualization.BarChart(document.getElementById('barchart_div'));
        barchart.draw(data, barchart_options);

      }