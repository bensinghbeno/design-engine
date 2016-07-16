/*! \file main.cpp
    \brief This source file contains the main() function
*/

#include"mainapplication.h"
#include "myclass.h"
#include<string.h>

using namespace utils;
using namespace std;


int main(int argc,char* argv[])
{
    cout<<"Program Started"<<endl;

    cvector* pMycvector = cvector_init();
    cvector_set_def_values(pMycvector);
    cvector_display_values(pMycvector);


    cvector_element* pMycvectorlement = MALLOC(cvector_element);
    pMycvectorlement->int_element = 17;
    cvector_push_back(pMycvector,pMycvectorlement);
    cvector_display_values(pMycvector);


    cvector_remove(pMycvector,7);
    cvector_display_values(pMycvector);



    cvector_delete(pMycvector);

    cout<<"\nProgram Completed "<<endl;


}





















/*

///cvector//
///
///
    cvector* pMycvector = cvector_init();
    //cvector_set_def_values(myVector);
    int i = 0;
    while(i < 32)
    {
        cvector_element* pMycvectorlement = MALLOC(cvector_element);
        pMycvectorlement->int_element = i;
        cvector_push_back(pMycvector,pMycvectorlement);
        ++i;
    }

    cvector_display_values(pMycvector);

    cvector_remove(pMycvector,0);

    cvector_display_values(pMycvector);



    cvector_delete(pMycvector);

* ///NODE/////


class student
{
public:
    void disp(){cout<<"student"<<endl;}
};


class teacher
{
public:
    void disp(){cout<<"teacher"<<endl;}
};

class role:public student, public teacher
{
};

    char cstr[2] ;
    string str("Content");


    strncpy(cstr,str.c_str(),str.size());

    cout<<"String = "<<cstr<<endl;


    //MyClass objMyclass1;
    //MyClass objMyclass2(objMyclass1);
    //objMyclass2 = objMyclass1;


    Singleton* pSingleton = NULL;
    pSingleton = Singleton::Instance();

    MainApplication mainAppObj(argc, argv);
    return mainAppObj.execute();


    struct Node* pHead = SAFE_CREATE(Node);
    struct Node* pNewHead;

    if(CHECK_VALIDITY(pHead))
    {
        initNode(pHead,10);
        display(pHead);

        addNode(pHead,20);
        display(pHead);

        addNode(pHead,30);
        display(pHead);

        addNode(pHead,35);
        display(pHead);

        insertFront(&pHead,16);
        display(pHead);







        if(CHECK_VALIDITY(pHead))
        {
            deleteLinkedList(&pHead);
            display(pHead);
        }
    }


        if(CHECK_VALIDITY(pHead))
        {
            copyLinkedList(pHead,&pNewHead);
            display(pNewHead);
        }

        addNode(pNewHead,334);
        display(pNewHead);

        if(compareLinkedList(pHead,pNewHead))
            cout << "Yes, they are same!\n";
        else
            cout << "No, they are different!\n";
        cout << endl;

        reverse(&pHead);
            display(pHead);

        int numDel = 20;
        Node *ptrDelete = searchNode(pHead,numDel);
        if(deleteNode(&pHead,ptrDelete))
            cout << "Node "<< numDel << " deleted!\n";
        display(pHead);
            ////////////////////////////


    Shape* pShape = SAFE_CREATE(Circle);
    if(CHECK_VALIDITY(pShape))
    {
        try
        {
            Circle* pCircle = dynamic_cast<Circle*> (pShape);
            pCircle->setRadius(5);
            pCircle->draw();
        }
        catch(exception& e)
        {
            cout<<"ERROR_EXCEPTION_CAUGHT : "<<e.what()<<endl;
        }
    }

#include"observerAlpha.h"
#include"observerBeta.h"

    Shape* pShapeObj = SAFE_CREATE(Shape);
    SAFE_DELETE(pShapeObj);

    int* pValue = NULL;
    //int val = 100;
    //pValue = &val;

    if(CHECK_VALIDITY(pValue))
    {
        cout<<"VALID_POINTER"<<endl;
    }
    else
    {
        cout<<"INVALID_POINTER"<<endl;
    }
 DataShare objDataShare;

 objDataShare.m_data = 1;
 ObserverAlpha objObserverA;

 objDataShare.m_data = 2;
 ObserverBeta objObserverB;

 objDataShare.m_data = 3;
 cout<<"main.cpp sharedData = "<<DataShare::m_data<<endl;



 //Validator<int> uObj;
 //int * pInt = NULL;
 //uObj.validatePointer(pInt);
//MyClass<int> myClassObj;
 //myclass <int> myobject (100, 75);
 //cout << myobject.getmax()<<endl;
*/












/*

Utils::Node* myNode = Utils::createNode();

    if(Utils::validatePointer(myNode))
    {
        myNode->data = 100;
    }

    if(Utils::validatePointer(myNode))
    {
        cout<<"myNode->data = "<<myNode->data<<endl;
        //delete myNode;
    }
    */
