#include <QCoreApplication>
#include <QDebug>

class IClass
{};


class Myclass
{
public:
    Myclass()
    {
        qDebug() << "Myclass constr";

    }

    IClass* GetIclass()
    {
        return vecIclass.back();
    }


public:
    QVector<IClass*> vecIclass;
};

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    Myclass obj;

    return a.exec();
}
