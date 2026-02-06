Can be flashed to esp32 using terminal only, No IDE needed.
Dependencies :
MicroPython Firmware Flashed
mpremote installed
Root access to microcontrollers port (its either ACM* or USB*, If you can not find use : 
$ ls /dev/tty*
Use chmod for admin access to port
simply :
`mpremote connect /dev/ttyACM* fs cp main.py :main.py`
And then reset the microcontroller
The saved password will be saved in password.json in / (root) of microcontroller
Saved passwords can survive resets until manually deleted
