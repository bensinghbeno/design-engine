#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronmainwindow.h"

#include <QJsonObject>
#include <QDebug>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

//    PerceptronMainWindow* pPerceptronMainWindow = new PerceptronMainWindow();

//    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();

//    pPerceptronMainWindow->addPerceptronWidget(*myPerceptronWidget);

//    pPerceptronMainWindow->show();

    QJsonObject jsonobj;
    jsonobj["w00"] = "77";
    jsonobj["w01"] = "100";

    QJsonDocument jsonDoc(jsonobj);
    QString strJson(jsonDoc.toJson(QJsonDocument::Compact));

    qDebug() << strJson;




    return a.exec();
}
