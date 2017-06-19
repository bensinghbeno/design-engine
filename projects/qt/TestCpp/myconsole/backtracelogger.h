#ifndef BACKTRACELOGGER_H
#define BACKTRACELOGGER_H



/*

#include <stdio.h>
#include <execinfo.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>
#include <cxxabi.h>
#include <iostream>


void handler(int sig) {
  void *array[10];
  size_t size;

  // get void*'s for all entries on the stack
  size = backtrace(array, 10);

  // print out all the frames to stderr
  fprintf(stderr, "Error: signal %d:\n", sig);
  backtrace_symbols_fd(array, size, STDERR_FILENO);

  int status = -1;
  char *demangledName = abi::__cxa_demangle( "_Z7handleri", NULL, NULL, &status );
  if ( status == 0 )
  {
    std::cout << "!!! DemangledName = "<< demangledName  << std::endl;
  }
  free( demangledName );


  exit(1);
}

void baz() {
 int *foo = (int*)-1; // make a bad pointer
  printf("%d\n", *foo);       // causes segfault
}

void bar() { baz(); }
void foo() { bar(); }


int main(int argc, char **argv)
{
  printf("Hello Backtracer!!\n");
  signal(SIGSEGV, handler);   // install our handler
  foo(); // this will call foo, bar, and baz.  baz segfaults.
}
*/
#endif // BACKTRACELOGGER_H

