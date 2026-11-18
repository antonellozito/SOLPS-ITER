/* Helpers of the Python interface: the layout of the structures Python
   reads and writes (offsets and sizes from the compiler, so that Python
   never assumes a layout), wrappers of the macros of the core, the
   notifications of the core, and the views (amview.c, amfio.c). */

#include <stddef.h>
#include "py_amds.h"

typedef struct _PyField {
  char* name;
  size_t offset,size;
  char type;            /* i int, u unsigned long, p pointer */
} PyField;

#define F(st,field,type) \
  {#st "." #field,offsetof(struct _##st,field), \
    sizeof(((struct _##st*)0)->field),type}

static PyField layout[]={
  F(Doc,db,'p'), F(Doc,views,'p'), F(Doc,undoStack,'p'),
  F(Doc,redoStack,'p'), F(Doc,varDefs,'p'), F(Doc,undoMode,'i'),
  F(Doc,data,'p'), F(Doc,startupParticles,'p'), F(Doc,fileName,'p'),
  F(Doc,reactionCount,'i'), F(Doc,alt,'i'),

  F(Database,particles,'p'), F(Database,reactions,'p'),
  F(Database,reactionTypes,'p'),

  F(Particle,db,'p'), F(Particle,name,'p'), F(Particle,bIsAbstract,'i'),
  F(Particle,superClasses,'p'), F(Particle,subClasses,'p'),

  F(ReactionType,db,'p'), F(ReactionType,name,'p'),

  F(Reaction,db,'p'), F(Reaction,number,'i'), F(Reaction,name,'p'),
  F(Reaction,types,'p'), F(Reaction,input,'p'), F(Reaction,output,'p'),
  F(Reaction,inputSet,'p'), F(Reaction,outputSet,'p'), F(Reaction,vars,'p'),

  F(VarDef,v,'p'), F(VarDef,type,'i'), F(VarDef,flags,'i'),

  F(View,xapp,'p'), F(View,db,'p'), F(View,subset,'p'), F(View,mainView,'p'),
  F(View,dirty,'i'), F(View,rdWidth,'i'), F(View,rsWidth,'i'),
  F(View,rnWidth,'i'), F(View,riWidth,'i'), F(View,bGroupParticles,'i'),

  F(XApp,db,'p'), F(XApp,views,'p'), F(XApp,clipboard,'p'),
  F(XApp,config,'p'), F(XApp,pargc,'p'), F(XApp,argv,'p'),
};

/* Field k of the table; returns its size, 0 after the last one */
size_t GetPyLayout(int k,char** name,size_t* offset) {
  if (k<0 || k>=(int)(sizeof(layout)/sizeof(layout[0]))) return 0;
  *name=layout[k].name;
  *offset=layout[k].offset;
  return layout[k].size;
}

char GetPyLayoutType(int k) {
  return layout[k].type;
}

/* Macros of the core *************************************************/

int PyGroupCount(Group g) { return (int)GroupCount(g); }
Group PyCreateGroup(void) { return CreateGroup(); }
void* PyFreeGroup(Group g) { return FreeGroup(g); }

Reaction PyDocReaction(Doc d,int i) { return d->data[i].r; }
Group PyDocEnabled(Doc d,int i) { return d->data[i].enabled; }
int PyReactionActive(Doc d,Reaction r) { return ReactionActive(d,r); }
int PyIsStartupParticle(Doc d,Particle p) { return IsStartupParticle(d,p); }

void PyUndo(Doc d) { Undo(d); }
void PyRedo(Doc d) { Redo(d); }
void PyCancel(Doc d) { Cancel(d); }

char* PyVarDefName(VarDef vd) { return GetVarDefName(vd); }
char* PyVarDefDescr(VarDef vd) { return GetVarDefDescr(vd); }

/* Notifications and the Python side **********************************/

static PyNotifyProc pyNotify=NULL;
static PyViewProc pyFreeView=NULL,pyUnsaved=NULL;
static PyExitProc pyExit=NULL;

void SetPyProcs(PyNotifyProc notify,PyViewProc freeView,PyViewProc unsaved,
    PyExitProc exitApp) {
  pyNotify=notify;
  pyFreeView=freeView;
  pyUnsaved=unsaved;
  pyExit=exitApp;
}

/* The dependent widgets of the view are on the Python side */
void NotifyView(View w,int msg,void* obj) {
  if (pyNotify!=NULL) pyNotify(w,msg,obj);
}

/* XApp and views (amxapp.c, amview.c, amfio.c) ***********************/

/* CreateXApp up to the database: Python reads the options and resources */
XApp PyCreateXApp(int* pargc,char** argv) {
  XApp xap;

  xap=Malloc(sizeof(*xap));
  memset(xap,0,sizeof(*xap));
  xap->pargc=pargc;
  xap->argv=argv;
  xap->views=CreateGroup();
  return xap;
}

/* CreateView without the widgets: Python makes the window, then adds the
   dependent widgets */
View PyCreateView(XApp xapp,Doc ss,View mainView,int rdWidth,int rsWidth,
    int rnWidth,int riWidth,int bGroupParticles) {
  View w;

  w=Malloc(sizeof(*w));
  memset(w,0,sizeof(*w));
  w->xapp=xapp;
  w->db=ss->db;
  w->subset=ss;
  w->mainView=mainView;
  w->dirty=1;
  w->rdWidth=rdWidth;
  w->rsWidth=rsWidth;
  w->rnWidth=rnWidth;
  w->riWidth=riWidth;
  w->bGroupParticles=bGroupParticles;

  GroupAdd(w->xapp->views,w);
  GroupAdd(w->subset->views,w);
  return w;
}

/* FreeView: the subset views first; Python removes the dependent widgets
   and the window */
void PyFreeView(View w) {
  View w1;
  Index ix;

  for (w1=Group1st(w->xapp->views,&ix);w1!=NULL;w1=Next(&ix))
    if (w1->mainView==w) PyFreeView(w1);

  if (pyFreeView!=NULL) pyFreeView(w);

  GroupDel(w->subset->views,w);
  GroupDel(w->xapp->views,w);
  Free(w);
}

/* CloseView */
void PyCloseView(View w,int bAskUnsaved) {
  Doc ss;
  XApp xap;

  ss=w->subset;
  xap=w->xapp;

  if (bAskUnsaved && ss->alt && GroupCount(ss->views)<2) {
    if (pyUnsaved!=NULL) pyUnsaved(w);
  } else {
    PyFreeView(w);
    if (IsEmptyGroup(ss->views)) FreeDoc(ss);
    if (IsEmptyGroup(xap->views) && pyExit!=NULL) pyExit(0);
  }
}
