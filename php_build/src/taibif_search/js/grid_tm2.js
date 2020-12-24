//Visit PROJ.4/Proj4js at http://www.proj4js.org/ for source code
Proj4js.defs["EPSG:3821"] = "+title=經緯度：TWD67 +proj=longlat  +towgs84=-752,-358,-179,-.0000011698,.0000018398,.0000009822,.00002329 +ellps=aust_SA +units=度 +no_defs";
Proj4js.defs["EPSG:3826"] = "+title=二度分帶：TWD97 TM2 台灣 +proj=tmerc  +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +units=公尺 +no_defs";
Proj4js.defs["EPSG:3828"] = "+title=二度分帶：TWD67 TM2 台灣 +proj=tmerc  +towgs84=-752,-358,-179,-.0000011698,.0000018398,.0000009822,.00002329 +lat_0=0 +lon_0=121 +x_0=250000 +y_0=0 +k=0.9999 +ellps=aust_SA  +units=公尺";

Proj4js.EPSG = new Proj4js.Proj('EPSG:3826');

var params = {};
if (location.search) {
  var parts = location.search.substring(1).split('&');

  for (var i = 0; i < parts.length; i++) {
    var nv = parts[i].split('=');

    if (!nv[0])
      continue;

    params[nv[0]] = nv[1] || true;
  }
}  // Now you can get the parameters you want like so: var abc = params.abc; 

function isEmpty(obj) {
  for (var i in obj) {
    return false;
  }

  return true;
}

var projHash = {};

var destIndex   = 0;
var sourceIndex = 0;
function initProj4js() {
  var crsSource = document.getElementById('crsSource');
  var crsDest   = document.getElementById('crsDest');
  var optIndex  = 0;

  for (var def in Proj4js.defs) {
    //create a Proj for each definition
    projHash[def] = new Proj4js.Proj(def);   

    var label = (projHash[def].title ? projHash[def].title : '');

    if (def == 'WGS84') {
      label = (projHash[def].title ? "經緯度：TWD97/WGS84" : '');
    }

    var opt = new Option(label, def);
    crsSource.options[optIndex]= opt;
    if (params.crsSource == def) {
      sourceIndex = optIndex;
    }

    var opt = new Option(label, def);
    crsDest.options[optIndex]= opt;
    if (params.crsDest == def) {
      destIndex = optIndex;
    }

    ++optIndex;
  }

  if (null != params.xySource) {
    document.getElementById('xySource').value = params.xySource;
  }

  updateCrs('Source');
  updateCrs('Dest');

  if (!isEmpty(params)) {
    simulateClick();
    outputUrl();
  }
}

function simulateClick() {
  if (0 != sourceIndex) {
    document.getElementById('crsSource').options[sourceIndex].selected = true;
    updateCrs('Source');
  }

  if (0 != destIndex) {
    document.getElementById('crsDest').options[destIndex].selected = true;
    updateCrs("Dest");
  }

  transform();
}

function updateCrs(id) {
  var crs = document.getElementById('crs' + id);

  if (crs.value) {
    document.getElementById('xyDest').value = '';

    var proj  = projHash[crs.value];
    var units = document.getElementById('units' + id);
    units.innerHTML = proj.units;

    if ('crs' + id == 'crsDest') {
      return proj.projName;
    }
  }
}

function transform() {
  document.getElementById('xyDest').value = '';

  var crsSource = document.getElementById('crsSource');
  var projSource = null;
  if (crsSource.value) {
    projSource = projHash[crsSource.value];
  }
  else {
    alert("請選擇欲轉換之座標參考系統!");
    return;
  }

  var crsDest = document.getElementById('crsDest');
  var projDest = null;
  if (crsDest.value) {
    projDest = projHash[crsDest.value];
  }
  else {
    alert("請選擇轉換後之座標參考系統!");
    return;
  }

  var pointInput = document.getElementById('xySource');
  if (pointInput.value) {
    var pointSource = new Proj4js.Point(pointInput.value);
    var pointDest = Proj4js.transform(projSource, projDest, pointSource);

    //check the Input(not Source) coordinates
    var xyInput = pointInput.value;
    //clear the space, comma & decimal letter
    xyInput = xyInput.replace(" ",'');
    xyInput = xyInput.replace(",",'');
    xyInput = xyInput.replace(".",'');
    xyInput = xyInput.replace(".",'');

    var inputRe = /^[0-9]+$/;
    if (xyInput.search(inputRe) == -1) {
      alert("請檢查並重新輸入待轉換座標!");
	   return;
    }

    //check the Dest coordinates
    if (isNaN(pointDest.x) || isNaN(pointDest.y)) {
      alert("請檢查並重新輸入待轉換座標!");
      return;
    }

    if (updateCrs('Dest') == "longlat") {
      // convert destPoint to 6-digi/longlat or 3-digi/tm2 decimal
      pointDest.x = (pointDest.x).toFixed(6);
      pointDest.y = (pointDest.y).toFixed(6);
    }
    else {
      pointDest.x = (pointDest.x).toFixed(3);
      pointDest.y = (pointDest.y).toFixed(3);
    }

    document.getElementById('xyDest').value = pointDest.toShortString();

    outputUrl();

    if ((null != params.autoconvert) && (1 == params.autoconvert)) {
      document.write(pointDest.toShortString());
    }
  }
  else {
    alert("請輸入欲轉換之原始座標!");
    return;
  }
}

function outputUrl() {
  var url      = window.location.href;
  var urlparts = url.split("?");

  document.getElementById('outputUrl').innerHTML =
    "<table>" +
    "  <tr>" +
    "    <td style='text-align: right;'>" +
    "      url:" +
    "    </td>" +
    "    <td>" +
    "      <input type='text' value='" + urlparts[0] +
    "?crsSource=" + document.getElementById('crsSource').value +
    "&crsDest=" + document.getElementById('crsDest').value +
    "&xySource=" + document.getElementById('xySource').value.replace(" ", "") +
    "' / size='130'>" +
    "    </td>" +
    "  </tr>" +
    "  <tr>" +
    "    <td style='text-align: right;'>" +
    "      auto convert url:" +
    "    </td>" +
    "    <td>" +
    "      <input type='text' value='" + urlparts[0] +
    "?crsSource=" + document.getElementById('crsSource').value +
    "&crsDest=" + document.getElementById('crsDest').value +
    "&xySource=" + document.getElementById('xySource').value.replace(" ", "") +
    "&autoconvert=1' / size='130'>" +
    "    </td>" +
    "  </tr>" +
    "</table>";
}

//style display for firefox & ie
function displayOn() {
  // Mozilla, Safari,...
  if (window.XMLHttpRequest) {
    return "table-row";
  }
  // ie
  else if (window.ActiveXObject) {
    return "block";
  }
} 
