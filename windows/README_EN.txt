Boltsmith — fastener generator -> STEP (real helical threads)
=============================================================

Shortcut with icon: run Create_Shortcut.bat once - a "Boltsmith" shortcut appears on the
Desktop and in the Start menu (starts without a console window).
Start with console (for troubleshooting): Fastener_Generator.bat.
Switch the language in the window (top right: «Мова / Language»); the choice is remembered.
(the first start downloads the CAD kernel, a few minutes; afterwards it starts in seconds).
Files are saved to the output\ folder next to it (can be changed in the window).

TABS
- Bolt / Screw
  * Standard: 26 ISO/DIN types with exact dimension tables
    (socket cap, cheese, button, countersunk, raised countersunk, hex head, hex flange,
     pan head; hex socket / Torx / slotted / Phillips; set screws, shoulder screws).
  * Custom: M1-M100, any pitch, any head (socket cap, button/dome, countersunk,
    raised countersunk, pan, hex, hex flange, headless) + any drive
    (hex socket, Torx, triangle, square, pentagon, slot, cross).
    Thread length and head dimensions can be set manually.
- Nut
  * Standard: ISO 4032/4033/4035/4036, flange nut DIN 1665, domed cap nut DIN 1587,
    square nut DIN 557, heat-set inserts for 3D printing (McMaster, CNC Kitchen, ruthex, Hilitchi).
  * Custom: M1-M100 - hex, thin/jam, nylon-insert lock nut (ISO 7040, insert as a
    separate body), furniture sleeve nut (flat or countersunk head, any drive),
    coupling nut DIN 6334.
- Washer: ISO 7089/7090/7091/7092/7093/7094, internal tooth lock washer DIN 6797;
  custom flat washer and spring lock washer (DIN 127, real helical shape).
- Threaded rod: any size and length.
- Kit: the bolt from the first tab + nut + washers, positioned for a given grip
  (clamped thickness) - a ready joint for assemblies (each part a separate body).

GENERAL
- Right-hand / left-hand (LH) thread for everything.
- "Single solid body": the thread is merged with the part. If the kernel cannot
  merge it (rare, e.g. countersunk Torx ISO 14581/14584), you get 2 bodies -
  in Fusion: Modify > Combine.
- "Also save STL" - for printing.

NOTES
- Custom parts use formulas close to ISO/DIN; use "Standard" mode for exact sizes.
- Torx and Phillips recesses on custom parts are simplified but realistic.
- Threads use the nominal ISO profile without fit tolerances. For 3D-printed
  nuts/holes add clearance in the slicer or scale up slightly.
