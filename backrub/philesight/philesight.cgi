#!/usr/bin/ruby
#
# CGI-wrapper for philesight

require "socket"

if Socket.gethostname == 'albana.ucsf.edu' then
	require 'cgi'
	require 'digest/md5'
	require 'philesight'
	
	##############################################################################
	# Config variables
	##############################################################################
	
			
	$img_size = 800
	$img_rings = 4
	$img_gradients = true
	$show_list = true
			
	# Uncomment the following lines to enable caching. Make sure the $path_cache
	# directory is writable by the httpd user
	
	# $path_cache = "/tmp/philesight"
	# $cache_maxage = 60
	
	##############################################################################
	# End of configuration
	##############################################################################
	
	
	class PhilesightCGI
	
		def initialize()
			
			@ps = Philesight.new($img_rings, $img_size, $img_gradients)
			
			cgi = CGI.new
      cmd = cgi.params['cmd'][0]
      userdir = cgi.params['userdir'][0]
      #$psdatabase = cgi.params['psdatabase'][0] or "ganon" # Not sure what's wrong here but this doesn't work
      $psdatabase = "ganon" # "webserver" or "ganon"
      
      if $psdatabase == "ganon" then
       $path_db = "/var/www/html/rosettaweb/backrub/philesight/userspace.db"
        if cgi.params['path'][0] then
          if cgi.params['path'][0] == "/" then
            cgi.params['path'][0] = "/kortemmelab"
          end
        end
        if userdir then
          path = cgi.params['path'][0] || "/kortemmelab/" + userdir || @ps.prop_get("root") || "/"
        else
          path = cgi.params['path'][0] || "/kortemmelab"
        end
      end
      
      if $psdatabase == "webserver" then
        $path_db = "/var/www/html/rosettaweb/backrub/philesight/webserver_diskusage.db"
        path = "/"
      end
      
      # Create philesight object and open database			
			@ps.db_open($path_db)
			
			# Get parameters from environment and CGI. 
			
			# ISMAP image maps do not return a proper CGI parameter, but only the
			# coordinates appended after a question mark. If this is found in the
			# QUERY_STRING, assume the 'find' command
	
			qs = ENV["QUERY_STRING"]
			if(qs && qs =~ /\?(\d+,\d+)/ ) then
				find_pos = $1
				cmd = 'find'
			end
	
			# Check if the cache directory is given and writable
	
			if $path_cache
				stat = File.lstat($path_cache)
				if stat.directory? and stat.writable? then
					@do_caching = true
				end
			end
	
			# Perform action depending on 'cmd' parameter
	
			case cmd
	
				when "img" 
					do_img(path)
	
				when "find"
					if(find_pos =~  /(\d+),(\d+)/) then
						do_find(path, $1.to_i, $2.to_i)
					end
	
				else 
					do_show(path, $psdatabase)
	
			end
		end
	
	
		#
		# Generate PNG image for given path
		#
	
		def do_img(path)
			puts "Content-type: image/png"
			puts "Cache-Control: no-cache, must-revalidate"
			puts "Expires: Sat, 26 Jul 1997 05:00:00 GMT"
			puts
			$stdout.flush
	
			if @do_caching then
				
				# First check if the image is in cache and fresh enough. If not,
				# generate new image
	
				now = Time.now()
				fname_img = $path_cache + "/cache-" + Digest::MD5.hexdigest(path)
	
				if ! File.readable?(fname_img) then
					@ps.draw(path, fname_img)
				else
					stat = File.lstat(fname_img)
					if now > stat.mtime + $cache_maxage then
						@ps.draw(path, fname_img)
					end
				end
	
				# Return the cached image
	
				fd = File.open(fname_img)
				while true do
					b = fd.read(4096)
					if b then
						print(b)
					else
						break
					end
				end
				fd.close
	
				# Clean all images in the cache directory older then $cache_maxage
				# seconds. Make sure only to cleanup files matching the name 'cache-'
				# followed by 32 chars (MD5 sum)
	
				Dir.foreach($path_cache) do |f|
					print(f)
					if f =~ /^cache-.{32}$/ then
						f_full = $path_cache + "/" + f
						stat = File.lstat(f_full)
						if now > stat.mtime + $cache_maxage then
							File.unlink(f_full)
						end
					end
				end
	
			else
	
				# Not caching, generate the PNG and send to stdout right away
				@ps.draw(path, "-")
	
			end
		end
	
	
		#
		# Find the path belonging to the ring and segment the user clicked
		# 
	
		def do_find(path, x, y)
			url = "?path=%s" % CGI.escape(@ps.find(path, x, y))
			puts "Content-type: text/html"
			puts "Cache-Control: no-cache, must-revalidate"
			puts "Expires: Sat, 26 Jul 1997 05:00:00 GMT"
			puts
			puts '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
			puts '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" >'
			puts '<head>'
			puts '	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
			puts '	<meta http-equiv="refresh" content="0; url=' + "#{url}" + '">'
			puts '</head>'
			puts '<body></body>'
			puts '</html>'
		end
	
	
		#
		# Generate HTML page with list and graph
		#
		
		def do_show(path, psdatabase)
			random = ""
			puts "Content-type: text/html"
			puts "Cache-Control: no-cache, must-revalidate"
			puts "Expires: Sat, 26 Jul 1997 05:00:00 GMT"
			puts
			puts '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
			puts '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" >'
			puts '<head>'
			puts '	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
			puts "	<title>Disk usage : " + CGI.escapeHTML(path) + "</title>"
			puts '	<style type="text/css">'
			#puts '	<!--'
			#puts '		body {color:black;text-align:center;background:#FAFAFA;}'
			#puts '		table {margin:auto;width:780px;}'
			#puts '		table,td {border:0;}'
			#puts '		td.size {text-align:right;}'
			#puts '		thead td {font-weight:bold;border-bottom:1px solid black;background:#EEE;}'
			#puts '		tbody td {background:#F0F0F0;}'
			#puts '		tbody tr.parentdir td {background:#E5D0D0;}'
			#puts '		tbody tr.evenrow td {background:#FFF;}'
			#puts '		'
			#puts '	-->'
			puts '	<!--'
			puts '		body {color:black;text-align:center;background:#FFF;}'
			puts '		table {margin:auto;width:780px;}'
			puts '		table,td {border:0;}'
			puts '		table.bordered {border:1px solid black;}'
			puts '		td.size {text-align:right; background:#F0F0F0;}'
			puts '		tbody td {background:#FFF;}'
			puts '		tbody td.folders {background:#F0F0F0;}'
			puts '		tbody tr.parentdir td {background:#E5D0D0;}'
			puts '		tbody tr.evenrow td {background:#FFF;}'
			puts '		'
			puts '	-->'
			puts '	</style>'
			puts '	<link rel="STYLESHEET" type="text/css" href="../style.css"/>'
			puts '</head>'
			puts '<body>'
			puts '	<table border="0" width="700" cellpadding="0" cellspacing="0">'
			puts '		<tr>'
			puts '			<td align="center" style="border-bottom:1px solid gray;">' 
			puts '				<a href="../"><img src="../images/header.png" usemap="#links" alt="kortemmelab"/></a>' 
			puts '			</td>'
			puts '		</tr>'
			puts '		<tr><td align="center" style="padding:10px;"></td></tr>'
			puts '		<tr><td align="right">[&nbsp;Other Services: <a class="nav" style="color:green;" href="/alascan">Alanine Scanning</a>&nbsp;] '
			puts '		<br/><small>[&nbsp;<span style="color:red">not logged in</span>&nbsp;]</small></td>' 
			puts '		</tr>'
			puts '		<tr>'
			puts '			<td align="center">'	
			puts '				[&nbsp;<a class="nav" href="/backrub/cgi-bin/rosettaweb.py?query=index" >Home</a>&nbsp;] &nbsp;&nbsp;&nbsp;'
			puts '				[&nbsp;<a class="nav" href="https://kortemmelab.ucsf.edu/backrub/wiki/" onclick="window.open(this.href, \'backrubwiki\').focus(); return false;">Documentation</a>&nbsp;] &nbsp;&nbsp;&nbsp;'
			puts '				[&nbsp;<a class="nav" href="/backrub/cgi-bin/rosettaweb.py?query=register">Register</a>&nbsp;]&nbsp;&nbsp;&nbsp;'
			puts '				[&nbsp;<a class="nav" href="/backrub/cgi-bin/rosettaweb.py?query=admin">Admin</a>&nbsp;]&nbsp;&nbsp;&nbsp;'
			puts '				[&nbsp;<a class="nav" href="/backrub/philesight/philesight.cgi">philesight</a>&nbsp;]'
			puts '			</td>'
			puts '		</tr>'
			puts '		<tr><td><p></p></td></tr>'
			puts '		<tr>'
			puts '			<td><table style="width:250px;text-align:left">'
			if psdatabase == "ganon" then
  			puts '				<tr>'
  			puts '				<td>Current members:</td>'
  			puts '				<td><button onclick="window.open(\'/backrub/philesight/philesight.cgi?psdatabase=ganon&userdir=home\',\'_self\')">home</button></td>'
  			puts '				<td><button onclick="window.open(\'/backrub/philesight/philesight.cgi?psdatabase=ganon&userdir=data\',\'_self\')">data</button></td>'
  			puts '				</tr>'
  			puts '				<tr>'
  			puts '				<td>Lab alumni:</td>'
  			puts '				<td><button onclick="window.open(\'/backrub/philesight/philesight.cgi?psdatabase=ganon&path=%2Fkortemmelab%2Falumni%2Fahome\',\'_self\')">home</button></td>'
  			puts '				<td><button onclick="window.open(\'/backrub/philesight/philesight.cgi?psdatabase=ganon&path=%2Fkortemmelab%2Falumni%2Fadata\',\'_self\')">data</button></td>'
  			puts '				</tr>'
  			puts '       <tr>'
        puts '        <td></td>'
        puts '        <td><button onclick="window.open(\'/backrub/philesight/philesight.cgi?psdatabase=ganon&userdir=archive\',\'_self\')">archive</button></td>'
        puts '        </tr>'
      end
      if psdatabase == "webserver" then
        puts '        <tr>'
        puts '        <td>Webserver</td>'
        puts '        <td><button onclick="window.open(\'/backrub/philesight/philesight.cgi?psdatabase=webserver\',\'_self\')">webserver</button></td>'
        puts '        </tr>'
      end
      puts '			</table></td>'
			puts '		</tr>'
			puts '		<tr>'
			puts '		<td>'
			puts '	<p><a href="' + "?path=" + CGI.escape(path) + "&amp;" + '">'
			puts '		<img style="border:0" width="' + $img_size.to_s + '" height="' + $img_size.to_s + '" src="?cmd=img&amp;path=' + CGI.escape(path) + '" ismap="ismap" alt="' + CGI.escapeHTML(path) + '" />'
			puts '	</a></p>'
			
			if $show_list then
				# Array of files
				content = @ps.listcontent(path)
				if(content && content[0]) then
					puts '	<table class="bordered" width="1000"  summary="File lists">'
					puts '		<thead>'
					puts '			<tr><td class="folders">Filename</td><td class="size">Size</td></tr>'
					puts '		</thead>'
					puts '		<tbody>'
					puts '			<tr class="parentdir"><td>' + content[0][:path].to_s + '</td><td class="size">' + content[0][:humansize].to_s + '</td></tr>'
	
					if(content[1].size > 0) then
						linenum = 0
	
						content[1] = content[1].sort_by { |f| - f[:size] }
						content[1].each do |f|
							if(linenum%2 == 0) then
								print '			<tr class="evenrow">'
							else
								print '			<tr>'
							end
	
							puts '<td class="folders"><a href="?path='+ CGI.escape(f[:path].to_s) +'">' + f[:path].to_s + '</a></td><td class="size">' + f[:humansize].to_s + '</td></tr>'
	
							linenum += 1
						end
					end
					puts '		</tbody>'
					puts '	</table>'
				end
			end
			puts '			</td>'
			puts '		</tr>'
			puts '	</table>'
			puts '<p style="text-align:center"><br/><a href="http://www.zevv.nl/play/code/philesight/">philesight</a> is an open source project written by Ico Doornekamp which turns the <a href="http://methylblue.com/filelight/">filelight</a> program of Max B. Howell and Martin Sandsmark into this webpage.</p>'
			puts '<p><a href="http://validator.w3.org/check?uri=referer"><img src="http://www.w3.org/Icons/valid-xhtml10" alt="Valid XHTML 1.0 Strict" height="31" width="88" /></a></p>'
			puts '</body>'
			puts '</html>'
		end
	
	end
	
	
	philesightcgi = PhilesightCGI.new
	
	#
	# vi: ts=4 sw=4
	#
else
	require 'cgi'
	puts "Content-type: text/html"
	puts "Cache-Control: no-cache, must-revalidate"
	puts "Expires: Sat, 26 Jul 1997 05:00:00 GMT"
	puts
	puts '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
	puts '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" >'
	puts '<head>'
	puts '<meta HTTP-EQUIV="REFRESH" content="0; url=https://kortemmelab.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=index">'
	puts '</head>'
	puts '</html>'
	philesightcgi = PhilesightCGI.new
end

