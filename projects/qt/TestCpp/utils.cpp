#include "utils.h"

using namespace std;
namespace utils
{

///cvector////


cvector* cvector_init()
{
    cvector* pcvector = (cvector*)(malloc(sizeof(cvector)));
    pcvector->pcvelement = (cvector_element *) malloc(INIT_VECTOR_SIZE*sizeof(cvector_element));
    pcvector->allocated_size = INIT_VECTOR_SIZE;
    pcvector->size = 0;
    cout<<"\ncvector_init :: size = "<<pcvector->allocated_size<<endl;
    return(pcvector);
}

void cvector_remove(cvector* pcvector,unsigned int index)
{
    if(CHECK_VALIDITY(pcvector) && CHECK_VALIDITY(pcvector->pcvelement) && (pcvector->size > index))
    {
        //cout<<"l = "<<0<<"int = "<<pcvector->pcvelement[0].int_element<<endl;

        int l = index;
        while ( (l < (pcvector->size-1)) && ( ((pcvector->pcvelement)+l) != NULL))
        {
            pcvector->pcvelement[l] = pcvector->pcvelement[l+1];
            //cout<<"l = "<<l<<"int = "<<pcvector->pcvelement[l].int_element<<endl;
            ++l;
        }
        --(pcvector->size);
        cout<<"\ncvector_remove :: index = "<<index<<endl;

    }
    else
    {
        cout<<"\ncvector_remove :: ERROR_INVALID index = "<<index<<endl;
    }
}
void cvector_push_back(cvector* pcvector,cvector_element *pelem)
{
    if(CHECK_VALIDITY(pelem) && CHECK_VALIDITY(pcvector))
    {
        int prev_alloc_size = pcvector->allocated_size;
        if(pcvector->size == prev_alloc_size)
        {
            int new_alloc_size = prev_alloc_size + INIT_VECTOR_SIZE;
            pcvector->pcvelement = (cvector_element *) realloc(pcvector->pcvelement,(new_alloc_size)*sizeof(cvector_element));
            pcvector->allocated_size = new_alloc_size;

            pcvector->pcvelement[pcvector->size] = *pelem;
            ++(pcvector->size);
        }
        else if(pcvector->size == 0)
        {
            pcvector->pcvelement[0] = *pelem;
            ++(pcvector->size);
        }
        else if(pcvector->size < prev_alloc_size)
        {
            pcvector->pcvelement[pcvector->size] = *pelem;
            ++(pcvector->size);
        }
        else
        {
            return;
        }
        cout<<"\ncvector_push_back, size :: "<<pcvector->size<<endl;

    }
}

void cvector_set_def_values(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        int l = pcvec->allocated_size;

        while(--l >= 0)
        {
            pcvec->pcvelement[l].int_element = l;
            ++(pcvec->size);

        }
        cout<<"\ncvector_set_def_values:: size = "<<pcvec->size<<endl;

    }

}

void cvector_display_values(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        cout<<"\ncvector_display_values :: size = "<<pcvec->size<<"\n values :: ";

        int l = pcvec->size;
        while(--l >= 0)
        {
            cout<<" "<<pcvec->pcvelement[l].int_element;
        }
        cout<<endl;
    }
}

void cvector_delete(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        SAFE_FREE_PURGE(pcvec->pcvelement);
        SAFE_FREE_PURGE(pcvec);
        cout<<"\ncvector_delete:: res = "<<(CHECK_VALIDITY(pcvec))<<endl;
    }
}


///Singleton/////

std::atomic<Singleton*> Singleton::pinstance
{
    nullptr
};

std::mutex Singleton::m_;

Singleton* Singleton::Instance()
{
    if(pinstance == nullptr)
    {
        std::lock_guard<std::mutex> lock(m_);
        if(pinstance == nullptr)
        {
            pinstance = new Singleton();
        }
    }
    std::cout<<"Singleton::Instance()"<<std::endl;

    return pinstance;
}


//////////////////////Thread Callables///////////////////////////////////


void buzzer(unsigned int loopCount)
{
    while(--loopCount)
    {
        cout<<"Z";
    }
    cout<<endl;
}

