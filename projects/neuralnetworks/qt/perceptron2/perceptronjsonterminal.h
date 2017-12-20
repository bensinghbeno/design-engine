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
    void readJson(QString filepath);
    void loadjsonfile(QString filepath);
    void insertvalue(QString key, QString value);
    QString getvalue(QString key);
    QString& getstringbuffer();
    void insertJsonStringbuffer(QString strJson);

    void demo();

    QFile m_file;
    QString m_fileBuffer;
    QString m_stringbuffer;
    QJsonDocument m_docjson;

    QJsonValue m_valweight;
    QJsonObject m_objlayer;
    QString m_strdocjson;

    //Perceptron Engine
    QString m_pythonEnginePath;
};

#endif // JSONLOAD_H
