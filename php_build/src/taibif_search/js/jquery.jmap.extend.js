function in_array(arr, value)
{
   for (var index in arr)
   {
      if (arr[index] == value)
         return true;
   }

   return false;
}

Mapifies.AddGControl = function(element, options, callback) {
	function defaults() {
		return {
			'gcontrolTitle':'Title',
			'gcontrolTextNode':'TextNode',
			'gcontrolClass':'',
			'gcontrolPosition':G_ANCHOR_TOP_RIGHT,
			'gcontrolWidth':7,
			'gcontrolHeigh':31
		};
	};
	var thisMap = Mapifies.MapObjects.Get(element);
	options = jQuery.extend(defaults(), options);

   function MDControl() { }
   MDControl.prototype = new GControl();
   MDControl.prototype.initialize = function(thisMap)
   {
      var container = document.createElement('div');

      var button = document.createElement('div');
      button.title = options.gcontrolTitle;
      button.className = options.gcontrolClass;
      container.appendChild(button);

      button.appendChild(document.createTextNode(options.gcontrolTextNode));
      GEvent.addDomListener(button, 'click', function() {
         var color = document.getElementById('color');
         while (color != null)
         {
            color.parentNode.removeChild(color);
            color = document.getElementById('color');
         }
      });

      thisMap.getContainer().appendChild(container);
      return container;
   }

   MDControl.prototype.getDefaultPosition = function()
   {
      return new GControlPosition(options.gcontrolPosition, new GSize(options.gcontrolWidth, options.gcontrolHeigh));
   }

   thisMap.addControl(new MDControl());

	if (typeof callback == 'function')
      return callback(container, options);

   return;
};

