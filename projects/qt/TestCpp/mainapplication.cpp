#include"mainapplication.h"
using namespace std;
using namespace utils;



MainApplication::MainApplication(int argc, char* argv[])
{

    cout<<"MainApplication::MainApplication()"<<endl;

    importAppArgs(argc, argv);

}

MainApplication::~MainApplication()
{
    cout<<"MainApplication::~MainApplication()"<<endl;

}

void MainApplication::importAppArgs(int argc, char* argv[])
{
    cout<<"Static MainApplication::importAppArgs()"<<endl;
    while(argc)
    {
        //cout<<"arg"<<argc<<" = "<<argv[argc-1]<<endl;
        string myAppArgStr = argv[argc-1];
        _vecAppArgs.push_back(myAppArgStr);
        --argc;
    }


}

void MainApplication::displayAppArgs()
{
    cout<<"MainApplication::displayAppArgs()"<<endl;

    vector<string>::iterator vecAppArgIter = _vecAppArgs.begin();
    while(vecAppArgIter != _vecAppArgs.end())
    {

        cout<<"Arg = "<<*vecAppArgIter<<endl;
        ++vecAppArgIter;
    }


}

MainAppReturnStatus MainApplication::execute()
{
    cout<<"MainApplication::execute()"<<endl;
    displayAppArgs();

    NodeSearch myNodeSearchObj;

    struct Node* pHead = SAFE_CREATE(Node);
    struct Node* pNewHead;

    if(CHECK_VALIDITY(pHead))
    {
        initNode(pHead,10);
        myNodeSearchObj.display(pHead);

        addNode(pHead,20);
        myNodeSearchObj.display(pHead);

        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        addNode(pHead,30);
        //myNodeSearchObj.display(pHead);
    }


    cout<<"---------------spawn threads----------------"<<endl;

    thread thrDisplayNode(NodeSearch::display,pHead);

    thread thrNodeSearch(NodeSearch::searchNode,pHead,20);

    thrNodeSearch.join();
    thrDisplayNode.join();


    return APP_STATUS_TASK_COMPLETED;
}


