var fen1,pos;
var gpstart, gpend;

window.onunload = function()
{
    fen1.onunload();
}

function xFenster(eleId, iniX, iniY, zoomLayer, zoomBtnId, resBtnId, qryBtnId, zoomOutBtnId, cameraBtnId)
{
  var me = this;
  var ele = xGetElementById(eleId);
  var rBtn = xGetElementById(resBtnId);
  var qBtn = xGetElementById(qryBtnId);
  var zBtn = xGetElementById(zoomBtnId);
  var z2Btn = xGetElementById(zoomOutBtnId);
  var ddiv = xGetElementById(zoomLayer);
  var cBtn = xGetElementById(cameraBtnId);
  
  this.onunload = function()
  {
    if (xIE4Up) {
      xDisableDrag(qBtn);
      xDisableDrag(rBtn);
      xDisableDrag(zBtn);
      xDisableDrag(z2Btn);
      xDisableDrag(cBtn);
      qBtn.onclick = ele.onmousedown = null;
      zBtn.onclick = ele.onmousedown = null;
      z2Btn.onclick = ele.onmousedown = null;
      cBtn.onclick = ele.onmousedown = null;
      me = ele = rBtn = qBtn = zBtn = z2Btn = cBtn = null;
    }
  }

  this.paint = function()
  {
    xMoveTo(rBtn, xWidth(ele) - xWidth(rBtn) - 2, xHeight(ele) - xHeight(rBtn) - 2);
    xMoveTo(qBtn, 0, xHeight(ele) - xHeight(qBtn) - 2);
  }

  function zoomOnDrag(e, mdx, mdy)
  {
    xMoveTo(ele, xLeft(ele) + mdx, xTop(ele) + mdy);
  }

  function resOnDrag(e, mdx, mdy)
  {
    xResizeTo(ele, xWidth(ele) + mdx, xHeight(ele) + mdy);
    me.paint();
  }

  function fenOnMousedown()
  {
    xZIndex(ele, xFenster.z++);
  }

  function ZoomOnClick()
  {
   gpstart = getLatLonFromPixel(xLeft(ele), xTop(ele));
   gpend = getLatLonFromPixel(xLeft(ele) + xWidth(ele), xTop(ele) + xHeight(ele));
   
        var bounds = new GLatLngBounds();
        var tlpoint = new GLatLng(gpstart.lat(), gpstart.lng());
        bounds.extend(tlpoint);
        var brpoint = new GLatLng(gpend.lat(), gpend.lng());
        bounds.extend(brpoint);
        
        map.setZoom(map.getBoundsZoomLevel(bounds));
		zoom(bounds.getSouthWest().lng(), bounds.getSouthWest().lat(), bounds.getNorthEast().lng(), bounds.getNorthEast().lat());
  }

  function ZoomOutOnClick()
  {
  	gpstart = getLatLonFromPixel(xLeft(ele), xTop(ele));
  	gpend = getLatLonFromPixel(xLeft(ele) + xWidth(ele), xTop(ele) + xHeight(ele));

        var bounds = new GLatLngBounds();
        var tlpoint = new GLatLng(gpstart.lat(), gpstart.lng());
        bounds.extend(tlpoint);
        var brpoint = new GLatLng(gpend.lat(), gpend.lng());
        bounds.extend(brpoint);
        
		var zoomLevel = map.getBoundsZoomLevel(bounds);
		map.setZoom(map.getBoundsZoomLevel(bounds)-2);
		zoom(bounds.getSouthWest().lng(), bounds.getSouthWest().lat(), bounds.getNorthEast().lng(), bounds.getNorthEast().lat());
  }

  function zoom(x1, y1, x2, y2)
  {
		var clat = (y2 + y1) /2;
		
        var correction = (360 + x2 - x1) /2;
          
			if (x1 > 0 && x2 < 0)
			{
            	if (Math.abs(x1) < Math.abs(x2))
				{
				var clng = x2 - correction;
				}
				else
				{
				var clng = x1 + correction;
				}
			}
			else
			{
			var clng = (x2 + x1) /2;
			}
		
		map.setCenter(new GLatLng(clat,clng));
  }

  function CameraOnClick ()
  {
  	gpstart = getLatLonFromPixel(xLeft(ele), xTop(ele));
  	gpend = getLatLonFromPixel(xLeft(ele) + xWidth(ele), xTop(ele) + xHeight(ele));
	
 if ( Math.abs(gpstart.lng()) - Math.abs(gpend.lng()) > 40 || gpstart.lat() - gpend.lat() > 20 ) {
		alert("Sorry, your selected region is too large. Please zoom in or narrow your search.");
	}
	else
	{
	var url;
	url = "NElat="+gpstart.lat()+"&SWlat="+gpend.lat()+"&NElng="+gpend.lng()+"&SWlng="+gpstart.lng();
   window.open('./search_by_map.php?'+url, 'mapsearch', 'toolbar=yes,location=yes,directories=yes,status=yes,menubar=yes,scrollbars=yes,resizable=yes');
	}
  }

  function QueryOnClick()
  {
  	gpstart = getLatLonFromPixel(xLeft(ele), xTop(ele));
  	gpend = getLatLonFromPixel(xLeft(ele) + xWidth(ele), xTop(ele) + xHeight(ele));
	
 if ( Math.abs(gpstart.lng()) - Math.abs(gpend.lng()) > 40 || gpstart.lat() - gpend.lat() > 20 ) {
		alert("Sorry, your selected region is too large. Please zoom in or narrow your search.");
	}
	else
	{
	var url;
	url = "NElat="+gpstart.lat()+"&SWlat="+gpend.lat()+"&NElng="+gpend.lng()+"&SWlng="+gpstart.lng();
   window.open('./search_by_map.php?'+url, 'mapsearch', 'toolbar=yes,location=yes,directories=yes,status=yes,menubar=yes,scrollbars=yes,resizable=yes');
	}
  }

  xFenster.z++;
  this.paint();
  xEnableDrag(rBtn, null, resOnDrag, null);
  xEnableDrag(ddiv, null, zoomOnDrag, null);
  qBtn.onclick = QueryOnClick;
  zBtn.onclick = ZoomOnClick;
  z2Btn.onclick = ZoomOutOnClick;
  cBtn.onclick = CameraOnClick;
  ele.onmousedown = fenOnMousedown;
  xShow(ele);
}

