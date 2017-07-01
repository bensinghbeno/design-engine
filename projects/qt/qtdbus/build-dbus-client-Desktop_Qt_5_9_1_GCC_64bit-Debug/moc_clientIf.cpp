/****************************************************************************
** Meta object code from reading C++ file 'clientIf.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.9.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../dbus-client/clientIf.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'clientIf.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.9.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_SignalReceiver_t {
    QByteArrayData data[4];
    char stringdata0[36];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_SignalReceiver_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_SignalReceiver_t qt_meta_stringdata_SignalReceiver = {
    {
QT_MOC_LITERAL(0, 0, 14), // "SignalReceiver"
QT_MOC_LITERAL(1, 15, 14), // "receivedSignal"
QT_MOC_LITERAL(2, 30, 0), // ""
QT_MOC_LITERAL(3, 31, 4) // "aStr"

    },
    "SignalReceiver\0receivedSignal\0\0aStr"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_SignalReceiver[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       1,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    1,   19,    2, 0x0a /* Public */,

 // slots: parameters
    QMetaType::Void, QMetaType::QString,    3,

       0        // eod
};

void SignalReceiver::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        SignalReceiver *_t = static_cast<SignalReceiver *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->receivedSignal((*reinterpret_cast< QString(*)>(_a[1]))); break;
        default: ;
        }
    }
}

const QMetaObject SignalReceiver::staticMetaObject = {
    { &QObject::staticMetaObject, qt_meta_stringdata_SignalReceiver.data,
      qt_meta_data_SignalReceiver,  qt_static_metacall, nullptr, nullptr}
};


const QMetaObject *SignalReceiver::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *SignalReceiver::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_SignalReceiver.stringdata0))
        return static_cast<void*>(const_cast< SignalReceiver*>(this));
    return QObject::qt_metacast(_clname);
}

int SignalReceiver::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 1)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 1;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 1)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 1;
    }
    return _id;
}
struct qt_meta_stringdata_clientIf_t {
    QByteArrayData data[9];
    char stringdata0[96];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_clientIf_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_clientIf_t qt_meta_stringdata_clientIf = {
    {
QT_MOC_LITERAL(0, 0, 8), // "clientIf"
QT_MOC_LITERAL(1, 9, 17), // "somethingHappened"
QT_MOC_LITERAL(2, 27, 0), // ""
QT_MOC_LITERAL(3, 28, 13), // "signalMessage"
QT_MOC_LITERAL(4, 42, 11), // "SendMessage"
QT_MOC_LITERAL(5, 54, 26), // "QDBusPendingReply<QString>"
QT_MOC_LITERAL(6, 81, 3), // "cmd"
QT_MOC_LITERAL(7, 85, 4), // "read"
QT_MOC_LITERAL(8, 90, 5) // "write"

    },
    "clientIf\0somethingHappened\0\0signalMessage\0"
    "SendMessage\0QDBusPendingReply<QString>\0"
    "cmd\0read\0write"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_clientIf[] = {

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
       1,    1,   34,    2, 0x06 /* Public */,

 // slots: name, argc, parameters, tag, flags
       4,    1,   37,    2, 0x0a /* Public */,
       7,    0,   40,    2, 0x0a /* Public */,
       8,    0,   41,    2, 0x0a /* Public */,

 // signals: parameters
    QMetaType::Void, QMetaType::QString,    3,

 // slots: parameters
    0x80000000 | 5, QMetaType::QString,    6,
    0x80000000 | 5,
    0x80000000 | 5,

       0        // eod
};

void clientIf::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        clientIf *_t = static_cast<clientIf *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->somethingHappened((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 1: { QDBusPendingReply<QString> _r = _t->SendMessage((*reinterpret_cast< const QString(*)>(_a[1])));
            if (_a[0]) *reinterpret_cast< QDBusPendingReply<QString>*>(_a[0]) = std::move(_r); }  break;
        case 2: { QDBusPendingReply<QString> _r = _t->read();
            if (_a[0]) *reinterpret_cast< QDBusPendingReply<QString>*>(_a[0]) = std::move(_r); }  break;
        case 3: { QDBusPendingReply<QString> _r = _t->write();
            if (_a[0]) *reinterpret_cast< QDBusPendingReply<QString>*>(_a[0]) = std::move(_r); }  break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (clientIf::*_t)(const QString & );
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&clientIf::somethingHappened)) {
                *result = 0;
                return;
            }
        }
    }
}

const QMetaObject clientIf::staticMetaObject = {
    { &QDBusAbstractInterface::staticMetaObject, qt_meta_stringdata_clientIf.data,
      qt_meta_data_clientIf,  qt_static_metacall, nullptr, nullptr}
};


const QMetaObject *clientIf::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *clientIf::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_clientIf.stringdata0))
        return static_cast<void*>(const_cast< clientIf*>(this));
    return QDBusAbstractInterface::qt_metacast(_clname);
}

int clientIf::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QDBusAbstractInterface::qt_metacall(_c, _id, _a);
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
void clientIf::somethingHappened(const QString & _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(&_t1)) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
