
![logo](https://user-images.githubusercontent.com/9065463/232618260-d9017259-1786-4d85-807f-63752143d403.png)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/dp247/Freeview-EPG/actions.yml?color=%232ca9bc&label=EPG%20Generation&style=flat-square) ![GitHub issues](https://img.shields.io/github/issues-raw/dp247/Freeview-EPG?color=%232ca9bc&style=flat-square)

<a href='https://ko-fi.com/K3K4EYJL5' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi2.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

Freeview-EPG is a project designed to provide XMLTV data for UK free-to-air TV channels and radio stations for personal use.

![image](https://user-images.githubusercontent.com/9065463/235314658-369f0825-692c-4626-8938-d3f60de3d167.png)

## About
This project exists because of a gap in the market - up until recently, it was very hard to get hold of a free, reliably updated and region-supported XMLTV file. You could either get a TV tuner and grab the data, or pay for it from a service. I didn't like either of those options - looking at what's on TV should be easy and free, so now it is.
### Features
- 48 hours of data, built every 8 hours. If your TV/IPTV client supports auto-refresh, this is very much a set-and-forget solution.
- Supports regional channels, as well as just London-based ones.
- Includes data for both TV and radio stations.
- Data is reliably sourced from UK TV providers, rather than third parties. 
- Builds to an XMLTV file, complete with channel logos and programme images.

## Usage
Grab the XMLTV file from this link and paste it into your favorite IPTV client:
```
https://raw.githubusercontent.com/dp247/Freeview-EPG/master/epg.xml
```

## Contributing
### Guidelines
- Please check [the FAQ](https://github.com/dp247/Freeview-EPG/wiki/FAQ) to make sure your question hasn't already been answered.
- Please report issues [here](https://github.com/dp247/Freeview-EPG/issues/new?assignees=&labels=bug&template=issue-report.md&title=%5BIssue%5D), including as much detail as possible about the problem.
- You can request channels [here](https://github.com/dp247/Freeview-EPG/issues/new?assignees=&labels=channel&template=channel-request.md&title=%5BChannel+request%5D). Please bear in mind that a request is not a guarantee.
- If you'd like to suggest a change or feature, feel free to either open a blank fork and PR back in. Big changes should be discussed in a [blank issue](https://github.com/dp247/Freeview-EPG/issues/new) first.

### To-do
- Improve code, maybe through splitting files and OOP
- Speed up EPG processing, probably using async code
- Finish adding regional stations
- Attempt to fix/find alternate EPG images

## Special thanks
- This project was heavily influenced by iptv-org's [EPG](https://github.com/iptv-org/epg) project
- [ExperiencersInternational](https://github.com/ExperiencersInternational) for all the testing and contributions
- The [tv-logos](https://github.com/tv-logo/tv-logos) and [mediaportal-uk-logos](https://github.com/Jasmeet181/mediaportal-uk-logos) projects, for making channel icon finding so simple
- This project would not be possible without the support of [Jetbrains' OSS licenses](https://www.jetbrains.com/community/opensource/)


## License
[GNU General Public License v3.0](https://github.com/dp247/Freeview-EPG/blob/master/LICENSE)
```text
TLDR from TLDRLegal:
You may copy, distribute and modify the software as long as you track changes/dates in source files. Any modifications to or software including (via compiler) GPL-licensed code must also be made available under the GPL along with build & install instructions.

```

## Disclaimers
- You're welcome to request channel additions (see [Contributing](#contributing)), but I'll only add channels that are **free-to-air**.
- If you're looking for a longer EPG, the [custom](https://github.com/dp247/Freeview-EPG/tree/custom) branch allows for this. However, the logic of the branch is also out-of-date and I have no immediate plans to continue development on it.
- The software and data are provided as-is. While I intend for it to be as reliable as possible, certain aspects are out of my control.

## Related projects
- [YouTube to M3U8](https://github.com/dp247/YouTubeToM3U8) - converts and maintains YouTube live streams in a single M3U8 playlist
- [iptv-cutter](https://github.com/dp247/iptv-cutter) - deduplicator and generator of M3Us for popular IPTV services
- [Freeview M3U](https://github.com/ExperiencersInternational/tvsetup) - companion playlist for this project

## Legal
- This project extracts publicly available data from public-facing websites without the use of private APIs. 
- This project is not owned by, related to or affiliated with BBC, ITV plc, Channel Four Television Corporation, Sky Group, Everyone TV or DTV Services Ltd. 
