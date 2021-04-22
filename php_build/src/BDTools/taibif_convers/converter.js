Proj4js.defs["EPSG:4326"] = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs";
var EPSG4326 = new Proj4js.Proj('EPSG:4326');

Proj4js.defs["EPSG:3821"] = "+proj=longlat  +towgs84=-752,-358,-179,-.0000011698,.0000018398,.0000009822,.00002329 +ellps=aust_SA +units=度 +no_defs";
var EPSG3821 = new Proj4js.Proj('EPSG:3821');

Proj4js.defs["EPSG:3824"] = "+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs";
var EPSG3824 = new Proj4js.Proj('EPSG:3824');

Proj4js.defs["EPSG:3825"] = "+proj=tmerc +lat_0=0 +lon_0=119 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs";
var EPSG3825 = new Proj4js.Proj('EPSG:3825');

Proj4js.defs["EPSG:3826"] = "+proj=tmerc  +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +units=???? +no_defs";
var EPSG3826 = new Proj4js.Proj('EPSG:3826');

Proj4js.defs["EPSG:3827"] = "+proj=tmerc +lat_0=0 +lon_0=119 +k=0.9999 +x_0=250000 +y_0=0 +ellps=aust_SA +units=m +towgs84=-752,-358,-179,-0.0000011698,0.0000018398,0.0000009822,0.00002329 +no_defs";
var EPSG3827 = new Proj4js.Proj('EPSG:3827');

Proj4js.defs["EPSG:3828"] = "+proj=tmerc  +towgs84=-752,-358,-179,-.0000011698,.0000018398,.0000009822,.00002329 +lat_0=0 +lon_0=121 +x_0=250000 +y_0=0 +k=0.9999 +ellps=aust_SA  +units=公尺";
var EPSG3828 = new Proj4js.Proj('EPSG:3828');


function TransCoord() {
  var sourceX = parseFloat(document.getElementById('sourceX').value);
  var sourceY = parseFloat(document.getElementById('sourceY').value);

  if (!sourceX || !sourceY) {
    document.getElementById('targetX').value = "";
    document.getElementById('targetY').value = "";
    return false;
  }

  switch (document.getElementById('sourceSystem').value) {
    case "1":
      var sourceProj = new Proj4js.Proj("EPSG:4326");
      break;
    case "2":
      var sourceProj = new Proj4js.Proj("EPSG:3821");
      break;
    case "3":
      var sourceProj = new Proj4js.Proj("EPSG:3824");
      break;
    case "4":
      var sourceProj = new Proj4js.Proj("EPSG:3825");
      break;
    case "5":
      var sourceProj = new Proj4js.Proj("EPSG:3826");
      break;
    case "6":
      var sourceProj = new Proj4js.Proj("EPSG:3827");
      break;
    case "7":
      var sourceProj = new Proj4js.Proj("EPSG:3828");
      break;
  }

  switch (document.getElementById('targetSystem').value) {
    case "1":
      var targetProj = new Proj4js.Proj("EPSG:4326");
      break;
    case "2":
      var targetProj = new Proj4js.Proj("EPSG:3821");
      break;
    case "3":
      var targetProj = new Proj4js.Proj("EPSG:3824");
      break;
    case "4":
      var targetProj = new Proj4js.Proj("EPSG:3825");
      break;
    case "5":
      var targetProj = new Proj4js.Proj("EPSG:3826");
      break;
    case "6":
      var targetProj = new Proj4js.Proj("EPSG:3827");
      break;
    case "7":
      var targetProj = new Proj4js.Proj("EPSG:3828");
      break;
  }

  var point = new Proj4js.Point(sourceX, sourceY);  //Create a point object
  Proj4js.transform(sourceProj, targetProj, point) //Do your conversion

  //alert(point.y + "," + point.x);
  //document.write('<p>x: ' + point.x + '<br>y: ' + point.y  + '</p>');
  document.getElementById('targetX').value = point.x;
  document.getElementById('targetY').value = point.y;

  var x=document.getElementById('targetX').value;
  var y=document.getElementById('targetY').value;

  return true;
  //document.myform.submit();
}


document.onreadystatechange = function () {
  if (document.readyState == "complete") {
    document.getElementById('launch').onclick = TransCoord;
  }
}
