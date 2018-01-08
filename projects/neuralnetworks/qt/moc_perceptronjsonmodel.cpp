/****************************************************************************
** Meta object code from reading C++ file 'perceptronjsonmodel.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.5.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "perceptron2/perceptronjsonmodel.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'perceptronjsonmodel.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.5.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_PerceptronJsonModel_t {
    QByteArrayData data[8];
    char stringdata0[142];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_PerceptronJsonModel_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_PerceptronJsonModel_t qt_meta_stringdata_PerceptronJsonModel = {
    {
QT_MOC_LITERAL(0, 0, 19), // "PerceptronJsonModel"
QT_MOC_LITERAL(1, 20, 19), // "sgnJsonModelUpdated"
QT_MOC_LITERAL(2, 40, 0), // ""
QT_MOC_LITERAL(3, 41, 19), // "sltLayerCountUpdate"
QT_MOC_LITERAL(4, 61, 10), // "layerCount"
QT_MOC_LITERAL(5, 72, 25), // "sltMasterInputCountUpdate"
QT_MOC_LITERAL(6, 98, 16), // "masterInputCount"
QT_MOC_LITERAL(7, 115, 26) // "sltCreatePerceptronNetwork"

    },
    "PerceptronJsonModel\0sgnJsonModelUpdated\0"
    "\0sltLayerCountUpdate\0layerCount\0"
    "sltMasterInputCountUpdate\0masterInputCount\0"
    "sltCreatePerceptronNetwork"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_PerceptronJsonModel[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       4,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       1,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    0,   34,    2, 0x06 /* Public */,

 // slots: name, argc, parameters, tag, flags
       3,    1,   35,    2, 0x0a /* Public */,
       5,    1,   38,    2, 0x0a /* Public */,
       7,    0,   41,    2, 0x0a /* Public */,

 // signals: parameters
    QMetaType::Void,

 // slots: parameters
    QMetaType::Void, QMetaType::Int,    4,
    QMetaType::Void, QMetaType::Int,    6,
    QMetaType::Void,

       0        // eod
};

void PerceptronJsonModel::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        PerceptronJsonModel *_t = static_cast<PerceptronJsonModel *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->sgnJsonModelUpdated(); break;
        case 1: _t->sltLayerCountUpdate((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 2: _t->sltMasterInputCountUpdate((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 3: _t->sltCreatePerceptronNetwork(); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (PerceptronJsonModel::*_t)();
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&PerceptronJsonModel::sgnJsonModelUpdated)) {
                *result = 0;
            }
        }
    }
}

const QMetaObject PerceptronJsonModel::staticMetaObject = {
    { &QObject::staticMetaObject, qt_meta_stringdata_PerceptronJsonModel.data,
      qt_meta_data_PerceptronJsonModel,  qt_static_metacall, Q_NULLPTR, Q_NULLPTR}
};


const QMetaObject *PerceptronJsonModel::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *PerceptronJsonModel::qt_metacast(const char *_clname)
{
    if (!_clname) return Q_NULLPTR;
    if (!strcmp(_clname, qt_meta_stringdata_PerceptronJsonModel.stringdata0))
        return static_cast<void*>(const_cast< PerceptronJsonModel*>(this));
    return QObject::qt_metacast(_clname);
}

int PerceptronJsonModel::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 4)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 4;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 4)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 4;
    }
    return _id;
}

// SIGNAL 0
void PerceptronJsonModel::sgnJsonModelUpdated()
{
    QMetaObject::activate(this, &staticMetaObject, 0, Q_NULLPTR);
}
QT_END_MOC_NAMESPACE
