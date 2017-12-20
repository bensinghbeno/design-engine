#ifndef PERCEPTRONJSONGATEWAY_H
#define PERCEPTRONJSONGATEWAY_H

#include <QObject>
class PerceptronJsonTerminal;

class PerceptronJsonModel : public QObject
{
    Q_OBJECT
public:
    explicit PerceptronJsonModel(PerceptronJsonTerminal& perceptronJsonTerminal, QObject *parent = 0);

    PerceptronJsonTerminal& m_perceptronJsonTerminal;

signals:

public slots:
    void sltLayerCountUpdate(int layerCount);

};

#endif // PERCEPTRONJSONGATEWAY_H
