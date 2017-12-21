#ifndef PERCEPTRONJSONGATEWAY_H
#define PERCEPTRONJSONGATEWAY_H

#include <QObject>
#include "perceptronjsonterminal.h"

class PerceptronJsonModel : public QObject
{
    Q_OBJECT
public:
    explicit PerceptronJsonModel(QString pythonEnginePath, QObject *parent = 0);

    PerceptronJsonTerminal m_perceptronJsonTerminal;

    //Json Helper
    QFile m_file;
    QString m_fileBuffer;
    QString m_stringbuffer;
    QJsonDocument m_docjson;
    QJsonValue m_valweight;
    QJsonObject m_objlayer;
    QString m_strdocjson;
    void readJson(QString filepath);
    void loadjsonfile(QString filepath);
    void insertvalue(QString key, QString value);
    QString getvalue(QString key);
    QString& getstringbuffer();
    void insertJsonStringbuffer(QString strJson);
    void demo();

    //Json Engine
    void sendJsonBuffer();

signals:

public slots:
    void sltLayerCountUpdate(int layerCount);
    void sltMasterInputCountUpdate(int masterInputCount);
    void sltRequestPerceptronMatrix();

};

#endif // PERCEPTRONJSONGATEWAY_H
