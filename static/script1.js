var canvas = $('canvas');
var context = canvas[0].getContext('2d');
var imageObj = new Image();

imageObj.onload = function() {
  $(canvas).attr({
    width : this.width,
    height: this.height
  });
  context.drawImage(imageObj,0,0);
};
imageObj.src = 'static/inputframe00.jpg';

var clicks = [];

function drawPolygon(){
  context.fillStyle = 'rgba(100,100,100,0.5)';
  context.strokeStyle = "#df4b26";
  context.lineWidth = 1;

  context.beginPath();
  context.moveTo(clicks[0].x, clicks[0].y);
  for(var i=1; i < clicks.length; i++) {
    context.lineTo(clicks[i].x,clicks[i].y);
  }
  context.closePath();
  context.fill();
  context.stroke();
};

function drawPoints(){
  context.strokeStyle = "#df4b26";
  context.lineJoin = "round";
  context.lineWidth = 5;

  for(var i=0; i < clicks.length; i++){
    context.beginPath();
    context.arc(clicks[i].x, clicks[i].y, 3, 0, 2 * Math.PI, false);
    context.fillStyle = '#ffffff';
    context.fill();
    context.lineWidth = 5;
    context.stroke();
  }
};

function redraw(){
  canvas.width = canvas.width; // Clears the canvas
  context.drawImage(imageObj,0,0);

  drawPolygon();
  drawPoints();
};

canvas.mouseup(function (e) {
    clicks.push({
      x: e.offsetX,
      y: e.offsetY
    });
    redraw();
  });

function reset() {
    clicks = [];
    redraw();
}

function back() {
//    sendData()
    history.back()
}

function sendData() {
//    var json_string = JSON.stringify(clicks);
    $.post( "/postmethod", {
      canvas_data: JSON.stringify(clicks)
    }, function(err, req, resp){
      console.log(resp);
    });
}

