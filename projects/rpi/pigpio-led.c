/*
   pulse.c
 
   gcc -o blink-pigpio pigpio-led.c -lpigpio -lrt -lpthread
 
   sudo ./pulse
*/
 
#include <stdio.h>
 
#include <pigpio.h>
 
int main(int argc, char *argv[])
{

 
   if (gpioInitialise() < 0)
   {
      fprintf(stderr, "pigpio initialisation failed\n");
      return 1;
   }
 
   /* Set GPIO modes */
   gpioSetMode(2, PI_OUTPUT);
   gpioSetMode(3, PI_OUTPUT);
   gpioSetMode(4, PI_OUTPUT);
 

 
   while (true)
   {
      gpioWrite(2, 1); /* on */
      gpioWrite(3, 1); /* on */
      gpioWrite(4, 1); /* on */

      time_sleep(1);
 
      gpioWrite(2, 0); /* off */
      gpioWrite(3, 0); /* off */
      gpioWrite(4, 0); /* off */
 
      time_sleep(1);

   }
 
   /* Stop DMA, release resources */
   gpioTerminate();
 
   return 0;
}
