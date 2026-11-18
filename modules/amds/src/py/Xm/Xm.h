/* The X toolkit and Motif types named by the AMDS core headers, for the
   build with the Python interface, which uses no X11 and no Motif. Only
   types: any X or Motif function in the core fails to link. The values
   are those of the X11 headers. The other headers of amds.h are empty
   files made by the Makefile. */

#ifndef _amds_py_xm_h
#define _amds_py_xm_h

#include <string.h>

typedef char* String;
typedef char Boolean;
typedef void* XtPointer;
typedef unsigned int Cardinal;
typedef unsigned long Pixel;
typedef unsigned long Atom;
typedef struct _WidgetRec* Widget;
typedef struct _WidgetClassRec* WidgetClass;
typedef struct _XtAppStruct* XtAppContext;
typedef struct { String name; long value; } Arg,* ArgList;
typedef struct __XmStringRec* XmString;
typedef XmString* XmStringTable;
typedef void (*XtCallbackProc)(Widget,XtPointer,XtPointer);

#define True 1
#define False 0

#endif
