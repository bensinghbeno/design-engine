#ifndef BACKGROUNDWORKER_H
#define BACKGROUNDWORKER_H

#include <qthread.h>
#include <thread>
#include <functional>
#include <QMutexLocker>

enum EN_WORKER_STATE
{
    STATE_RUN   = 0,
    STATE_STOP  = 1,
};

class BackGroundWorker : public QThread
{

public:
    BackGroundWorker(QObject* parent = 0);

    void run();

    void StartJob(std::function<void()> job);

    void SetWorkerState(EN_WORKER_STATE aState);

    EN_WORKER_STATE GetWorkerState();

private:

    std::function<void()> m_job;

    QMutex m_mutex;

    EN_WORKER_STATE m_workerState;
};

#endif // BACKGROUNDWORKER_H
