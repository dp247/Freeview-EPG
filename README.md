# Freeview-EPG
[![Make EPG](https://github.com/dp247/Freeview-EPG/actions/workflows/actions.yml/badge.svg?branch=master)](https://github.com/dp247/Freeview-EPG/actions/workflows/actions.yml)

Freeview-EPG is a project designed to provide a reliable source of XMLTV data for UK free-to-air channels. The channel list was designed to match [this](https://github.com/ExperiencersInternational/tvsetup) project as closely as possible, and is a cutdown fork from the [iptv/epg](https://github.com/iptv-org/epg) project. 

It currently uses Sky's EPG Services or BT's YouView API to parse channel and programme data and then build the resulting dataset into an XMLTV file. The file provides a 48h EPG and is automatically updated every 24 hours.

![image](https://user-images.githubusercontent.com/9065463/232475526-1ea36b57-df01-4a95-afe2-dfbd3116052f.png)

## Disclaimer
I'm open to adding any *free-to-air* channels to this EPG, whether that's for an IPTV channel or a Freeview channel.

I'm also generating some [YouTube live streams](https://github.com/dp247/YouTubeToM3U8) that can be used in IPTV applications, although these don't contain EPG data.


## Usage
Grab the XMLTV file from this link and paste it into your favourite IPTV client:
```
https://raw.githubusercontent.com/dp247/Freeview-EPG/master/epg.xml
```

## To-do
- Provide support for EPG images/icons
- Build EPG data for radio stations

## Contributing
Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License
[GNU General Public License v3.0](https://github.com/dp247/Freeview-EPG/blob/master/LICENSE)
