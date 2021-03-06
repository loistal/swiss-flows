function draw(geo_data, current_filename, current_nodes, current_from_date, current_to_date, is_directed) {

  "use strict";
  var margin = 0,
      width = 960 - margin,
      height = 780 - margin;

  var svg = d3.select("body")
      .append("svg")
      .attr("width", width + margin)
      .attr("height", height + margin)
      .append('g')
      .attr('class', 'map');

  var projection = d3.geo.mercator()
                         .scale(11000)
                         .center([8.03667, 46.70111]) // because of scroll, not perfectly centered on CH
                         .translate( [width / 2, height / 2]);

  var path = d3.geo.path().projection(projection);

  var map = svg.selectAll('path')
               .data(geo_data.features)
               .enter()
               .append('path')
               .attr('d', path)
               .style('fill', '#FFFFFF')
               .style('stroke', 'black')
               .style('stroke-width', 0.5);

  function plot_points(data) {

      // Find the maximum weight among all nodes
      var weight_max = d3.max(data, function(node) {
          return node['weight'];
      });

      // Scale the radius so that circles are visible if if they have extreme weights
      var radius = d3.scale.sqrt()
                     .domain([0, weight_max])
                     .range([0, 60]);

      // Draw circles
      svg.append('svg')
         .attr("class", "bubble")
         .selectAll("circle")
         .data(data)
         .enter()
         .append("circle")
         .attr('cx', function(node) {
            var node_longitude = node['node']['position'][1];
            var node_latitude = node['node']['position'][0];

            return projection([node_longitude, node_latitude])[0];
          })
         .attr('cy', function(node) {
            var node_longitude = node['node']['position'][1];
            var node_latitude = node['node']['position'][0];

            return projection([node_longitude, node_latitude])[1];
          })
         .attr('r', function(node) {
              return radius(node['weight']);
         })
         .attr('fill', function(node){
          var population = node['node']['population'];

          if(population <= 50000) {
            return "#FFE0B2";
          } else if( (population > 50000) && (population <= 100000) ) {
            return "#FFCC80";
          } else if( (population > 100000) && (population <= 150000) ) {
            return "#FFA726";
          } else if( (population > 150000) && (population <= 200000) ) {
            return "#FB8C00";
          } else if( (population > 200000) && (population <= 250000) ) {
            return "#EF6C00";
          } else {
            return "#E65100";
          }

         })
         .attr('stroke', 'black')
         .attr('stroke-width', 0.7)
         .attr('opacity', 0.7);

      // Write node name on top
      svg.selectAll("text")
         .data(data)
         .enter()
         .append("text")
         .attr("x", function(node) {

          var node_longitude = node['node']['position'][1];
          var node_latitude = node['node']['position'][0];

           // The node's name is placed on its right side
           return projection([node_longitude, node_latitude])[0] + radius(node['weight']) + 1;
         })
         .attr("y", function(node) {

          var node_longitude = node['node']['position'][1];
          var node_latitude = node['node']['position'][0];

          if( (node['node']['name'] == "Basel") || (node['node']['name'] == "Verbania") || (node['node']['name'] == "Mulhouse") || (node['node']['name'] == "Koniz")) {
           return projection([node_longitude, node_latitude])[1] + 10;
          } else {
            return projection([node_longitude, node_latitude])[1];
          }
         })
         .text( function (node) {
          return node['node']['name'];
         })
         .attr("font-family", "sans-serif")
         .attr("font-size", "15px")
         .attr("fill", "black");

  }

  function plot_flows(data) {

    console.log(current_from_date);
    console.log(current_to_date);

    // Define the reusable arrow tip
    svg.append("svg:defs")
        .append("svg:marker")
        .attr("id", "triangle")
        .attr("refX", 6)
        .attr("refY", 6)
        .attr("markerWidth", 30)
        .attr("markerHeight", 30)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M 0 0 12 6 0 12 3 6")
        .attr("opacity", 0.5)
        .style("fill", "blue");

    // Plot the lines programatically
    svg.selectAll("line")
       .data(data)
       .enter()
       .append("line")
       .attr("x1", function(flow) {

         // Coordinates
         var src_longitude = flow['src']['position'][1];
         var src_latitude = flow['src']['position'][0];
         var dst_longitude = flow['dst']['position'][1];
         var dest_latitude = flow['dst']['position'][0];

         var orientation = src_longitude - dst_longitude;
         if(orientation < 0) {
          return projection([src_longitude, src_latitude])[0] - 5;
         } else {
          return projection([src_longitude, src_latitude])[0] + 5;
         }
       })
       .attr("y1", function(flow) {

         // Coordinates
         var src_longitude = flow['src']['position'][1];
         var src_latitude = flow['src']['position'][0];

         return projection([src_longitude, src_latitude])[1];
       })
       .attr("x2", function(flow) {

         // Coordinates
         var src_longitude = flow['src']['position'][1];
         var src_latitude = flow['src']['position'][0];
         var dst_longitude = flow['dst']['position'][1];
         var dest_latitude = flow['dst']['position'][0];

         var orientation = src_longitude - dst_longitude;
         if(orientation < 0) {
          return projection([dst_longitude, dest_latitude])[0] - 5;
         } else {
          return projection([dst_longitude, dest_latitude])[0] + 5;
         }
       })
       .attr("y2", function(flow) {

         // Coordinates
         var dst_longitude = flow['dst']['position'][1];
         var dest_latitude = flow['dst']['position'][0];

         return projection([dst_longitude, dest_latitude])[1];
       })
       .attr("stroke-width", function(flow) {
         return flow['weight'] / 8;
       })
       .attr("stroke", "blue")
       .style("stroke-opacity", function(flow) {
        var flow_start_date = new Date(flow['start_date']);
        var flow_end_date = new Date(flow['end_date']);

        if( (flow_start_date >= current_from_date) && (flow_end_date <= current_to_date) ) {
          return 0.6;
        } else {
          return 0.6;
          //return 0;
        }
       })
       .attr("marker-end", function(flow) {
          var flow_start_date = new Date(flow['start_date']);
          var flow_end_date = new Date(flow['end_date']);

          if( (flow_start_date >= current_from_date) && (flow_end_date <= current_to_date) && (is_directed)) {
            return "url(#triangle)";
          } else {
            return null;
          }
        });

  }

  // Load the nodes and plot them
  d3.json(current_nodes, function(error, data){
    if(error){
      console.log(error);
    }

    plot_points(data);
  });

  // Load the flows and plot them
  d3.json(current_filename, function(error, data){
    if(error){
      console.log(error);
    }

    plot_flows(data);
  });

};
