#include "widget.h"
#include <QApplication>
#include <QLabel>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);


    QPixmap m_logo_pic;
    QLabel *m_pic_label = new QLabel();

    m_logo_pic.load("/home/beno/Pictures/dev/blueimage.jpeg");
    m_pic_label->setPixmap(m_logo_pic);

    m_pic_label->showMaximized();

    return a.exec();
}