NodeSearch::NodeSearch()
{
    cout<<"NodeSearch::NodeSearch()"<<endl;
}

void NodeSearch::operator() ()
{
    cout<<"NodeSearch::operator()"<<endl;
}


NodeSearch::~NodeSearch()
{
    cout<<"NodeSearch::~NodeSearch()"<<endl;
}

struct Node* NodeSearch::searchNode(struct Node *head, int n)
{
    cout<<"NodeSearch::searchNode()"<<endl;

    if(CHECK_VALIDITY(head))
    {
        Node *cur = head;
        while(cur) {
            if(cur->data == n)
            {
                display(cur);
                return cur;
            }
            cur = cur->next;
        }
        cout << "No Node " << n << " in list.\n";
        cur = NULL;
        return cur;
    }
    else
    {
        Node * pNode = NULL;
        return pNode;
    }
}

void NodeSearch::display(struct Node *head)
{
    cout<<"Display Node:: ";
    if(NULL != head )
    {
        Node *list = head;
        while(list)
        {
            cout << list->data << " ";
            list = list->next;
        }
    }
    cout << endl;
    cout << endl;
}

//////////////////////List Utils///////////////////////////////////


// Create the 1st Node
void initNode(Node *head,int n)
{
    head->data = n;
    head->next =NULL;
}

// apending
void addNode(struct Node *head, int n)
{
    Node *newNode = SAFE_CREATE(Node);
    if(CHECK_VALIDITY(newNode))
    {
        newNode->data = n;
        newNode->next = NULL;

        Node *cur = head;
        while(cur) {
            if(cur->next == NULL)
            {
                cur->next = newNode;
                return;
            }
            cur = cur->next;
        }
    }
}

void insertFront(struct Node **head, int n)
{
    Node *newNode = SAFE_CREATE(Node);
    if(CHECK_VALIDITY(newNode))
    {
        newNode->data = n;
        newNode->next = *head;
        *head = newNode;
    }
}



bool deleteNode(struct Node **head, Node *ptrDel)
{
    Node *cur = *head;
    if(ptrDel == *head)
    {
        *head = cur->next;
        delete ptrDel;
        return true;
    }

    while(cur) {
        if(cur->next == ptrDel)
        {
            cur->next = ptrDel->next;
            delete ptrDel;
            return true;
        }
        cur = cur->next;
    }
    return false;
}

// reverse the list
struct Node* reverse(struct Node** head)
{
    Node *parent = *head;
    Node *me = parent->next;
    Node *child = me->next;

    //make parent as tail
    parent->next = NULL;
    while(child)
    {
        me->next = parent;
        parent = me;
        me = child;
        child = child->next;
    }
    me->next = parent;
    *head = me;
    return *head;
}

// Creating a copy of a linked list //
void copyLinkedList(struct Node *node, struct Node **pNew)
{
    if(node != NULL)
    {
        *pNew = SAFE_CREATE(Node);
        (*pNew)->data = node->data;
        (*pNew)->next = NULL;
        copyLinkedList(node->next, &((*pNew)->next));
    }
    else
    {
        return;
    }

}

// Compare two linked list //
// return value: same(1), different(0) //
int compareLinkedList(struct Node *node1, struct Node *node2)
{
    static int flag;

    // both lists are NULL //
    if(node1 == NULL && node2 == NULL)
    {
        flag = 1;
    }
    else {
        if(node1 == NULL || node2 == NULL)
            flag = 0;
        else if(node1->data != node2->data)
            flag = 0;
        else
            compareLinkedList(node1->next, node2->next);
    }

    return flag;
}

void deleteLinkedList(struct Node **node)
{
    cout<<"Deletion:: "<<endl;

    struct Node *tmpNode;
    while(*node)
    {
        tmpNode = *node;
        *node = tmpNode->next;
        cout<<"D-"<<tmpNode->data<<" ";
        SAFE_DELETE(tmpNode);
        SAFE_PURGE(tmpNode);
    }
    cout<<"\nList is Deleted"<<endl;

}


///////////////////////////////////////////////////////////////////


DataShare::DataShare()
{
}
int DataShare::m_data = 777;


}//Namespace Utils
