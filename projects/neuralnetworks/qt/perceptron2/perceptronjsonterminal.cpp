#include "perceptronjsonterminal.h"
#include <QDebug>
#include <QByteArray>
#include <QProcess>

PerceptronJsonTerminal::PerceptronJsonTerminal(QString pythonEnginePath)
    : m_pythonEnginePath(pythonEnginePath)
{}

PerceptronJsonTerminal::PerceptronJsonTerminal()
{}

void PerceptronJsonTerminal::setPythonEnginePath(QString enginePath)
{
    m_pythonEnginePath = enginePath;
}


void PerceptronJsonTerminal::sendJsonBuffer2Engine(QString& jsonBuffer)
{
    QProcess *myProcess = new QProcess(this);
    //m_pythonEnginePath = "/home/ben/engine/design-engine/projects/python/matrix_dotprod.py";
    QStringList arguments;
    QString strOut;

//    insertvalue("w00","1677");
//    insertvalue("w01","19");
//    insertvalue("w00","77");
//    //qDebug() << "json string buffer = " << getstringbuffer().toStdString().c_str();
//    insertvalue("w01","55");
//    insertJsonStringbuffer(getstringbuffer());
//    qDebug() << "w00 = " << getvalue("w00");
//    qDebug() << "w01 = " << getvalue("w01");
//    arguments  << getstringbuffer().toStdString().c_str();
//    myProcess->start(program, arguments);
//    myProcess->waitForFinished();
//    strOut = myProcess->readAllStandardOutput();
//    qDebug() << strOut.toStdString().c_str();


    arguments.clear();
    arguments  << jsonBuffer.toStdString().c_str();
    myProcess->start(m_pythonEnginePath, arguments);
    myProcess->waitForFinished();
    strOut = myProcess->readAllStandardOutput();
    qDebug() << strOut.toStdString().c_str();
}

