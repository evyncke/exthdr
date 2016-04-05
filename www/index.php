<?php

require_once 'conf.php' ;

$data_set = (isset($_REQUEST['ds'])) ? $_REQUEST['ds'] : 'alexa2016' ;
switch ($data_set) {
        case 'alexa2015': $summary_table = 'exthdr_summary' ; $db_db = $db_db_2015 ; break ;
        case 'alexa2016': $summary_table = 'exthdr_summary' ; $db_db = $db_db_2016 ; break ;
        case 'bgp2016': $summary_table = 'bgp_exthdr_summary' ; $db_db = $db_db_2016 ; break ;
        case 'bgp2015': $summary_table = 'bgp_exthdr_summary' ; $db_db = $db_db_2015 ; break ;
}
$test = (isset($_REQUEST['t'])) ? $_REQUEST['t'] : 'do' ;
switch ($test) {
        case 'do': $test_id = 1 ; break ;
        case 'hbh': $test_id = 2 ; break ;
        case 'rh0': $test_id = 3 ; break ;
        case 'rh4': $test_id = 4 ; break ;
        case 'afh': $test_id = 5 ; break ;
        case 'fh': $test_id = 6 ; break ;
        case 'hbhdo': $test_id = 7 ; break ;
//        case 'do128': $test_id = 8 ; break ;
        case 'do256': $test_id = 9 ; break ;
        case 'do512': $test_id = 10 ; break ;
//        case 'hbh128': $test_id = 11 ; break ;
        case 'hbh256': $test_id = 12 ; break ;
        case 'hbh512': $test_id = 13 ; break ;
        default: $test_id = 1 ; $test = 'do' ; 
}
$mysqli = new mysqli($db_host, $db_user, $db_password, $db_db, $db_port) ;
?>
<html>
<head>
<title>IPv6 Extension Headers on the Internet</title>
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript">
google.load("visualization", "1", {packages:["corechart"]});

function drawChart() {
	var filteredDataArray = [] ;
	for (var i = 0; i < dataArray.length; i++) {
		if (!document.getElementById("unreachCheckBox").checked || (dataArray[i][0] != 'not reached'))
			filteredDataArray.push(dataArray[i]) ;
	}
	var data = google.visualization.arrayToDataTable(filteredDataArray) ;
        var options = {
          title: 'Ratio of outcome',
          is3D: true,
          sliceVisibilityThreshold: 0,
          slices: colorsArray,
        };

        var chart = new google.visualization.PieChart(document.getElementById('piechart'));
        chart.draw(data, options);
}

function changingDropdown() {
        var dsValue = document.getElementsByName('ds')[0].value;
        var tValue = document.getElementsByName('t')[0].value;
        window.location.href = "<?=$_SERVER['PHP_SELF']?>?ds=" + dsValue + '&t=' + tValue ;
}

function toggleUnreach() {
	drawChart() ;
}

</script>
</head>
<body onload="drawChart();">
<h1>IPv6 Extension Headers on the Internet</h1>
The data set is about: <select name="ds" onchange="changingDropdown();">
<option value="alexa2016" <?=($data_set == 'alexa2016')? 'selected' : ''?>>IPV6 web servers in Alexa top million sites Spring 2016</option>
<option value="bgp2016" <?=($data_set == 'bgp2016')? 'selected' : ''?>>all IPv6 prefixes in BGP tables Spring 2016</option>
</select>, the test was done by sending IPv6 packets with <select name="t" onchange="changingDropdown();">
<option value="do" <?=($test == 'do')? 'selected' : ''?>>Destination Header - 16 bytes</option>
<!-- option value="do128" <?=($test == 'do128')? 'selected' : ''?>>Destination Header - 128 bytes</option-->
<option value="do256" <?=($test == 'do256')? 'selected' : ''?>>Destination Header - 256 bytes</option>
<option value="do512" <?=($test == 'do512')? 'selected' : ''?>>Destination Header - 512 bytes</option>
<option value="hbh" <?=($test == 'hbh')? 'selected' : ''?>>Hop-by-Hop Header - 16 bytes</option>
<!-- option value="hbh128" <?=($test == 'hbh128')? 'selected' : ''?>>Hop-by-Hop Header - 128 bytes</option-->
<option value="hbh256" <?=($test == 'hbh256')? 'selected' : ''?>>Hop-by-Hop Header - 256 bytes</option>
<option value="hbh512" <?=($test == 'hbh512')? 'selected' : ''?>>Hop-by-Hop Header - 512 bytes</option>
<option value="hbhdo" <?=($test == 'hbhdo')? 'selected' : ''?>>Hop-by-Hop Header - 16 bytes - and Destination Header - 16 bytes</option>
<option value="rh0" <?=($test == 'rh0')? 'selected' : ''?>>Routing Header type 0</option>
<option value="rh4" <?=($test == 'rh4')? 'selected' : ''?>>Routing Header type 4</option>
<option value="afh" <?=($test == 'afh')? 'selected' : ''?>>Atomic Fragmentation Header (first and last fragment)</option>
<option value="fh" <?=($test == 'fh')? 'selected' : ''?>>Fragmentation Header (first fragment)</option>
</select>.
<br/>
<br/>
<table border="0">
<tr><td style="vertical-align: top;">

