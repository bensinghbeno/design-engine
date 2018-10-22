#include "backgroundworker.h"
#include <QDebug>

BackGroundWorker::BackGroundWorker(QObject* parent)
    : QThread(parent)
{

}

void BackGroundWorker::run()
{
    auto itr = 0;
    while (GetWorkerState() == EN_WORKER_STATE::STATE_RUN)
    {
        m_job();
        qDebug() << "--------------------------------------------------------------- iteration = " << ++itr;
    }
}

void BackGroundWorker::StartJob(std::function<void()> job)
{
    m_job = job;

    SetWorkerState(EN_WORKER_STATE::STATE_RUN);

    start();
}

void BackGroundWorker::SetWorkerState(EN_WORKER_STATE aState)
{
    QMutexLocker mutexlocker(&m_mutex);

    m_workerState = aState;
}

EN_WORKER_STATE BackGroundWorker::GetWorkerState()
{
    QMutexLocker mutexlocker(&m_mutex);

    return(m_workerState);
}
