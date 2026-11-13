#!/usr/bin/env python3
from pathlib import Path
import argparse, random, html

BG="#0b0b0b"; PAPER="#d8d3c4"; MUTED="#827f76"; GOLD="#c9bea4"

def svg(body, w, h, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}">
<title>{html.escape(title)}</title>
<defs>
 <linearGradient id="gold"><stop stop-color="#f0e9d8"/><stop offset="1" stop-color="#9c9077"/></linearGradient>
 <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#b9b09c" stroke-opacity=".09"/></pattern>
</defs>{body}</svg>'''

def header():
    b=f'''<rect width="1200" height="360" fill="{BG}"/><rect width="1200" height="360" fill="url(#grid)"/>
<path d="M0 38H1200M0 322H1200" stroke="{GOLD}" stroke-opacity=".65"/>
<g fill="{MUTED}" font-family="monospace" font-size="12" letter-spacing="3"><text x="42" y="27">BUNKER // PERSONNEL DATABASE</text><text x="1158" y="27" text-anchor="end">NO. 2B-00 / ONLINE</text><text x="42" y="345">ACCESS LEVEL: DEVELOPER</text><text x="1158" y="345" text-anchor="end">ARCHIVE STATUS: ACTIVE</text></g>
<g transform="translate(600 172)" fill="none" stroke="{GOLD}" stroke-width="1.2" opacity=".85">
<circle r="105" stroke-dasharray="2 8"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="42s" repeatCount="indefinite"/></circle>
<circle r="88" stroke-dasharray="70 14 4 14"><animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="28s" repeatCount="indefinite"/></circle>
<path d="M-130 0H130M0 -130V130" opacity=".5"/></g>
<g transform="translate(600 172)">
<path d="M-22 -62Q-42 -49 -37 -10L-30 25L-15 49H15L30 25L37 -10Q42 -49 22 -62Q0 -76 -22 -62Z" fill="#c9c3b5"/>
<path d="M-32 -42Q0 -76 32 -42L25 -20H-25Z" fill="#171717"/>
<path d="M-24 -18L-10 -11L-24 -5M24 -18L10 -11L24 -5" fill="none" stroke="#0b0b0b" stroke-width="3"/>
<path d="M-15 49L-28 88L-8 105L0 70L8 105L28 88L15 49Z" fill="#a7a193"/>
<path d="M-52 3L-79 44L-61 57L-30 28M52 3L79 44L61 57L30 28" fill="none" stroke="#c9c3b5" stroke-width="9"/>
<path d="M-8 -5H8" stroke="#d8d3c4" stroke-width="2" filter="url(#glow)"/></g>
<g font-family="monospace" fill="{PAPER}"><text x="76" y="135" font-size="38" letter-spacing="5">cikeZ00</text><text x="78" y="164" font-size="13" fill="{GOLD}" letter-spacing="3">SYSTEMS DEVELOPER</text><text x="78" y="199" font-size="12" fill="{MUTED}">Rust / C / C++ / Python</text><text x="1124" y="135" text-anchor="end" font-size="15">UNIT STATUS</text><text x="1124" y="165" text-anchor="end" font-size="26" fill="{GOLD}">OPERATIONAL</text><text x="1124" y="199" text-anchor="end" font-size="12" fill="{MUTED}">MEMORY CORE: STABLE</text></g>
<rect x="0" y="0" width="1200" height="3" fill="{GOLD}" opacity=".5"><animate attributeName="y" values="0;357;0" dur="8s" repeatCount="indefinite"/></rect>'''
    random.seed(8)
    for i in range(65):
        x=(i*197+31)%1200; y=(i*83+19)%360
        b+=f'<circle cx="{x}" cy="{y}" r="{1+i%3*.35}" fill="{GOLD}" opacity=".45"><animate attributeName="opacity" values=".1;.85;.1" dur="{2+i%5}s" begin="-{i%7}s" repeatCount="indefinite"/></circle>'
    return svg(b,1200,360,"operator header")

def divider():
    b=f'''<rect width="1200" height="34" fill="{BG}"/><path d="M0 17H1200" stroke="{GOLD}" stroke-opacity=".45"/>
<path d="M0 17H1200" stroke="{PAPER}" stroke-width="2" stroke-dasharray="70 1130"><animate attributeName="stroke-dashoffset" values="1200;0" dur="5s" repeatCount="indefinite"/></path>
<path d="M600 7L610 17L600 27L590 17Z" fill="{GOLD}"><animateTransform attributeName="transform" type="rotate" from="0 600 17" to="360 600 17" dur="12s" repeatCount="indefinite"/></path>'''
    return svg(b,1200,34,"Scanline divider")

def core():
    b=f'''<rect width="420" height="330" rx="4" fill="{BG}" stroke="{GOLD}" stroke-opacity=".55"/><rect x="12" y="12" width="396" height="306" fill="url(#grid)"/>
