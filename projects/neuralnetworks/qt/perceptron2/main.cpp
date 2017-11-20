#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronmainwindow.h"

#include <QDebug>
#include "jsonhelper.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

//    PerceptronMainWindow* pPerceptronMainWindow = new PerceptronMainWindow();

//    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();

//    pPerceptronMainWindow->addPerceptronWidget(*myPerceptronWidget);

//    pPerceptronMainWindow->show();

//    QJsonObject jsonobj;
//    jsonobj["w00"] = "77";
//    jsonobj["w01"] = "100";
//    qDebug() << "jsonobj[w00] = " << jsonobj["w00"].toString();



//    QJsonDocument jsonDoc(jsonobj);
//    QByteArray jsonByteArray = jsonDoc.toBinaryData();
//    qDebug() << "jsonByteArray1 = " << jsonByteArray;



////    QByteArray jsonByteArray2 = jsonByteArray;
//    QJsonDocument jsonDoc2(jsonByteArray);
//    //jsonDoc2.fromBinaryData(jsonByteArray);
//    QByteArray jsonByteArray2 = jsonDoc2.toBinaryData();
//    qDebug() << "jsonByteArray2 = " << jsonByteArray2;


    JsonLoad jsonloadobj;
    jsonloadobj.readJson("../perceptron2/neuralnetwork.json");




    return a.exec();
}
