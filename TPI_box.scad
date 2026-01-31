/*
  Simple proof of concept and animation of the gears in the 'TPI box'; a set of gears to achieve zero-error TPI feed-rates for the MW210V lathe family.
  This OpenSCAD file should have reached you accompanied by it's fellow, tpi_box_gears.py, the Python routine that actually does the hard work determining the best set of gears for the application.
*/

/* You gotta get The GHOUL. */
include<TheGHOUL/Config.scad>

$Verbose=true;
S=56;       // Spindle gear.
P=140;      // Primary or 'Input' gear.
I=127;      // Inch gear (smallest integer 'inch-fold' -- 5x24.4=127).
M=40;       // Third gear.
N=35;       // Fourth gear.
Q=I+M-N;    // Fifth (intermediate) gear.
O=P+56-Q;   // Sixth (intermediate) or 'Output' gear.

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
