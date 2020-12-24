<?php


if (isset($argv[1])) {
	$console =  true;
}
else {
	$console = false;
}


$src = (isset($_REQUEST['sourceSystem']))?$_REQUEST['sourceSystem']:1;
$tgt = (isset($_REQUEST['targetSystem']))?$_REQUEST['targetSystem']:1;


$srcSelected = array ("", "", "", "", "", "", "", "", "");
$srcSelected[$src] = 'selected';
$tgtSelected = array ("", "", "", "", "", "", "", "", "");
$tgtSelected[$tgt] = 'selected';


if ($console) {
	$sourceXY = (isset($_REQUEST['sourceXY']))?$_REQUEST['sourceXY']:"121 23
		121	23
		121,  23
		121,23";
}
else {
	$sourceXY = (isset($_REQUEST['sourceXY']))?$_REQUEST['sourceXY']:"";
}

$ep = "http://nginx/BDTools/proj4/convert.php";

$sourceXY = trim($sourceXY, " \r\n");
$resultXY = $sourceXY;
if (!empty($sourceXY)) {
	$xys = explode("\n", $sourceXY);
	$sourceXYs = array();
	$resXYs = array();

	foreach ($xys as $idx => $xy_item) {
		$sourceXYs[] = $xy_item;

		$xy_item = trim($xy_item, " \t,.;\r\n");
		$xy_frags = preg_split( '/(\s|,)/', $xy_item);
		$x = $xy_frags[0];
		$y = end($xy_frags);

		$data = array (
			'source' => $src,
			'destination' => $tgt,
			'x' => $x,
			'y' => $y,
		);
		$qparams = http_build_query($data);
		$url = $ep . "?" . $qparams;
		//$url = "http://nginx/info.php";
        //$runfile = "http://localhost:8000/BDTools/proj4/convert.php" . "?" . $qparams;
        $runfile ="http://linux.vbird.org/new_linux.php";
        function curl_get_contents($runfile)
        {
            $ch = curl_init();

            curl_setopt($ch, CURLOPT_HEADER, 0);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            curl_setopt($ch, CURLOPT_URL, $url);

            $data = curl_exec($ch);
            curl_close($ch);

            return $data_n;
        }
        //var_dump($data);

		$res = file_get_contents($url);
		// do whatever needed to be done to $res
		$res_res = explode("<br>", end(explode("Conversion : ", $res)));

		//var_dump($res_res);

		$res_res_frags = explode(" ", $res_res[0]);
		if ($x !== "") {
			$resX = trim($res_res_frags[0]);
		}
		else {
			$resX = 'NaN';
		}
		if ($y !== "") {
			$resY = trim(end($res_res_frags));
		}
		else {
			$resY = 'NaN';
		}
		if (($x == "")||($y == "")) {
			$resXYs[] = $resX.",".$resY;
		}
		else {
			$resXYs[] = round($resX,6).",".round($resY,6);
		}

	}
	$sourceXY = implode("\n", $sourceXYs);
	$resultXY = implode("\n", $resXYs);
}
?>
<html lang="en">
  <head>
        <meta charset="utf-8"><title>地理分布線上座標轉換 - 生物多樣性資料校對轉換工具</title>
    <meta name="description" content="生物多樣性資料校對轉換工具 Biodiversity Data Check Tools">
    <meta name="author" content="TaiBIF">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="bootstrap/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="stylesheets/screen.css" media="screen">
    <link rel="stylesheet" href="stylesheets/print.css" media="print">
        <script src="/taibif_search/js/proj4js.js"></script>
<script src="/taibif_search/js/proj4js-combined.js"></script>
<script src="/BDTools/taibif_convers/converter.js"></script>
    <!--[if lt IE 9]>           
    <script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <link href='http://fonts.googleapis.com/css?family=Droid+Sans:400,700|Gilda+Display|Playfair+Display' rel='stylesheet' type='text/css'>
    <script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-988217-3']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>
      </head>
	  <body>
    <header>
              <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
  <div class="navbar-header">
    <!--<button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">-->
      <!--<span class="icon-bar"></span>-->
      <!--<span class="icon-bar"></span>-->
      <!--<span class="icon-bar"></span>-->
    <!--</button>-->
    <a href="http://taibif.org.tw/BDTools/" class="site-title navbar-brand"><span class="glyphicon glyphicon-home"></span>生物多樣性資料校對轉換工具</a>
  </div>
  <!--<div class="collapse navbar-collapse">-->
  <!--</div>-->
</nav>
          </header>
    <section class="content container">
      <div class="page-header"><h1>地理分布線上座標轉換&nbsp;<small>批次轉換</small></h1></div>
      <div class="row">



