/*! \file utils.h
    \brief This source file contains the helper utilities - functions / macros / consts / structs
    \brief Compiler flags for conditional C/C++ based utilities are available.
*/

#ifndef UTILS_H
#define UTILS_H


/*! \brief Following section contains the  utility includes for c
*/

#ifdef _C_UTIL

#include <string.h>
#include <time.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>


#endif

/*! \brief Following section contains the  utility includes for cpp
*/
#ifdef _CPP_UTIL

#include <thread>
#include <iostream>
#include <exception>
#include <thread>
#include <vector>
#include <mutex>
#include <atomic>
#include <string.h>
#include <time.h>
#include <unistd.h>

#endif

/*! \brief Following section contains the macro utilities
*/

#define CHECK_VALIDITY(pValue) ((pValue == NULL)? UTIL_FALSE: UTIL_TRUE)

#ifdef _C_UTIL

#define MALLOC(type) (type*)malloc(sizeof(type));
#define SAFE_FREE_PURGE(pObj) {if(pObj != NULL) {free(pObj);pObj=NULL;}}

#endif

#ifdef _CPP_UTIL

#define SAFE_CREATE(classType) (new (std::nothrow)classType())
#define SAFE_DELETE_PURGE(pObj) {if(pObj != NULL) {delete(pObj);pObj=NULL;}}
#define SAFE_DELETE_ARRAY(pObj) (delete[] pObj)
#define SAFE_PURGE(pObj) (pObj = NULL)

#endif

const int ZERO = 0;
const int UTIL_FALSE = 0;
const int UTIL_TRUE  = 1;
const int MAX_VECTOR_CHARS = 10;
const int INIT_VECTOR_SIZE = 10;
const int INIT_CALLBACK_VECTOR_SIZE = 10;



#ifdef _C_UTIL

/*! \brief Following section contains the struct utilities for a c-style vector implementation
*/

typedef struct generic_payload
{
    unsigned int command_index;
    unsigned char char_element;
    char buffer_data[10];
    unsigned int (*pAction)(char* buffer);
}generic_payload;

typedef struct cvector
{
    generic_payload* pcvelement;
    unsigned int allocated_size;
    unsigned int size;
}cvector;

/*! \brief Following section contains the function utilities for a C-STYLE VECTOR implementation
*/
cvector* cvector_init();
void cvector_delete(cvector *pcvec);
void cvector_set_def_values(cvector* pcvec);
void cvector_display_values(cvector* pcvec);
unsigned int cvector_push_back(cvector* pcvector,generic_payload *pelem);
void cvector_remove(cvector* pcvector, unsigned int index);

/*! \brief Following section contains the function utilities for a FUNCTION CALLBACK implementation based on c-style vector
*/
unsigned int generic_action_function(char* buffer);
unsigned int add_callback(char* buffer_data, unsigned int(*fpAction)(char* buffer));
void activate_callback(unsigned int command_id);
void callback_vector_display_values();
void callback_vector_delete();

/*! \brief Following section contains the struct utilities for a C-STYLE LINKED LIST implementation
*/

typedef struct Node
{
    int data;
    struct Node* next;
}Node;

/*! \brief Following section contains the function utilities for a C-STYLE LINKED LIST implementation
*/

void initNode(Node *head,int n);
void appendNode(struct Node *head, int n);
void insertAtBeginning(struct Node **head, int n);
unsigned int deleteNode(struct Node **head, Node *ptrDel);
struct Node* reverse_list(struct Node** head);
void copyList(struct Node *node, struct Node **pNew);
int compareLists(struct Node *node1, struct Node *node2);
void deleteList(struct Node **node);
struct Node *searchNode(struct Node *head, int n);
void display_list(struct Node *head);


/*! \brief delay_loop function for introducing delays
*/

void delay_loop(unsigned int loopCount);


#endif

#ifdef _CPP_UTIL

/*! \brief Following section contains the class utilities for a RE-ENTRANT, THREAD-SAFE  Singleton class implementation using atomic type
*/

class Singleton
{
public:
    static Singleton* getSingletonInstance();
private:
    Singleton() {}
    static std::atomic<Singleton*> _pInstance;
    static std::mutex _mutexSingleton;
    Singleton(const Singleton&);
    Singleton& operator= (const Singleton& other);
};




/*! \brief Following section contains the static class utilities for a GENERIC POINTER VALIDATOR
*/

template <class U>
class Validator
{
public:
    Validator()
    {
        std::cout<<"Class Validator Constructor"<<std::endl;
    }
    static bool validatePointer(U* pUObj)
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

    ~Validator()
    {}

};


/*! \brief Following section contains the function utilities for a GENERIC POINTER VALIDATOR
*/

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


#endif

#endif // UTILS_H