<table border="1">
<thead>
<tr><th>Test result</th><th>Number of<br/>destinations</th><th>%-age of<br/>destinations</th><th>%-age of<br/>reachable<br/>destinations</th></tr>
</thead>
<tbody>
<?php

$sql = "select count(*) as cnt
        from $summary_table
        where test_nb = $test_id" ;
$result = $mysqli->query($sql) or die("Cannot select count! " . $mysqli->error) ;
$row = $result->fetch_assoc() ;
$total_test = $row['cnt'] ;
$sql = "select count(*) as cnt
        from $summary_table
        where test_nb = $test_id
	and result != 'not reached'" ; // All except not reached
$result = $mysqli->query($sql) or die("Cannot select count reached! " . $mysqli->error) ;
$row = $result->fetch_assoc() ;
$total_test_reached = $row['cnt'] ;
$result->free() ;
$sql = "select s.result as result,count(*) as cnt, color, show_as
        from $summary_table s left join exthdr_results r on s.result = r.result
        where test_nb = $test_id
        group by result
        order by display_order asc" ;
$result = $mysqli->query($sql) or die("Cannot select ! " . $mysqli->error) ;
$js_table = "var dataArray = [ ['Result', 'Count']" ;
$js_color_table = "var colorsArray = {\n" ;
$slice_nr = 0 ;
while ($row = $result->fetch_assoc()) {
        $pct_age = round(100 * $row['cnt'] / $total_test, 1) ;
        $pct_age_reached = ($row['result'] == 'not reached') ? '-' : round(100 * $row['cnt'] / $total_test_reached, 1) ;
        if ($row['show_as'] != 0)
                print("<tr><td><a href=\"detail.php?ds=$data_set&t=$test&r=$row[result]\">$row[result]</a></td><td style=\"text-align: right;\">$row[cnt]</td><td style=\"text-align: right;\">$pct_age</td>
		<td style=\"text-align: right;\">$pct_age_reached</td></tr>\n" ) ;
        else
                print("<tr><td>$row[result]</td><td style=\"text-align: right;\">$row[cnt]</td><td style=\"text-align: right;\">$pct_age</td><td style=\"text-align: right;\">$pct_age_reached</td></tr>\n" ) ;
        $js_table .= ",\n['$row[result]', $row[cnt]]" ;
        $js_color_table .= "$slice_nr: { color: '$row[color]'},\n" ;
        $slice_nr ++ ;
}
$result->free() ;
$js_table .= "] ;\n" ;
$js_color_table .= "} ;\n" ;
?>
</tbody>
</table>
This test was executed with <?=$total_test?> packets sent with varying hop-limit.<br/>
<b>Not reached</b> means that a TCP SYN packet to 
port 80 even without any extension header did not get any reply (not even an ICMP or TCP RST); in short, those destinations
do not really exist.
</td><td>
<div id="piechart" style="width: 600px; height: 300px;">Loading...</div>
<input type="checkbox" onchange="drawChart();" id="unreachCheckBox" checked> Hide '<b>Not reached</b>' destinations.
</td></tr>
</table>
<script type="text/javascript">
<?=$js_table?>
<?=$js_color_table?>
</script>
<hr>
<em>Measurements done from <?=$location?>. Based on work done by Eric Vyncke and Mehdi Kouhen, 2015. Graphics by Google. Written in Python using the scapy module. 
This service includes GeoLite data created by MaxMind, available from <a href="http://www.maxmind.com">http://www.maxmind.com</a>.</em>
</body>
</html>
