<?php    
 include_once("proj4php.php");
 $proj4 = new Proj4php();
 /* 定義參數說明
 WGS84 經緯度：1
 67經緯度：2
 97經緯度：3
 二度分帶 TW2 97 澎湖：4
 二度分帶 TW2 97 台灣：5
 TW2 67 澎湖：6
 TW2 67 台灣：7
 */
 if ($_GET['source']=="1")  $projsource = new Proj4phpProj('EPSG:4326',$proj4);
 if ($_GET['source']=="2")  $projsource = new Proj4phpProj('EPSG:3821',$proj4);
 if ($_GET['source']=="3")  $projsource = new Proj4phpProj('EPSG:3824',$proj4);
 if ($_GET['source']=="4")  $projsource = new Proj4phpProj('EPSG:3825',$proj4);
 if ($_GET['source']=="5")  $projsource = new Proj4phpProj('EPSG:3826',$proj4);
 if ($_GET['source']=="6")  $projsource = new Proj4phpProj('EPSG:3827',$proj4);
 if ($_GET['source']=="7")  $projsource = new Proj4phpProj('EPSG:3828',$proj4);
 
 if ($_GET['destination']=="1")  $projdest = new Proj4phpProj('EPSG:4326',$proj4);
 if ($_GET['destination']=="2")  $projdest = new Proj4phpProj('EPSG:3821',$proj4);
 if ($_GET['destination']=="3")  $projdest = new Proj4phpProj('EPSG:3824',$proj4);
 if ($_GET['destination']=="4")  $projdest = new Proj4phpProj('EPSG:3825',$proj4);
 if ($_GET['destination']=="5")  $projdest = new Proj4phpProj('EPSG:3826',$proj4);
 if ($_GET['destination']=="6")  $projdest = new Proj4phpProj('EPSG:3827',$proj4);
 if ($_GET['destination']=="7")  $projdest = new Proj4phpProj('EPSG:3828',$proj4);

 $pointSrc = new proj4phpPoint($_GET['x'],$_GET['y']);
// echo "Source : ".$pointSrc->toShortString()."<br>";
 $pointDest = $proj4->transform($projsource,$projdest,$pointSrc);
// echo "Conversion : ".$pointDest->toShortString()."<br><br>";

function epsg ($i) {
switch($i) {
  case 1:
    return 'EPSG:4326';
  case 2:
    return 'EPSG:3821';
  default:
    $x = 3821 + $i;
    return 'EPSG:' . $x;
}


}


$ret['src'] = $pointSrc->toArr();
$ret['src']['datum'] = epsg($_GET['source']);
$ret['dest'] = $pointDest->toArr();
$ret['dest']['datum'] = epsg($_GET['destination']);

echo json_encode($ret);

?>
