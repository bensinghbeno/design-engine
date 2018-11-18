/*
* Simple Linux Char Driver
*
*
*/

#include <linux/module.h>
#include <linux/kernel.h>

static int my_init_module(void)
{
	printk(KERN_INFO" === Hello linux driver === \n");
	return 0;
}

static void my_exit_module(void)
{
	printk(KERN_INFO" === Goodbye linux driver === \n");
}

static void ben_func(void)
{
	printk(KERN_INFO" === ben_func linux driver === \n");	
}

EXPORT_SYMBOL(ben_func);

module_init(my_init_module);
module_exit(my_exit_module);
