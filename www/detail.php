<?php
require_once('Cache/Lite/Output.php');
require_once 'conf.php' ;

$options = array(
        'cacheDir' => '/tmp/exthdr/',
        'writeControl' => 'true',
        'readControl' => 'true',
        'fileNameProtection' => false,
        'lifeTime' => 4 * 3600
);

$cache = new Cache_Lite_Output($options);

$data_set = ($_REQUEST['ds']) ? $_REQUEST['ds'] : 'alexa2015' ;
switch ($data_set) {
        case 'alexa2015': $db_db = $db_db_2015; $summary_table = 'exthdr_summary' ; break ;
        case 'alexa2016': $db_db = $db_db_2016; $summary_table = 'exthdr_summary' ; break ;
        case 'bgp2016': $db_db = $db_db_2016; $summary_table = 'bgp_exthdr_summary' ; break ;
        case 'bgp2015': $db_db = $db_db_2015; $summary_table = 'bgp_exthdr_summary' ; break ;
}
$test = ($_REQUEST['t']) ? $_REQUEST['t'] : 'do' ;
switch ($test) {
        case 'do': $test_id = 1 ; $test_name = "Destination Header" ; break ;
        case 'hbh': $test_id = 2 ; $test_name = "Hop-by-Hop Header" ; break ;
        case 'rh0': $test_id = 3 ; $test_name = "Routing Header type 0" ; break ;
        case 'rh4': $test_id = 4 ; $test_name = "Routing Header type 4" ; break ;
        case 'fh': $test_id = 5 ; $test_name = "Fragmentation Header" ; break ;
        case 'afh': $test_id = 6 ; $test_name = "Atomic Fragment" ; break ;
        case 'hbhdo': $test_id = 7 ; $test_name = "Hop-by-Hop and Destination Headers" ; break ;
#        case 'do128': $test_id = 8 ; $test_name = "128-bit Destination Header"; break ;
        case 'do256': $test_id = 9 ; $test_name = "256-bit Destination Header"; break ;
        case 'do512': $test_id = 10 ; $test_name = "512-bit Destination Header"; break ;
//        case 'hbh128': $test_id = 11 ; break ;
        case 'hbh256': $test_id = 12 ; $test_name = "256-bit Hop-by-Hop Header" ; break ;
        case 'hbh512': $test_id = 13 ; $test_name = "512-bit Hop-by-Hop Header" ; break ;

        default: $test_id = 1 ; $test = 'do' ; $test_name = "Destination Option Header" ;
}

$result = $_REQUEST['r'] ;
$cache_id = "${data_set}_${test}_${result}" ;
$cache_group = "detail" ;

if (!$cache->start($cache_group, $cache_id)) {
$mysqli = new mysqli($db_host, $db_user, $db_password, $db_db, $db_port) ;
$result = $mysqli->real_escape_string($_REQUEST['r']) ;


?>
<html>
<head>
<title>AS and <?=$test_name?> on the Internet</title>
</head>
<body>
<h1>AS and <?=$test_name?> on the Internet: <?=$result?></h1>
<table border="1">
<thead>
<tr><th>Test result</th><th>Number of destinations</th></tr>
</thead>
<tbody>
<?php

$sql = "select dropping_as,count(*) as cnt
	from $summary_table
	where test_nb = $test_id and result = '$result'
	group by dropping_as order by cnt desc limit 0,20" ;
$result_set = $mysqli->query($sql) or die("Cannot select ! " . $mysqli->error) ;
while ($row = $result_set->fetch_assoc()) {
        if ($row['dropping_as']) {
                $chunks = explode(' ', $row['dropping_as']) ;
                $asn = $chunks[0] ;
                print("<tr><td><a href=\"as_detail.php?ds=$data_set&t=$test&r=$_REQUEST[r]&asn=$asn\">$row[dropping_as]</a></td><td style=\"text-align: right;\">$row[cnt]</td></tr>\n" ) ;
        } else
                print("<tr><td>Cannot be determined</a></td><td style=\"text-align: right;\">$row[cnt]</td></tr>\n" ) ;
}
$result_set->free() ;
?>
</tbody>
</table>
<i>Limited to the top-20.</i>
<hr>
<em>Measurements done from <?=$location?>. Based on work done by Eric Vyncke and Mehdi Kouhen, 2015. Graphics by Google. Written in Python using the scapy module.
This service includes GeoLite data created by MaxMind, available from 
<a href="http://www.maxmind.com">http://www.maxmind.com</a>.</em>
</body>
</html>
<?php
        $cache->end() ;
}
?>
