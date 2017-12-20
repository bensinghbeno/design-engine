#ifndef JSONLOAD_H
#define JSONLOAD_H

#include <QFile>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QByteArray>
#include <QJsonValue>

class PerceptronJsonTerminal : public QObject
{
public:
    PerceptronJsonTerminal(QString pythonEnginePath);
    PerceptronJsonTerminal();

    void setPythonEnginePath(QString enginePath);

    //Perceptron Engine
    QString m_pythonEnginePath;

    void sendJsonBuffer2Engine(QString& jsonBuffer);
};

#endif // JSONLOAD_H
