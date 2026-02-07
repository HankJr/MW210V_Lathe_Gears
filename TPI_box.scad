/*
  Simple proof of concept and animation of the gears in the 'TPI box'; a set of gears to achieve zero-error TPI feed-rates for the MW210V lathe family.
  This OpenSCAD file should have reached you accompanied by it's fellow, tpi_box_gears.py, the Python routine that actually does the hard work determining the best set of gears for the application.
*/

/* You gotta get The GHOUL. */
/*
  The GHOUL is my Great Helpful OpenSCAD Unified Library.
  You can find The GHOUL here:
    http://hankjr.ca/theghoul
  or on GitHub:
    https://github.com/HankJr/The-GHOUL
*/
include<TheGHOUL/Config.scad>

/*
 From tpi_box_gears.py I've chosen this set, because it not only is relatively 'compact', but also allows for a good minimum feedrate of 3.3 thou.
 [140, 127, 40, 35, 132, 64, 44.45]
 This is a decent option, but it's a bit bigger, and its smallest feedrate is 3.6 thou.
 [140, 127, 64, 60, 131, 65, 47.625]
 If you don't mind some bigger gears, this one gives a minimum feedrate of under 2 thou, and can still do 3 tpi. It also manages 7 tpi with zero error--which the others don't--I wonder why ;-).
 [160, 127, 63, 36, 154, 62, 25.4]
*/


$Verbose=true;
S=56;       // Spindle gear.
P=140;      // Primary or 'Input' gear on the main shaft; must be bigger than its keyed neighbour:
I=127;      // Inch gear, keyed to input gear, 127 is the smallest integer 'inch-fold': 5x24.4, a prime number--of course.
M=40;       // Third gear, on the 'countershaft' keyed together with:
N=35;       // Fourth gear, which drives the:
Q=I+M-N;    // Fifth (idler) gear, on the main shaft, which drives:
O=P+S-Q;    // Sixth (idler) or 'Output' gear on the spindle, double-wide, next to the 'S' gear.

// 'Layout' angle; M and N gears position.
LA=120;

// Animation 'Spindle Angle'.
SA=$t*3600;

// Mesh angles; initial and animation 'spindle-factored' rotations of the gears.
// Initial mesh rotation +  layout rotation + animation rotation.
AA=(IsEven(P)?360/P/2:0)                    + -SA*S/P;
BA=                                           -SA*S/P;
CA=                         LA*I/M          +  SA*S/P*I/M;
DA=                         LA*I/M          +  SA*S/P*I/M;
EA=(IsEven(Q)?360/Q/2:0) + -LA*I/M*N/Q      + -SA*S/P*I/M*N/Q;
FA=                         LA*I/M*N/O      +  SA*S/P*I/M*N/O;

// Publish gear info (to correlate with tpi_box_gears.py).
Echo(["PIMNQO = ",P,", ",I,", ",M,", ",N,", ",Q,", ",O,"."]);
Echo(["Output gear Z = ",O,"."]);
Echo(["Effective output teeth Z-eff =",S/P*I/M*N,"."]);

// Flip 'the lot' sso the X-axis becomes the spindle axis. Maybe for more later.
rotate([90,30,0]){

    color(RED) // Spindle gear.
    rotate([0,0,SA])
    linear_extrude(6)
    InvoluteGear(1,S,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(DGN) // First or 'Input' gear.
    translate([(S+P)/2,0,0])
    rotate([0,0,AA])
    linear_extrude(6)
    InvoluteGear(1,P,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(DOG) // Second or 'Inch' gear.
    translate([(S+P)/2,0,6])
    rotate([0,0,BA])
    linear_extrude(6)
    InvoluteGear(1,I,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(DOG) // Third gear.
    translate([(S+P)/2,0,0])
    rotate([0,0,LA])
    translate([(-I-M)/2,0,6])
    rotate([0,0,CA])
    linear_extrude(6)
    InvoluteGear(1,M,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(BLU) // Fourth gear.
    translate([(S+P)/2,0,0])
    rotate([0,0,LA])
    translate([(-Q-N)/2,0,12])
    rotate([0,0,DA])
    linear_extrude(6)
    InvoluteGear(1,N,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(BLU) // Fifth (intermediary) gear.
    translate([(S+P)/2,0,12])
    rotate([0,0,EA])
    linear_extrude(6)
    InvoluteGear(1,Q,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(OSG) // Sixth (intermediary) or 'Output' gear.
    translate([0,0,6])
    rotate([0,0,FA])
    linear_extrude(12)
    InvoluteGear(1,O,Addendum=1,Dedendum=1.25,Shift=0,PressureAngle=14.5,Allowance=0,Title="",Work=undef);

    color(GRN) // Dot identifying the first tooth on the Spindle gear.
    rotate([0,0,SA])
    translate([S/2-2,0,-1])
    linear_extrude(1)
    circle(1);

    color(GRN) // Dot identifying the first tooth on the Output gear.
    rotate([0,0,Mod(LA*I/M*N/O, 360/O) + SA*S/P*I/M*N/O])
    translate([O/2-2,0,-1])
    linear_extrude(7)
    circle(1);

}