xFenster.z = 0;

function getLatLonFromPixel(x,y) {
var swpixel = map.getCurrentMapType().getProjection().fromLatLngToPixel(map.getBounds().getSouthWest(),map.getZoom());
var nepixel = map.getCurrentMapType().getProjection().fromLatLngToPixel(map.getBounds().getNorthEast(),map.getZoom());
 return map.getCurrentMapType().getProjection().fromPixelToLatLng(new GPoint(swpixel.x + Math.abs(x),nepixel.y + Math.abs(y)),map.getZoom());
}

function setDiv() {
	fen1 = new xFenster('zoomLayer', 0, 0, 'zoomLayer', 'ZoomBtn', 'ResBtn', 'QryBtn', 'ZoomOutBtn', 'CameraBtn');
	pos = new GControlPosition(G_ANCHOR_TOP_LEFT, new GSize(260,135));
	pos.apply(document.getElementById("zoomLayer"));
	map.getContainer().appendChild(document.getElementById("zoomLayer"));
	map.getContainer().style.overflow="hidden";
	//document.getElementById("zoomLayer").style.visibility = 'hidden';
	document.getElementById("zoomLayer").style.visibility = 'visible';
   map.addControl(new ToggleZoomControl());
}

function ToggleZoomControl() {}
ToggleZoomControl.prototype = new GControl();

ToggleZoomControl.prototype.initialize = function(map) {
	var container = document.createElement("div");
	var zoomToggle = document.createElement("img");
  	this.setImageStyle_(zoomToggle);
  	container.appendChild(zoomToggle);

  	GEvent.addDomListener(zoomToggle, "click", function() {
  		ToggleDisplay('zoomLayer');
  	});

	map.getContainer().appendChild(container);
	return container;
}

ToggleZoomControl.prototype.getDefaultPosition = function() {
  return new GControlPosition(G_ANCHOR_TOP_LEFT, new GSize(47, 47));
}

ToggleZoomControl.prototype.setImageStyle_ = function(img) {
	img.src = "./image/selector.png";
	img.style.cursor = "pointer";
	img.title = "Show/Hide Selector Box";
}

function ToggleDisplay(id){
	var elem = document.getElementById(id);
	if (elem){
		if (elem.style.display != 'block'){
			elem.style.display = 'block';
			elem.style.visibility = 'visible';
		}
		else{
			elem.style.display = 'none';
			elem.style.visibility = 'hidden';
		}
	}
}
