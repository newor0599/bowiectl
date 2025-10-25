## Bowiectl
A program to configure Baseus Bowei MA10 Pro earbud

### Why
The original earbud configuration app is only available on phone and isn't open source (the app always ask for location permission even when I have denied access many times)

### Goal
Create a cross-platform open source app that can configure bowei MA10 Pro earbud

### Usage
#### API
under development 🔨🏗️ 

#### Daemon
`anc [value:int|str]` <br>
**Sets ANC profile**
- 0-10 : ANC Intensity
- off : equavalent of `anc 0`
- on : equavalent of `anc general`
- general
- indoor
- outdoor
- transparent

`help` <br>
**Show help**

`quit` <br>
**Quit daemon**

### Todo
- [ ] API
- [ ] Control setting
- [ ] Low latency toggle
- [ ] Get info (battery, ANC profile, control)

### Plans
1. Intergrate ANC toggle into [my workspace widget](https://github.com/newor0599/ignis-workspace)
2. Add device to an open source gadget manager (eg [gadgetbridge](https://codeberg.org/Freeyourgadget/Gadgetbridge) so i can get rid of that malware)
