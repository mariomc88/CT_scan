# CT_scan
The project includes the files needed to run the PyQT5 script that runs the GUI used for the control of a CT scan. The projects bases itself on the 
stream.py example code in the grbl 1.1 repository https://github.com/gnea/grbl. The .csv files included are also found there under the doc folder.

Slight modification were done to the source code in order to capture the "end of rotation" trigger signal emitted by the servo motor controller. As the 
implementation lacks any added features which would allow the use of a pin for input, the axis limit pins will be used. 
In the file limits.c from te line 109 to the 151, the lines with the code: mc_reset(); system_set_exec_alarm(EXEC_ALARM_HARD_LIMIT); were replaced by 
printPgmString(PSTR("end\r\n")); being "end" the serial output we wait for to confirm the end of the rotation (In our case, the driver sends one trigger
once the rotation starts, and another one once it finishes, meaning we need to wait for the second of them). In the file config.h, the line 472
#define ENABLE_SOFTWARE_DEBOUNCE // Default disabled. Uncomment to enable. was uncommented to enable the debounce, which in our case reduced drastically
the number of readouts per trigger.
Each limit axis interrupt is mapped to the same function, meaning that in the current state, all would result in the same action. However, it can be 
modified so that each of the interrupts result on a different action, if that was needed.
# Medical_image_analysis
