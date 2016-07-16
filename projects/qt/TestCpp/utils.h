#ifndef UTILS_H
#define UTILS_H

#include<typeinfo>
#include<iostream>
#include "base.h"
#include "derived.h"
#include <exception>
#include <thread>
#include <vector>
#include <mutex>
#include <atomic>
#include<string.h>


#define CHECK_VALIDITY(pValue) ((pValue == NULL)? false: true)
#define SAFE_CREATE(classType) (new (std::nothrow)classType())
#define SAFE_DELETE(pObj) {if(pObj != NULL) delete pObj;}
#define SAFE_FREE_PURGE(pObj) {if(pObj != NULL) {free(pObj);pObj=NULL;}}
#define SAFE_DELETE_ARRAY(pObj) (delete[] pObj)
#define SAFE_PURGE(pObj) (pObj = NULL)
#define MALLOC(type) (type*)malloc(sizeof(type));

const int ZERO = 0;
const int MAX_VECTOR_CHARS = 10;
const int INIT_VECTOR_SIZE = 10;
const int INIT_CALLBACK_VECTOR_SIZE = 10;



namespace utils
{

////vector implementation//////////////////////////////////////////////////////

struct generic_payload
{
    unsigned int command_id;
    unsigned char char_element;
    char buffer_data[MAX_VECTOR_CHARS];//    bool(*fp)(char* buffer);
    bool(*pAction)(char* buffer);
};

struct cvector
{
    generic_payload* pcvelement;
    unsigned int allocated_size;
    unsigned int size;
};

bool generic_action_function(char* buffer);
void add_callback(cvector* pcvector,unsigned int command_id,char* buffer_data,bool(*fpAction)(char* buffer));
cvector* cvector_init();
void cvector_delete(cvector *pcvec);
void cvector_set_def_values(cvector* pcvec);
void cvector_display_values(cvector* pcvec);
void cvector_push_back(cvector* pcvector,generic_payload *pelem);
void cvector_remove(cvector* pcvector, unsigned int index);


///Singleton///////////////////////////////////////////////////////////////////

class Singleton
{
public:
    static Singleton* Instance();
private:
    Singleton() {}
    static std::atomic<Singleton*> pinstance;
    static std::mutex m_;
    Singleton(const Singleton&);
    Singleton& operator= (const Singleton& other);
};



///////////////Thread Callables////////////////////////////////////////////////

void buzzer(unsigned int loopCount);

struct Node
{
    int data;
    Node* next;
};


class NodeSearch
{
public:
    NodeSearch();
    ~NodeSearch();
    void operator() ();
    static struct Node *searchNode(struct Node *head, int n);
    static void display(struct Node *head);
};


///////List Utils///////////////////////////////////////////////////////////////


void initNode(Node *head,int n);
void addNode(struct Node *head, int n);
void insertFront(struct Node **head, int n);
bool deleteNode(struct Node **head, Node *ptrDel);
struct Node* reverse(struct Node** head);
void copyLinkedList(struct Node *node, struct Node **pNew);
int compareLinkedList(struct Node *node1, struct Node *node2);
void deleteLinkedList(struct Node **node);



class DataShare
{
public:
    DataShare();
    static int m_data;
private:

};

/////////////////////////////Template Class Validator////////////////////////////////

template <class U>
class Validator
{
public:
    Validator();
    static bool validatePointer(U* pUObj);
    ~Validator();

};

template <class U>
Validator<U>::Validator()
{
    std::cout<<"Class Validator Constructor"<<std::endl;
}

template<class U>
Validator<U>::~Validator()
{
    std::cout<<"Class Validator Constructor"<<std::endl;
}

template<class U>
bool Validator<U>::validatePointer(U* pUObj)
{
    if(pUObj ==  NULL)
    {
        std::cout<<"ERROR_POINTER_IS_INVALID"<<std::endl;
        return false;
    }
    else
    {
        std::cout<<"POINTER_IS_VALID"<<std::endl;
        return true;
    }

}

/////////////////////////////Template Function Validator////////////////////////////////

template <typename T>
bool validatePointer(T* genericType)
{
    if(genericType ==  NULL)
    {
        std::cout<<"ERROR_POINTER_IS_NULL"<<std::endl;
        return false;
    }
    else
    {
        std::cout<<"POINTER_IS_VALID"<<std::endl;
        return true;
    }
}

}

#endif // UTILS_H
