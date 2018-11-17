/*
* Simple Linux Char Driver
*
*
*/

#include <linux/module.h>
#include <linux/kernel.h>

int init_module(void)
{
	printk(KERN_INFO" === Hello linux driver === \n");
	return 0;
}

void cleanup_module(void)
{
	printk(KERN_INFO" === Goodbye linux driver === \n");
}
