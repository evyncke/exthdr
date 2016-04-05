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
        case 'alexa2015': $db_db = $db_db_2015 ; $summary_table = 'exthdr_summary' ; break ;
        case 'alexa2016': $db_db = $db_db_2015 ; $summary_table = 'exthdr_summary' ; ;
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
$asn = $_REQUEST['asn'] ;

$cache_id = "${data_set}_${test}_${result}_${asn}" ;
$cache_group = "as_detail" ;

if (!$cache->start($cache_group, $cache_id)) {
$mysqli = new mysqli($db_host, $db_user, $db_password, $db_db, $db_port) ;
$result = $mysqli->real_escape_string($_REQUEST['r']) ;
$asn = $mysqli->real_escape_string($_REQUEST['asn']) ;
# $gi = geoip_open('/usr/local/share/GeoIP/GeoIPASNumv6.dat') ;


?>
<html>
<head>
<title>Impact of <?=$asn?> on <?=$test_name?> Loss</title>
</head>
<body>
<h1>Impact of <?=$asn?> on <?=$test_name?> Loss</h1>
<table border="1">
<thead>
<tr><th>Destination Address</th><th>Dropping Router</th></tr>
</thead>
<tbody>
<?php

$sql = "select * from $summary_table
	where test_nb = $test_id and result = '$result' and (dropping_as like '$asn %' or dropping_as = '$asn')
	order by dest_addr limit 0,50" ;
$result_set = $mysqli->query($sql) or die("Cannot select ! " . $mysqli->error) ;
while ($row = $result_set->fetch_assoc()) {
        print("<tr><td><a href=\"addr_detail.php?ds=$data_set&t=$test&a=$row[dest_addr]\">$row[dest_addr]</a><br/><i>" .
		gethostbyaddr($row['dest_addr']) . "<br/>$row[dest_as]</i></td><td>$row[dropping_addr]<br/><i>" .
		gethostbyaddr($row['dropping_addr']) .  "<br/>$row[dropping_as]</i></td></tr>\n" ) ;
}
$result_set->free() ;
?>
</tbody>
</table>
<i>Limited to 50 destinations.</i>
<hr>
<em>Measurements done from <?=$location?>. Based on work done by Eric Vyncke and Mehdi Kouhen, 2015. Graphics by Google. Written in Python using the scapy module.</em>
</body>
</html>
<?php
        $cache->end() ;
}
?>
