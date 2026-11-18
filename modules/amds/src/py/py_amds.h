/* AMDS with the Python interface: the C part that the Python front end
   (lib/python/amds) loads with ctypes, built with the core into a shared
   library without Motif and X11.

   The core calls the front end only through NotifyView, which goes to
   Python. The helpers stand for the macros of the core, and the
   functions of py_cmds.c are the core part of the callbacks of the Motif
   front end, with the same core calls in the same order. */

#ifndef _py_amds_h
#define _py_amds_h

#include "amds.h"

typedef void (*PyNotifyProc)(View w,int msg,void* obj);
typedef void (*PyViewProc)(View w);
typedef void (*PyExitProc)(int code);
typedef void (*PyItemProc)(char* text);

/* The Python side: notifications, a view to be freed (its dependent
   widgets and its window), the Unsaved work question, the end */
void SetPyProcs(PyNotifyProc notify,PyViewProc freeView,PyViewProc unsaved,
    PyExitProc exitApp);

/* Structures */
XApp PyCreateXApp(int* pargc,char** argv);
View PyCreateView(XApp xapp,Doc ss,View mainView,int rdWidth,int rsWidth,
    int rnWidth,int riWidth,int bGroupParticles);
void PyFreeView(View w);
void PyCloseView(View w,int bAskUnsaved);

#endif
