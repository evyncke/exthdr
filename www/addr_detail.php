<?php
require_once('Cache/Lite/Output.php');
require_once 'conf.php' ;

$options = array(
        'cacheDir' => '/tmp/exthdr/',
        'writeControl' => 'true',
        'readControl' => 'true',
        'fileNameProtection' => false,
        'lifeTime' => 4 * 1
);

$cache = new Cache_Lite_Output($options);

$data_set = ($_REQUEST['ds']) ? $_REQUEST['ds'] : 'alexa2015' ;
switch ($data_set) {
        case 'alexa2015': $db_db = $db_db_2015; $test_table = 'exthdr' ; break ;
        case 'alexa2016': $db_db = $db_db_2016; $test_table = 'exthdr' ; break ;
        case 'bgp2015': $db_db = $db_db_2015; $test_table = 'bgp_exthdr' ; break ;
        case 'bgp2016': $db_db = $db_db_2016; $test_table = 'bgp_exthdr' ; break ;
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

$address = $_REQUEST['a'] ;

$cache_id = "${data_set}_${test}_${address}" ;
$cache_group = "addr_detail" ;

if (!$cache->start($cache_group, $cache_id)) {
$mysqli = new mysqli($db_host, $db_user, $db_password, $db_db, $db_port) ;
$address = $mysqli->real_escape_string($_REQUEST['a']) ;


?>
<html>
<head>
<title>Path of packets with <?=$test_name?> to <?=$address?></title>
</head>
<body>
<h1>Path of packets with <?=$test_name?> to <?=$address?></h1>
<table border="1">
<thead>
<tr><th>Hop</th><th>Packet without EH</th><th>Packet with <?=$test_name?></th></tr>
</thead>
<tbody>
<?php

$sql = "select g.hop as hop, g.router as grouter, t.router as trouter, t.message as tmessage
        from $test_table g join $test_table t on g.hop = t.hop and g.address = t.address
        where g.test = 0 and t.test = $test_id and g.address = '$address'
        order by hop asc" ;
$result_set = $mysqli->query($sql) or die("Cannot select ! " . $mysqli->error) ;
while ($row = $result_set->fetch_assoc()) {
        if ($row['trouter'])
                print("<tr><td>$row[hop]</td><td>$row[grouter]</td><td>$row[trouter]</td></tr>\n" ) ;
        else
                print("<tr><td>$row[hop]</td><td>$row[grouter]</td><td>$row[tmessage]</td></tr>\n" ) ;
}
$result_set->free() ;
?>
</tbody>
</table>
<hr>
<em>Measurements done from <?=$location?>. Based on work done by Eric Vyncke and Mehdi Kouhen, 2015. Graphics by Google. Written in Python using the scapy module.</em>
</body>
</html>
<?php
        $cache->end() ;
}
?>