Mapifies.AddDisplay = function(element, options, callback) {
	function defaults() {
		return {
         'displaySWLat':21,
         'displaySWLng':119,
         'displayNELat':27,
         'displayNELng':123,
         'displayWeight':1,
         'displayFadeColor':'#FFF',
         'displayFade':'#FFFFFF',
         'displayData':[],
         'displayShowData':[],
         'displayOpacityData':[],
         'displayFadeData':[],
         'displayConnectSet':[],
         'displayBoundSet':[],
         'displayColorSet':[],
         'displayTextColorSet':[]
		};
	};

	var thisMap = Mapifies.MapObjects.Get(element);
	options = jQuery.extend({}, defaults(), options);

   function Display(bounds, opt_bgColor, opt_visibility)
   {
      this.bounds_     = bounds;
      this.bgColor_    = opt_bgColor || '#FFF';
      this.visibility_ = opt_visibility || 'hidden';

      this.removeAllChildren = function()
      {
         var color = document.getElementById('color');
         while (color != null)
         {
            color.parentNode.removeChild(color);
            color = document.getElementById('color');
         }
      }

      this.createChildren = function()
      {
         var startLat = this.bounds_.getSouthWest().lat();
         var stopLat  = this.bounds_.getNorthEast().lat();
         var startLng = this.bounds_.getSouthWest().lng();
         var stopLng  = this.bounds_.getNorthEast().lng();

         //現在 map 的可視範圍
         var nowZoom = this.map_.getZoom();
         var nowBounds = this.map_.getBounds();
         var nowSW = nowBounds.getSouthWest();
         var nowNE = nowBounds.getNorthEast();

         var data         = options.displayData;
         var showData     = options.displayShowData;
         var opacityData  = options.displayOpacityData;
         var fadeData     = options.displayFadeData;
         var connectSet   = options.displayConnectSet;
         var boundSet     = options.displayBoundSet;
         var colorSet     = options.displayColorSet;
         var textColorSet = options.displayTextColorSet;

         var weight = options.displayWeight;
         var fadeColor = options.displayFadeColor;
         var fade = options.displayFade;

         for (var kiloSpan in data)
         {
            kiloSpan = parseInt(kiloSpan);

            //處理能顯現的色塊
            //if (typeof(showData[kiloSpan] != 'undefined') && showData[kiloSpan].in_array(nowZoom))
            if (typeof(showData[kiloSpan] != 'undefined') && in_array(showData[kiloSpan], nowZoom))
            {
               var span   = parseFloat(kiloSpan / 100);
               var startM = 0;
               var stopM  = (stopLat - startLat) / span;
               var startN = 0;
               var stopN  = (stopLng - startLng) / span;

               //如果 root 區塊的左側超出 map 可視範圍
               if (nowSW.lng() > startLng)
               {
                  startN = Math.floor((nowSW.lng() - startLng) / span);
               }

               //如果 root 區塊的右側超出 map 可視範圍
               if (stopLng > nowNE.lng())
               {
                  stopN = Math.floor((nowNE.lng() - startLng) / span);
               }

               //如果 root 區塊的下方超出 map 可視範圍
               if (nowSW.lat() > startLat)
               {
                  startM = Math.floor((nowSW.lat() - startLat) / span);
               }

               //如果 root 區塊的上方超出 map 可視範圍
               if (stopLng > nowNE.lat())
               {
                  stopM = Math.floor((nowNE.lat() - startLat) / span);
               }

               for (var m in data[kiloSpan])
               {
                  if ((m >= startM) && (m <= stopM))
                  {
                     m = parseInt(m);
                     for (var n in data[kiloSpan][m])
                     {
                        if ((n >= startN) && (n <= stopN))
                        {
                           n = parseInt(n);

                           var cnt = data[kiloSpan][m][n];

                           var index = 0;
                           for (; (cnt > boundSet[index]) && (index < boundSet.length); index++)
                           {
                              ;
                           }
                           if (index >= boundSet.length)
                              index = boundSet.length - 1;

                           var bgColor   = colorSet[index];
                           var textColor = textColorSet[index];
                           var boldColor = textColorSet[index];

                           if ((typeof(fadeData[kiloSpan]) != 'undefined') && in_array(fadeData[kiloSpan], nowZoom))
                           {
                              bgColor   = fadeColor;
                              textColor = fade;
                           }

                           var colorSW = new GLatLng(startLat + m * span, startLng + n * span);
                           var colorNE = new GLatLng(startLat + (m + 1) * span, startLng + (n + 1) * span);
                           var c1 = this.map_.fromLatLngToDivPixel(colorSW);
                           var c2 = this.map_.fromLatLngToDivPixel(colorNE);

                           var lngSpan = (colorNE.lng() - colorSW.lng()) / span;
                           var latSpan = (colorNE.lat() - colorSW.lat()) / span;
                           var xSpan = (c2.x - c1.x) / lngSpan;
                           var ySpan = (c2.y - c1.y) / latSpan;

                           //產生 div 色塊
                           var color = document.createElement('div');
                           color.id = 'color';
                           color.style.width = Math.abs(c2.x - c1.x) + 'px';
                           color.style.height = Math.abs(c2.y - c1.y) + 'px';
                           color.style.left = (Math.min(c2.x, c1.x) - weight) + 'px';
                           color.style.top = (Math.min(c2.y, c1.y) - weight) + 'px';
                           color.style.position = 'absolute';
                           color.style.background = bgColor;
                           color.style.border = weight + "px solid " + boldColor;
                           color.innerHTML = '<font color=\'' + textColor + '\'>(m,n) of SW | ' + m + ', ' + n + ' | kiloSpan | ' + kiloSpan + ' | </font>';
                           color.style.opacity = opacityData[kiloSpan];
                           color.style.filter = 'alpha(opacity=' + opacityData[kiloSpan] * 100 + ')';
                           color.style.overflow = 'hidden';

                           if ((typeof(connectSet) != "undefined") && in_array(connectSet, kiloSpan))
                           {
                              color.style.cursor = 'pointer';
                              color.onclick = function(){connectUrl(this)};
                           }

                           this.map_.getPane(G_MAP_MAP_PANE).appendChild(color);
                        }
                     }
                  }
               }
            }
         }
      }
   }

   Display.prototype = new GOverlay();

   Display.prototype.initialize = function(map)
   {
      var root = document.createElement('div');
      root.id = 'root';
      root.style.opacity = this.opacity_;
      root.style.position = 'absolute';
      root.style.visibility = this.visibility_;

      map.getPane(G_MAP_MAP_PANE).appendChild(root);

      this.map_ = map;
      this.div_ = root;
   }

   Display.prototype.redraw = function(force)
   {
      if (!force)
         return;

      var zoom = this.map_.getZoom();

      if (zoom < minZoom)
      {
         zoom = minZoom;
         this.map_.setZoom(zoom);
      }

      if (zoom > maxZoom)
      {
         zoom = maxZoom;
         this.map_.setZoom(zoom);
      }

      var c1 = this.map_.fromLatLngToDivPixel(this.bounds_.getSouthWest());
      var c2 = this.map_.fromLatLngToDivPixel(this.bounds_.getNorthEast());

      this.div_.style.width = Math.abs(c2.x - c1.x) + 'px';
      this.div_.style.height = Math.abs(c2.y - c1.y) + 'px';
      this.div_.style.left = Math.min(c2.x, c1.x) + 'px';
      this.div_.style.top = Math.min(c2.y, c1.y) + 'px';
      this.div_.style.background = this.bgColor_;

      //將舊的節點刪除
      this.removeAllChildren();

      //新增節點
      this.createChildren();

      //產生註釋
//      writeNote(this.map_);
   }

   function connectUrl(color)
   {
      var innerHTML = color.innerHTML;
      var slice = " | ";
      var tokens = innerHTML.split(slice);
      // [1]  是座標的 m,n
      // [3] 是 kiloSpan 資料
      var swString = tokens[1];
      var kiloSpan = tokens[3];

      var tokens = swString.split(", ");
      var m = tokens[0].substring(0, tokens[0].length);
      var n = tokens[1].substring(0, tokens[1].length);

      location.href="searchResult.php?op=marker&asc=&m=" + m + "&n=" + n + "&kiloSpan=" + kiloSpan;
   }

   function writeNote(map)
   {
      var note = document.getElementById("note");
      var zoom = map.getZoom();
      var innerHTML = "<font color='#FFFFFF'>";
      var cnt = 0;
      var appear = false;

      for (var kiloSpan in data)
      {
         if (typeof(showData[kiloSpan] != 'undefined') && in_array(showData[kiloSpan], zoom))
            cnt++;
      }

      for (var kiloSpan in data)
      {
         kiloSpan = parseInt(kiloSpan);

         //處理能顯現的色塊
         if (typeof(showData[kiloSpan] != 'undefined') && in_array(showData[kiloSpan], zoom))
         {
            //顯示多於1個方格的註釋
            if ((cnt > 1) && (appear == false))
            {
               innerHTML += "大方格: " + kiloSpan + " * " + kiloSpan + " 公里";

               appear = true;
            }
            else if ((cnt > 1) && (appear == true))
            {
               innerHTML += "小方格: " + kiloSpan + " * " + kiloSpan + " 公里";
            }
            else
            {
               innerHTML += "方格: " + kiloSpan + " * " + kiloSpan + " 公里";
            }

            if (in_array(connectSet, kiloSpan))
            {
               innerHTML += "(可點選連結)";
            }

            innerHTML += "<br>";
         }
      }

      innerHTML += "</font>";

      note.innerHTML = innerHTML;
   }

   //資料覆蓋範圍
   var dataSW = new GLatLng(options.displaySWLat, options.displaySWLng);
   var dataNE = new GLatLng(options.displayNELat, options.displayNELng);

   //繪圖用的 div 節點不必顯示出來
   var bounds = new GLatLngBounds(dataSW, dataNE);
   var display = new Display(bounds, '#FFF', 'hidden');

   thisMap.addOverlay(display);

   GEvent.addListener(thisMap, 'dragend', function()
   {
      display.redraw(true);
   });

   return;

};