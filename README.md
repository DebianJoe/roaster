roaster
=======

The Development branch for the Roaster web-browser for LinuxBBQ

License
=======
Original code Copyright (C) 2007, 2008, 2009 Jan Michael Alonzo <jmalonzo@gmai.com>

All additional files Copyright (c) 2013, Julius Hader <bacon@linuxbbq.org> and/or Joe Brock <DebianJoe@linuxbbq.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

Config Info
=======

Roaster is designed to read configuration files from one of 2 locations.  It will first source "/etc/roaster.conf", and then subsequently "~/.roaster.conf".  Should you wish to make changes to the Homepage, Default Page, or where files are stored using the "wget-it" option, this file is where you'll want to start hacking.  Before you even ask, I like config files because they're light on resource usage, so don't start requesting gtk-buttons and other such "user-friendly" options for changing these items.  There is an included .roaster.conf file in the tar, so you should be able to simply "cp /foo_bar_dir/.roaster.conf ~/.roaster.conf" and then start making it do what you want.

Faq
=======
*Q. What is this?
*A. Did you read the thing at the top of this document?  That's what it is.  It's the Development Branch for the LinuxBBQ's "Roaster" Web-Browser.  More accuratly, it's a Python-based browser that's lightweight and extremely hackable.


*Q. My config file doesn't work/some buttons don't work/foobar_function is broken. 
*A. Say it with me, "Development Branch"...we're working on it.  If you would like to submit an issue, then feel free.  We'll look into it.


*Q. I'd like to add (_______) feature. 
*A. Then by all means, add it.  If you want it in the main line program, put in a pull request.

*Q. How do I get it to run? 
*A. It is set to run by default in many LinuxBBQ distributions.  <http://www.linuxbbq.org>  If you'd like to run it as a script, then satisfy all of the imports, cd to the directory that the script is located, and run that bad mama-jama.

*Q. I see no buttons, how do I get around?  
*A. Right click.  When in doubt...right click.  It's designed to use gtk menus like BlackBox or OpenBox (or whatever_box).  All functionality is based on easy to navigate with right-click menus.

*Q. I don't use a mouse, mice are for noobs!  
*A. In the .roaster.conf file, there are user configurable shortcut keys.  If you don't use a mouse, then I'm sure you already are using a ton of hotkeys.  I'd hate to get in the way of that...so I give you full freedom to bind them however suits you.

*Q. How do I set the keybinds?  
*A. In the config file, there are detailed instructions.  If you screw up the syntax, though, they won't work.  So, don't screw it up.

*Q. How do I run it on Windows/Macintosh systems? 
*A. On the 13th of the month, at midnight, make 2 circles of salted leather strips.  Sacrifice a virgin, and draw a pentagram on the floor with her blood.  Then, repeat these lines, "Oh Overlord Satan, I beg of thee...make roaster run under Windows/Macintosh."  Report back with your findings.  Add "your soul" to the list of things to import.  I've not tried it, but it works in theory.

*Q. Will you please _______? 
*A. Probably not, but you can always ask.