<form name='batchCoordCnvrtForm' method='post'>
      <h2>原始坐標</h2><?php echo $runfile;?><?php echo '<pre>'; print_r($res); echo '</pre>';?>
      <div class="form-group">
        <label for="sourceSystem" class="col-sm-2 control-label">投影座標系統</label>
        <div class="col-sm-10">
          <select class="form-control" id="sourceSystem" name="sourceSystem">
            <option value="1"<?php echo $srcSelected[1];?>>WGS 84 經緯度</option>
            <option value="2"<?php echo $srcSelected[2];?>>TWD 67 經緯度</option>
            <option value="3"<?php echo $srcSelected[3];?>>TWD 97 經緯度</option>
            <option value="4"<?php echo $srcSelected[4];?>>TWD97/ 澎湖地區</option>
            <option value="5"<?php echo $srcSelected[5];?>>TWD97/ 臺灣地區</option>
            <option value="6"<?php echo $srcSelected[6];?>>TWD67/ 澎湖地區</option>
            <option value="7"<?php echo $srcSelected[7];?>>TWD67/ 臺灣地區</option>
          </select>
        </div>
      </div>
      <label for="sourceXY" class="col-sm-2 control-label">座標資料</label>        
        <div class="col-sm-10">
          <textarea id="sourceXY" name="sourceXY" class="form-control" rows="10"><?php echo $sourceXY;?></textarea>
        </div>
      

      <h2>轉換坐標</h2>
      <div class="form-group">
        <label for="targetSystem" class="col-sm-2 control-label">投影座標系統</label>
        <div class="col-sm-10">
          <select class="form-control" id="targetSystem" name="targetSystem">
            <option value="1"<?php echo $tgtSelected[1];?>>WGS 84 經緯度</option>
            <option value="2"<?php echo $tgtSelected[2];?>>TWD 67 經緯度</option>
            <option value="3"<?php echo $tgtSelected[3];?>>TWD 97 經緯度</option>
            <option value="4"<?php echo $tgtSelected[4];?>>TWD97/ 澎湖地區</option>
            <option value="5"<?php echo $tgtSelected[5];?>>TWD97/ 臺灣地區</option>
            <option value="6"<?php echo $tgtSelected[6];?>>TWD67/ 澎湖地區</option>
            <option value="7"<?php echo $tgtSelected[7];?>>TWD67/ 臺灣地區</option>
          </select>
        </div>
      </div>
     
        <label for="resultXY" class="col-sm-2 control-label">轉換結果</label>
        <div class="col-sm-10">
          <textarea class="form-control" rows="10" id="resultXY" name="resultXY"><?php echo $resultXY;?></textarea>
        </div>
      

      <input type='submit' value='送出'/>

</form>
<div class="col-md-6">
<h2>批次轉換說明</h2>
<p>將經度與緯度的坐標（經度在前，緯度在後）利用逗號或空格隔開，貼於原始坐標的輸入方塊中，並選擇原始輸入的坐標系統與欲輸出的坐標系統。再按下送出的按鈕，即可完成多筆坐標的轉換。</p>
</div>
<div class="col-md-6">
    <h2>網路服務使用說明</h2>
    <p>參數說明：</p>
    <ul>
      <li><strong>source:</strong> 來源坐標系統
        <ul>
          <li><strong>1:</strong> WGS 84 經緯度</li>
          <li><strong>2:</strong> TWD 67 經緯度</li>
          <li><strong>3:</strong> TWD 97 經緯度</li>
          <li><strong>4:</strong> TWD97/ 澎湖地區</li>
          <li><strong>5:</strong> TWD97/ 臺灣地區</li>
          <li><strong>6:</strong> TWD67/ 澎湖地區</li>
          <li><strong>7:</strong> TWD67/ 臺灣地區</li>
        </ul>
      </li>
      <li><strong>destination:</strong> 欲轉換的座標系統
        <ul>
          <li><strong>1:</strong> WGS 84 經緯度</li>
          <li><strong>2:</strong> TWD 67 經緯度</li>
          <li><strong>3:</strong> TWD 97 經緯度</li>
          <li><strong>4:</strong> TWD97/ 澎湖地區</li>
          <li><strong>5:</strong> TWD97/ 臺灣地區</li>
          <li><strong>6:</strong> TWD67/ 澎湖地區</li>
          <li><strong>7:</strong> TWD67/ 臺灣地區</li>
        </ul>
      </li>
      <li><strong>x:</strong> X 坐標</li>
      <li><strong>y:</strong> Y 坐標</li>
    </ul>
    <p>範例：</p>
    <pre>http://taibif.org.tw/BDTools/proj4/convert.php?<strong>source</strong>=5&amp;<strong>destination</strong>=1&amp;<strong>x</strong>=123456&amp;<strong>y</strong>=2234567</pre>
  </div>


 </section>
    <footer>
              <div class="container">
  <div class="row">
    <div class="col-md-3">
      <a href="http://taibif.tw/"><img src="images/taibif-logo-mono.png" alt="TaiBIF"></a>
    </div>
    <div class="col-md-9">
      <h2>技術提供：</h2>
      <p><a href="http://taibif.tw/"><span class="glyphicon glyphicon-link"></span>TaiBIF 臺灣生物多樣性資訊機構 Taiwan Biodiversity Information Facility</a></p>
    </div>
  </div>
</div>
          </footer>
    <script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
    <script src="bootstrap/dist/js/bootstrap.min.js"></script>
  </body>
</html>



