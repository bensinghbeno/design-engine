#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/uaccess.h>
#include <linux/fs.h>
#include <linux/slab.h>


MODULE_LICENSE("GPL");
MODULE_AUTHOR("Bensingh Beno");
MODULE_DESCRIPTION("A simple driver to get data from userland to kernel module");

#define DEVICE_NAME "lkm_example"
#define EXAMPLE_MSG "Hello, World!\n"
#define MSG_BUFFER_LEN 15

static int major_num;
static int device_open_count = 0;
static char msg_buffer[MSG_BUFFER_LEN];
static char *msg_ptr;
static int my_bytes_read;
char* rx_buffer;
int BUFFER_SIZE=64;


static ssize_t device_read(struct file *flip, char *buffer, size_t len, loff_t *offset)
{
    int bytes_read = 0;

    printk(KERN_INFO" === My Driver Comm : device_read start === \n");

    if (*msg_ptr == 0)
    {
        msg_ptr = msg_buffer;
    }

    while (len && *msg_ptr)
    {
        put_user(*(msg_ptr++), buffer++);
        len--;
        bytes_read++;
        ++my_bytes_read;
    }

    printk(KERN_INFO" === My Driver Comm : device_read finish === \n");
    if(my_bytes_read >= MSG_BUFFER_LEN)
    {
        my_bytes_read = 0;
        return 0;
    }

    return bytes_read;
}


static ssize_t device_write(struct file *flip, const char *buffer, size_t len, loff_t *offset)
{
    int retval = 0;

    printk(KERN_INFO" === My Driver Comm : device_write start === \n");
    if(len <= 1)
    {
        printk(KERN_ALERT" === My Driver Comm : device_write Invalid length of user buffer === \n");
    }
    else if(len > 10)
    {
        printk(KERN_ALERT" === My Driver Comm : device_write Invalid length of user buffer === \n");
    }
    else
    {
        printk(KERN_INFO" === My Driver Comm : device_write Good length of user buffer === \n");

        printk("New message from userspace - len:%ld\n",len);

        retval = copy_from_user(rx_buffer,buffer,len);
        rx_buffer[len] = '\0';

        printk("Buffer = %s\n", rx_buffer);
        printk("initialize rx buffer..\n");

        printk("content of rx buffer  = %s\n", rx_buffer);

    }

    return len;
}

static int device_open(struct inode *inode, struct file *file)
{
    printk(KERN_INFO" === My Driver Comm : device_open start === \n");
    if (device_open_count)
    {
        return -EBUSY;
    }
    device_open_count++;
    try_module_get(THIS_MODULE);
    printk(KERN_INFO" === My Driver Comm : device_open start === \n");
    return 0;
}


static int device_release(struct inode *inode, struct file *file)
{
    device_open_count--;
    printk(KERN_INFO" === My Driver Comm : device_release === \n");
    module_put(THIS_MODULE);
    return 0;
}

static struct file_operations file_ops = {
 .read = device_read,
 .write = device_write,
 .open = device_open,
 .release = device_release
};



static int __init my_module_init(void)
{
    printk(KERN_INFO" === Hello My Driver Comm : my_module_init === \n");

    rx_buffer = kmalloc(BUFFER_SIZE,  GFP_KERNEL);

    my_bytes_read = 0;

    /* Fill buffer with our message */
    strncpy(msg_buffer, EXAMPLE_MSG, MSG_BUFFER_LEN);
    /* Set the msg_ptr to the buffer */
    msg_ptr = msg_buffer;
    /* Try to register character device */
    major_num = register_chrdev(0, "lkm_example", &file_ops);
    if (major_num < 0)
    {
        printk(KERN_ALERT "Could not register device: %d\n", major_num);
        return major_num;
    }

    else
    {
        printk(KERN_INFO "lkm_example module loaded with device major number %d\n", major_num);
    }
    return 0;
}


static void __exit my_module_exit(void)
{
    printk(KERN_INFO" == Goodbye My Driver Comm === \n");
    unregister_chrdev(major_num, DEVICE_NAME);

    if (rx_buffer) {
        kfree(rx_buffer);
    }

    printk(KERN_INFO "Goodbye, World!\n");
}

module_init(my_module_init);
module_exit(my_module_exit);
