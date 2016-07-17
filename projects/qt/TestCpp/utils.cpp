#include "utils.h"

using namespace std;
namespace utils
{

#ifdef _C_UTIL

bool generic_action_function(char* buffer)
{
    cout<<"\ngeneric_action_function :: buffer = "<<buffer<<endl;
    return true;
}

unsigned int add_callback(char* buffer_data,bool(*fpAction)(char* buffer))
{
    if(pMainCallbackVector == NULL)
    {
        pMainCallbackVector = cvector_init();
        cout<<"main_callback_vector_init ::"<<endl;
    }

    generic_payload* pMyPayload = MALLOC(generic_payload);
    //pMyPayload->command_index = command_id;
    strncpy(pMyPayload->buffer_data,buffer_data,MAX_VECTOR_CHARS);
    pMyPayload->pAction = fpAction;
    unsigned int cmd_index = cvector_push_back(pMainCallbackVector,pMyPayload);
    cout<<"\nadd_callback ::  command_index = "<<cmd_index<<endl;
    return cmd_index;
}

void activate_callback(unsigned int command_id)
{
    cout<<"activate_callback :: command_id = "<<command_id<<endl;

    if(pMainCallbackVector != NULL)
    {
        if(pMainCallbackVector->size >= command_id)
        {
            cout<<"Valid command_id :: Activating callback now"<<command_id<<endl;
            pMainCallbackVector->pcvelement[command_id].pAction(pMainCallbackVector->pcvelement[command_id].buffer_data);
        }
        else
        {
            cout<<"ERROR_INVALID  command_id"<<endl;

        }
    }
    else
    {
        cout<<"\ncallback_vector_display_values :: ERROR uninitialized pMainCallbackVector"<<endl;
    }

}

void callback_vector_display_values()
{
    if(pMainCallbackVector != NULL)
    {
        cvector_display_values(pMainCallbackVector);
    }
    else
    {
        cout<<"\ncallback_vector_display_values :: ERROR uninitialized pMainCallbackVector"<<endl;
    }
}

void callback_vector_delete()
{
    if(pMainCallbackVector != NULL)
    {
        cvector_delete(pMainCallbackVector);
    }
    else
    {
        cout<<"\ncallback_vector_display_values :: ERROR uninitialized pMainCallbackVector"<<endl;
    }
}



cvector* cvector_init()
{
    cvector* pcvector = (cvector*)(malloc(sizeof(cvector)));
    pcvector->pcvelement = (generic_payload *) malloc(INIT_VECTOR_SIZE*sizeof(generic_payload));
    pcvector->allocated_size = INIT_VECTOR_SIZE;
    pcvector->size = 0;
    cout<<"\ncvector_init :: allocated_size = "<<pcvector->allocated_size<<endl;
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

unsigned int cvector_push_back(cvector* pcvector,generic_payload *pelem)
{
    if(CHECK_VALIDITY(pelem) && CHECK_VALIDITY(pcvector))
    {
        int prev_alloc_size = pcvector->allocated_size;
        if(pcvector->size == prev_alloc_size)
        {
            int new_alloc_size = prev_alloc_size + INIT_VECTOR_SIZE;
            pcvector->pcvelement = (generic_payload *) realloc(pcvector->pcvelement,(new_alloc_size)*sizeof(generic_payload));
            pcvector->allocated_size = new_alloc_size;
        }
        else if(pcvector->size > prev_alloc_size)
        {
            return 0;
            cout<<"\ncvector_push_back, ERROR_INVALID_INDICES :: "<<endl;
        }

        pcvector->pcvelement[pcvector->size] = *pelem;
        pcvector->pcvelement[pcvector->size].command_index = pcvector->size;
        ++(pcvector->size);
        cout<<"\ncvector_push_back :: done "<<endl;
        return(pcvector->size-1);

    }
}

void cvector_set_def_values(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        int l = pcvec->allocated_size;

        while(--l >= 0)
        {
            pcvec->pcvelement[l].command_index = l;
            ++(pcvec->size);

        }
        cout<<"\ncvector_set_def_values:: size = "<<pcvec->size<<endl;

    }

}

void cvector_display_values(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        cout<<"\ncvector_display_buffer_values :: size = "<<pcvec->size<<" :: ";

        int l = pcvec->size;
        while(--l >= 0)
        {
            cout<<" cmd_"<<pcvec->pcvelement[l].command_index<<"="<<pcvec->pcvelement[l].buffer_data;
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


struct Node* searchNode(struct Node *head, int n)
{
    cout<<"NodeSearch::searchNode()"<<endl;

    if(CHECK_VALIDITY(head))
    {
        Node *cur = head;
        while(cur) {
            if(cur->data == n)
            {
                display_list(cur);
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

void display_list(struct Node *head)
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



void initNode(Node *head,int n)
{
    head->data = n;
    head->next =NULL;
}

void appendNode(struct Node *head, int n)
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

void insertAtBeginning(struct Node **head, int n)
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

struct Node* reverse_list(struct Node** head)
{
    Node *par_node = *head;
    Node *me = par_node->next;
    Node *child = me->next;

    par_node->next = NULL;
    while(child)
    {
        me->next = par_node;
        par_node = me;
        me = child;
        child = child->next;
    }
    me->next = par_node;
    *head = me;
    return *head;
}

void copyList(struct Node *node, struct Node **pNew)
{
    if(node != NULL)
    {
        *pNew = SAFE_CREATE(Node);
        (*pNew)->data = node->data;
        (*pNew)->next = NULL;
        copyList(node->next, &((*pNew)->next));
    }
    else
    {
        return;
    }

}

int compareLists(struct Node *node1, struct Node *node2)
{
    static int flag;

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
            compareLists(node1->next, node2->next);
    }

    return flag;
}

void deleteList(struct Node **node)
{
    cout<<"Deletion:: "<<endl;

    struct Node *tmpNode;
    while(*node)
    {
        tmpNode = *node;
        *node = tmpNode->next;
        cout<<"D-"<<tmpNode->data<<" ";
        SAFE_DELETE_PURGE(tmpNode);
        SAFE_PURGE(tmpNode);
    }
    cout<<"\nList is Deleted"<<endl;

}

void delay_loop(unsigned int loopCount)
{
    while(--loopCount)
    {
    }
    cout<<endl;
}


#endif

#ifdef _CPP_UTIL

std::atomic<Singleton*> Singleton::_pInstance
{
    NULL
};

std::mutex Singleton::_mutexSingleton;

Singleton* Singleton::getSingletonInstance()
{
    if(_pInstance == nullptr)
    {
        std::lock_guard<std::mutex> lock(_mutexSingleton);
        if(_pInstance == nullptr)
        {
            _pInstance = new Singleton();
        }
    }
    std::cout<<"Singleton::Instance()"<<std::endl;

    return _pInstance;
}

#endif


}//Namespace Utils
