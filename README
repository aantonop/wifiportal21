This is an experimental Wifi captive portal that accepts bitcoin payments for Wifi minutes.

It uses the 21 Bitcoin Computer (http://21.co/) as the authentication server for any OpenWRT router running the Wifidog captive portal daemon.

INSTALL
=======


Install the wifiportal21 authentication server
----------------------------------------------

- Download the wifiportal21 zip or tar.gz and open it in a directory on your 21 computer.
- Change directory into the wifiportal21 directory
- Edit the config.py file and replace with your xpub and billing rate
- Install wifiportal21 package:

$ sudo python3 setup.py install

- Run the authentication server:

$ wifiportal21


Install OpenWRT and Wifidog on a wireless router
------------------------------------------------

- Install OpenWRT (http://wiki.openwrt.org/doc/howto/generic.flashing)
- Configure your wireless router and make sure it works properly. The WAN interface should be able to access the 21 computer IP address
- Install Wifidog captive portal gateway (http://wiki.openwrt.org/doc/howto/wireless.hotspot.wifidog)
- Configure Wifidog. A sample configuration is in wifidog.conf in the wifiportal21 package root directory. Most settings remain at defaults, except:
  - Set Authserver to point to your 21 computer:

      AuthServer {
            Hostname 192.168.1.21
            HTTPPort 21142
      }

  - Set CheckInterval to 60 seconds (so that elapsed minutes are counted correctly)
- Run:

# wifidog -f -d 6
