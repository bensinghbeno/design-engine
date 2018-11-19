#include <stdio.h>


int main(int argc, char** argv)
{
	printf("\n === MyApp Started ===\n");



   FILE *fp;

   fp = fopen("/dev/mydrivercomm", "w+");
   fputs("AppBuff", fp);
   fclose(fp);

	printf("\n === MyApp Finished ===\n");

	return 0;
}


