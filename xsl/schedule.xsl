<?xml version="1.0" encoding="UTF8"?>

<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="xml" indent="yes" 
	    doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
	    doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
	 	encoding="UTF-8"
	/>
		
	
	<xsl:template match="/">
		<html>
			<head>
				<style type="text/css">
body {
	font-family:Helvetica, Verdana;
	font-size:10pt;
}

table.link {
	align:left;
	text-align:left;
}

table.part {
	text-align:left;
	padding-left:100px;
}

table.part thead tr th {
	border-bottom:1px solid #CCCCCC;
	padding-bottom:2px;
}

table.part tbody tr td {
	padding-top: 2px;
	padding-bottom: 1px;
	padding-left: 5px;
}

h4, h3 {
	padding: 0;
	margin:0;
}

.frompart {
	background-color: #F0F0F0;
}

.topart {
	border-bottom: 1px dashed #C0C0C0;
}


				</style>
			</head>
			<body>
				<ul id="title" style="display:inline">
					<li>From: <span class="query"><xsl:value-of select="schedules/schedules/request/from"/></span></li>
					<li>To: <span class="query"><xsl:value-of select="schedules/schedules/request/to"/></span></li>
					<li>Time: <span class="query"><xsl:value-of select="schedules/schedules/request/time"/></span></li>
				</ul>
				<xsl:apply-templates/>
			</body>
		</html>
	</xsl:template>
	
	<xsl:template match="request"/>
	
	<xsl:template match="schedule">
		<div style='width:1200px;background: black;color:white;padding:5px;margin-top:50px;'><h3>Schedule</h3></div>
		<xsl:apply-templates/>
	</xsl:template>
	
	<xsl:template match="link">
		<div style='width:1200px;background: #C0C0C0;margin-top:50px;border-top:2px solid black;border-bottom:1px solid black;padding:5px;'>
			<table class="link" cellpadding='0' cellspacing='0'>
				<thead>
					<tr><th width='100px'></th><th width='250px'>Station</th><th width='150px'>Time</th></tr>
				</thead>
				<tbody>
					<xsl:apply-templates select="from"/>
					<xsl:apply-templates select="to"/>
				</tbody>
			</table>
		</div>
		<xsl:apply-templates select="parts"/>
	</xsl:template>
	
	<xsl:template match="link/from">
		<tr><th align='left'>From</th><td><xsl:value-of select="name"/></td><td><xsl:value-of select="datetime" /></td></tr>
	</xsl:template>
	
	<xsl:template match="link/to">
		<tr><th align='left'>To</th><td><xsl:value-of select="name"/></td><td><xsl:value-of select="datetime" /></td></tr>
	</xsl:template>
	
	<xsl:template match="parts">
		<div style='width:1200px;border-bottom:1px solid black;padding:5px;'><h4>Parts</h4></div>
		<div style='width:1200px;padding:5px;'>
			<table class="part" cellpading='0' cellspacing='0'>
				<thead>
					<tr><th width='250px'>Station</th><th width='150px'>Time</th><th width='100px'>Track</th><th width='100px'>Vehicle</th><th width='150px'>Line</th><th width='200px'>Notes</th><th width='180px'>Duration</th></tr>
				</thead>
				<tbody>
					<xsl:apply-templates />
				</tbody>
			</table>
		</div>
	</xsl:template>
	
	<xsl:template match="part">
		<xsl:apply-templates select="from"/>
		<xsl:apply-templates select="to"/>
	</xsl:template>
	
	<xsl:template match="part/from">
		<tr><td class="frompart"><xsl:value-of select="name"/></td><td class="frompart"><xsl:value-of select="datetime"/></td><td class="frompart"><xsl:value-of select="track"/></td><td class="topart" rowspan='2'><xsl:value-of select="../vehicle"/></td><td class="topart" rowspan='2'><xsl:value-of select="../line"/></td><td class="topart" rowspan='2'><xsl:value-of select="../notes"/></td><td class="topart" rowspan='2'><xsl:value-of select="../duration"/></td></tr>
	</xsl:template>
	
	<xsl:template match="part/to">
		<tr><td class="topart"><xsl:value-of select="name"/></td><td class="topart"><xsl:value-of select="datetime"/></td><td class="topart"><xsl:value-of select="track"/></td></tr>
	</xsl:template>
	
</xsl:stylesheet>