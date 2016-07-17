#include "utils.h"

#ifdef _CPP_UTIL

using namespace std;

#endif

#ifdef _C_UTIL

unsigned int generic_action_function(char* buffer)
{
    printf("\ngeneric_action_function :: buffer %s",buffer);
    return TRUE;
}

unsigned int add_callback(char* buffer_data,unsigned int(*fpAction)(char *))
{
    if(pMainCallbackVector == NULL)
    {
        pMainCallbackVector = cvector_init();
        printf("main_callback_vector_init ::");
    }

    generic_payload* pMyPayload = MALLOC(generic_payload);
    //pMyPayload->command_index = command_id;
    strncpy(pMyPayload->buffer_data,buffer_data,MAX_VECTOR_CHARS);
    pMyPayload->pAction = fpAction;
    unsigned int cmd_index = cvector_push_back(pMainCallbackVector,pMyPayload);
    printf("\nadd_callback ::  command_index %d",cmd_index);
    return cmd_index;
}

void activate_callback(unsigned int command_id)
{
    printf("activate_callback :: command_id %d",command_id);

    if(pMainCallbackVector != NULL)
    {
        if(pMainCallbackVector->size >= command_id)
        {
            printf("Valid command_id = %d :: Activating callback now",command_id);
            pMainCallbackVector->pcvelement[command_id].pAction(pMainCallbackVector->pcvelement[command_id].buffer_data);
        }
        else
        {
            printf("ERROR_INVALID  command_id");

        }
    }
    else
    {
        printf("\ncallback_vector_display_values :: ERROR uninitialized pMainCallbackVector");
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
        printf("\ncallback_vector_display_values :: ERROR uninitialized pMainCallbackVector");
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
        printf("\ncallback_vector_display_values :: ERROR uninitialized pMainCallbackVector");
    }
}



cvector* cvector_init()
{
    cvector* pcvector = (cvector*)(malloc(sizeof(cvector)));
    pcvector->pcvelement = (generic_payload *) malloc(INIT_VECTOR_SIZE*sizeof(generic_payload));
    pcvector->allocated_size = INIT_VECTOR_SIZE;
    pcvector->size = 0;
    printf("\ncvector_init :: allocated_size %d",pcvector->allocated_size);
    return(pcvector);
}

void cvector_remove(cvector* pcvector,unsigned int index)
{
    if(CHECK_VALIDITY(pcvector) && CHECK_VALIDITY(pcvector->pcvelement) && (pcvector->size > index))
    {

        int l = index;
        while ( (l < (pcvector->size-1)) && ( ((pcvector->pcvelement)+l) != NULL))
        {
            pcvector->pcvelement[l] = pcvector->pcvelement[l+1];
            ++l;
        }
        --(pcvector->size);
        printf("\ncvector_remove :: index %d",index);

    }
    else
    {
        printf("\ncvector_remove :: ERROR_INVALID index %d",index);
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
            printf("\ncvector_push_back, ERROR_INVALID_INDICES :: ");
        }

        pcvector->pcvelement[pcvector->size] = *pelem;
        pcvector->pcvelement[pcvector->size].command_index = pcvector->size;
        ++(pcvector->size);
        printf("\ncvector_push_back :: done ");
        return(pcvector->size-1);
    }
    else
    {
        printf("\ncvector_push_back :: ERROR_INVALID_POINTERS ");
        return FALSE;
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
        printf("\ncvector_set_def_values:: size %d",pcvec->size);

    }

}

void cvector_display_values(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        printf("\ncvector_display_buffer_values :: size %d :: ",pcvec->size);

        int l = pcvec->size;
        while(--l >= 0)
        {
            printf(" cmd_%d=%s",pcvec->pcvelement[l].command_index,pcvec->pcvelement[l].buffer_data);
        }
        printf("\n");
    }
}

void cvector_delete(cvector* pcvec)
{
    if(CHECK_VALIDITY(pcvec))
    {
        SAFE_FREE_PURGE(pcvec->pcvelement);
        SAFE_FREE_PURGE(pcvec);
        printf("\ncvector_delete:: res %d",(CHECK_VALIDITY(pcvec)));
    }
}


struct Node* searchNode(struct Node *head, int n)
{
    printf("NodeSearch::searchNode()");

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
        printf("No Node = %d in list",n);
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
    printf("Display Node:: ");
    if(NULL != head )
    {
        Node *list = head;
        while(list)
        {
            printf("%d", list->data);
            list = list->next;
        }
    }
    printf("\n");
    printf("\n");

}



void initNode(Node *head,int n)
{
    head->data = n;
    head->next =NULL;
}

void appendNode(struct Node *head, int n)
{
    Node *newNode = MALLOC(Node);
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
    Node *newNode = MALLOC(Node);
    if(CHECK_VALIDITY(newNode))
    {
        newNode->data = n;
        newNode->next = *head;
        *head = newNode;
    }
}



unsigned int deleteNode(struct Node **head, Node *ptrDel)
{
    Node *cur = *head;
    if(ptrDel == *head)
    {
        *head = cur->next;
        SAFE_FREE_PURGE(ptrDel);
        return TRUE;
    }

    while(cur) {
        if(cur->next == ptrDel)
        {
            cur->next = ptrDel->next;
            SAFE_FREE_PURGE( ptrDel);
            return TRUE;
        }
        cur = cur->next;
    }
    return FALSE;
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
        *pNew = MALLOC(Node);
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
    printf("Deletion:: ");

    struct Node *tmpNode;
    while(*node)
    {
        tmpNode = *node;
        *node = tmpNode->next;
        printf("D-%d",tmpNode->data);
        SAFE_FREE_PURGE(tmpNode);
    }
    printf("\nList is Deleted");

}

void delay_loop(unsigned int loopCount)
{
    while(--loopCount)
    {
    }
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