<text x="26" y="36" fill="{GOLD}" font-family="monospace" font-size="11" letter-spacing="2">BLACK BOX // MEMORY CORE</text>
<g transform="translate(210 164)" fill="none" stroke="{GOLD}"><circle r="104" stroke-dasharray="1 7" stroke-width="2"><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="35s" repeatCount="indefinite"/></circle>
<circle r="82" stroke-dasharray="34 9 3 9"><animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="21s" repeatCount="indefinite"/></circle>
<circle r="57"><animate attributeName="r" values="53;60;53" dur="4s" repeatCount="indefinite"/></circle><path d="M-125 0H125M0 -125V125" stroke-opacity=".4"/>
<path d="M-35 -26L0 -48L35 -26V26L0 48L-35 26Z" fill="#c9bea4" fill-opacity=".12" stroke-width="2"/><path d="M-17 -9L0 -20L17 -9V12L0 23L-17 12Z" fill="{PAPER}" fill-opacity=".7" filter="url(#glow)"/></g>
<g fill="{PAPER}" font-family="monospace" font-size="10"><text x="25" y="292">CORE TEMP</text><text x="395" y="292" text-anchor="end">37.2°C</text><text x="25" y="307">SYNC RATE</text><text x="395" y="307" text-anchor="end">99.7%</text></g>
<rect x="25" y="278" width="370" height="2" fill="#37352f"/><rect x="25" y="278" width="350" height="2" fill="{GOLD}"><animate attributeName="width" values="320;365;320" dur="5s" repeatCount="indefinite"/></rect>'''
    return svg(b,420,330,"Animated memory core")

def systems():
    b=f'<rect width="1200" height="190" fill="{BG}" stroke="{GOLD}" stroke-opacity=".4"/><text x="28" y="30" fill="{GOLD}" font-family="monospace" font-size="12" letter-spacing="3">POD SUPPORT // LIVE SUBSYSTEM MONITOR</text>'
    names=["RUST / SYSTEMS","C / LOW LEVEL","C++ / ENGINE","PYTHON / TOOLS","POSTGRES / DATA"]
    for i,n in enumerate(names):
        x=30+i*235
        b+=f'''<g transform="translate({x} 55)"><rect width="210" height="105" fill="#121210" stroke="#615b4e" stroke-opacity=".7"/>
<text x="13" y="23" fill="{PAPER}" font-family="monospace" font-size="11">{n}</text><text x="13" y="44" fill="{MUTED}" font-family="monospace" font-size="9">MODULE 0{i+1} // READY</text>
<rect x="13" y="59" width="184" height="3" fill="#38362f"/><rect x="13" y="59" width="{110+i*13}" height="3" fill="{GOLD}"><animate attributeName="width" values="{110+i*13};{170-i*7};{110+i*13}" dur="{3+i*.7}s" repeatCount="indefinite"/></rect>
<path d="M13 82H197" stroke="#514d43" stroke-dasharray="2 5"/><circle cx="190" cy="16" r="3" fill="{GOLD}"><animate attributeName="opacity" values="1;.2;1" dur="{1.4+i*.3}s" repeatCount="indefinite"/></circle></g>'''
    b+=f'<path d="M0 178H1200" stroke="{GOLD}" stroke-opacity=".5"/><text x="28" y="185" fill="{MUTED}" font-family="monospace" font-size="8">ALL SYSTEMS NOMINAL // DATA STREAMS SYNCHRONIZED</text>'
    return svg(b,1200,190,"Animated programming and database subsystem monitor")

def archive():
    random.seed(42)
    b=f'<rect width="1200" height="230" fill="{BG}" stroke="{GOLD}" stroke-opacity=".45"/><text x="24" y="28" fill="{GOLD}" font-family="monospace" font-size="12" letter-spacing="3">MEMORY ARCHIVE // CONTRIBUTION FIELD</text><text x="1176" y="28" text-anchor="end" fill="{MUTED}" font-family="monospace" font-size="10">FRAGMENTS RECOVERED: 365</text>'
    for c in range(53):
        for r in range(7):
            level=random.choices([0,1,2,3,4],[.38,.24,.18,.13,.07])[0]
            op=[.10,.28,.48,.72,.95][level]; x=24+c*18; y=55+r*18; delay=(c*7+r)*.013
            b+=f'<rect x="{x}" y="{y}" width="13" height="13" rx="2" fill="{GOLD}" opacity="{op}"><animate attributeName="opacity" values="{op};{min(1,op+.25)};{op}" dur="{2.5+(c+r)%5}s" begin="-{delay:.2f}s" repeatCount="indefinite"/><animate attributeName="rx" values="2;5;2" dur="{6+c%4}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></rect>'
    b+=f'<path d="M24 190H1176" stroke="#474238"/><text x="24" y="211" fill="{PAPER}" font-family="monospace" font-size="10">LOG DATA: VISUALIZED // CELLS ARE DECORATIVE, NOT LIVE CONTRIBUTION COUNTS</text><text x="1176" y="211" text-anchor="end" fill="{GOLD}" font-family="monospace" font-size="10">RECONSTRUCTION IN PROGRESS</text>'
    return svg(b,1200,230,"Animated memory archive field")

def footer():
    b=f'''<rect width="1200" height="100" fill="{BG}"/><path d="M0 8H1200" stroke="{GOLD}" stroke-opacity=".5"/>
<text x="30" y="42" fill="{PAPER}" font-family="monospace" font-size="13" letter-spacing="3">END OF TRANSMISSION</text><text x="1170" y="42" text-anchor="end" fill="{GOLD}" font-family="monospace" font-size="13" letter-spacing="3">GLORY TO MANKIND</text>
<g transform="translate(30 65)" fill="{MUTED}" font-family="monospace" font-size="9"><text>CONNECTION TERMINATING</text><text x="1138" text-anchor="end">...</text></g>
<rect x="30" y="77" width="1140" height="2" fill="#37352f"/><rect x="30" y="77" width="1140" height="2" fill="{GOLD}"><animate attributeName="width" values="0;1140;0" dur="9s" repeatCount="indefinite"/></rect>'''
    return svg(b,1200,100,"Animated terminal transmission footer")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",default="dist"); out=Path(p.parse_args().output); out.mkdir(parents=True,exist_ok=True)
    visuals={"yorha-header.svg":header(),"yorha-divider.svg":divider(),"yorha-core.svg":core(),"yorha-systems.svg":systems(),"yorha-archive.svg":archive(),"yorha-footer.svg":footer()}
    for name,data in visuals.items(): (out/name).write_text(data,encoding="utf-8"); print("Generated",name)
if __name__=="__main__": main()
