#ifndef MAINAPPLICATION_H
#define MAINAPPLICATION_H

/*! \class MainApplication
    \brief This is the core class that will launch,configure & implement the main application logic
*/


#include "utils.h"


enum MainAppReturnStatus
{
    APP_STATUS_TASK_COMPLETED = 0,
    APP_STATUS_MEMORY_ALLOC_ERROR,
    APP_STATUS_TASK_FAILURE
};


class MainApplication
{
public:
    MainApplication(int argc, char* argv[]);
    ~MainApplication();
    std::vector<std::string> _vecAppArgs;
    void importAppArgs(int argc, char* argv[]);
    void displayAppArgs();
    MainAppReturnStatus execute();

};


#endif // MAINAPPLICATION_H
