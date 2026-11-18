/* The graphs of the Python interface: the graph view of the graph
   dialog and its PostScript printing (amgraph.c). The drawing and
   PostScript code is the code of amgraph.c, function by function, so that
   the coordinates and the PostScript numbers are those of the Motif
   program (same compiler, same flags, same contractions); the screen view
   records its calls for Python (PyGraphProc), which draws them, and asks
   Python for the text extents. The calculation process, the timers and
   the fields of the dialog are on the Python side. */

#include <stdio.h>
#include "py_amds.h"

typedef unsigned long Font;             /* the X font id of the view */

/* Data structures and constants */

#define GD_DENSITIES 10
#define GDL_ALLOCINCR 20

#define V_NONE MAXDOUBLE

#define TEX_LEFT "E-88"
#define TEX_BOTTOM "E-88"
#define TEX_RIGHT "W 8.88E+88"
#define TEX_TOP "ABCDEFGH_H.8_8.88.88w"

#define GLVMCOUNT       4

#define VM0_GRAPHLINE   0
#define VM1_GRAPHLINE   1
#define VM2_GRAPHLINE   2
#define VM3_GRAPHLINE   3
#define VM4_GRAPHLINE   4
#define VM_GRIDLINE     100
#define VM_GRIDTEXT     101
#define VM1_LEGENDTEXT  102
#define VM1_GRAPHSYMS   103
#define VM0_GRAPHSYMS   104
#define VM_BORDER       105
#define VM0_LEGENDTEXT  106

#define DT_ABOVE        0x0001
#define DT_ORAQUE       0x0002
#define DT_CENTERX      0x0004
#define DT_CENTERY      0x0008
#define DT_LEFT         0x0010

#define SYMSIZE_X       3
#define SYMS_PER_LINE   10


typedef struct _GView {

/* Generic structure */

  void* x;

  double width,height,symSize,clipX1,clipY1,clipX2,clipY2;

  void* (*Free)(struct _GView* w);
  void (*SetMode)(struct _GView* w,int mode);
  void (*DrawLine)(struct _GView* w,double x1,double y1,double x2,double y2);
  void (*DrawText)(struct _GView* w,double x,double y,char* text,int type);
  void (*GetTextExtent)(struct _GView* w,char* text,double* px,double* py);
  void (*Clear)(struct _GView* gv,int bExposure);

/* GraphLine extensions */

  struct _GraphDlg* dlg; /* Stores GraphLines */
  double glMinX,glMinY,glMaxX,glMaxY,glW,glH,glLOff,glROff,glTOff,glBOff;
  int bLegendOn;
  
  /* Fix for the font problem */
  Font font;
}* GView;

typedef struct _GraphDlg {
  View w;
  GView gv;
  Group lines;
  Reaction calcReaction;
  double vT1,vT2,vY1,vY2,vDensity[GD_DENSITIES];
  int id;                               /* the dialog on the Python side */
  int realized;                         /* the drawing area has a window */
}* GraphDlg;

typedef struct {
  GraphDlg dlg;
  Reaction r;
  double t1,t2,d;
  struct {double x,y;} *xy;
  int numPoints,allocedPoints,dNumber,rNumber;
}* GraphLine;

typedef struct _PsGViewExt {
  FILE* f;
  double orgWidth,orgHeight,orgMargin;
  double r,g,b,lw;
  int bBW;
}* PsGViewExt;

#define GLX2GV(gv,x) \
  (((x)-(gv)->glMinX)/((gv)->glMaxX-(gv)->glMinX)*(gv)->glW+(gv)->glLOff)
#define GLY2GV(gv,y) \
  (((y)-(gv)->glMaxY)/((gv)->glMinY-(gv)->glMaxY)*(gv)->glH+(gv)->glTOff)

/* Calls of the screen view and events for Python: op 'M' mode (i), 'L'
   line (a,b,c,d), 'T' text (a,b position, i flags, text), 'E' text extent
   (a,b), 'C' clear (i: with exposure), 'U' repaint timer (i: 1 start,
   0 cancel) */
typedef void (*PyGraphProc)(int id,int op,int i,double a,double b,double c,
    double d,char* text);
typedef void (*PyGraphTextProc)(int id,char* text,double* px,double* py);

static PyGraphProc pyGraph=NULL;
static PyGraphTextProc pyGraphText=NULL;

void SetPyGraphProcs(PyGraphProc graph,PyGraphTextProc text) {
  pyGraph=graph;
  pyGraphText=text;
}

static void Rec(GraphDlg dlg,int op,int i,double a,double b,double c,
    double d,char* text) {
  if (pyGraph!=NULL) pyGraph(dlg->id,op,i,a,b,c,d,text);
}

/* Forward declarations */

static void RepaintGraph(GView gv);
static void AddGraphDlgUpdate(GraphDlg dlg);
static void CancelGraphDlgUpdate(GraphDlg dlg);
static void DrawGraphLine(GView gv,GraphLine gl,int mode);
static void SetGraphArea(GraphDlg dlg,
    double minX,double minY,double maxX,double maxY);
static Group GetDrawnReactions(GraphDlg dlg);
static GraphLine AddGraphLine(GraphDlg dlg,Reaction r,double t1,double t2,
    double d,int dNumber);
static void* DelGraphLine(GraphLine gdl);
static GView CreateGraphDlgGView(GraphDlg dlg);
static int RecalcGViewLayout(GView gv);
static void DrawSymbol(struct _GView* gv,double sx,double sy,int type);
static GView CreatePsGView(GView gv0,double width,double height,double
    margin,int bBlackWhite);
static int PsGViewOutput(GView gv,char* fName,int fd,char* title);
static void GViewClipTo(GView gv,double x1,double y1,double x2,double y2);
static void GViewNoClip(GView gv);
static void DrawGViewLine(GView gv,double x1,double y1,double x2,double y2);

/* Repaint timer (the timer is on the Python side) */

static void AddGraphDlgUpdate(GraphDlg dlg) {
  Rec(dlg,'U',1,0,0,0,0,NULL);
}

static void CancelGraphDlgUpdate(GraphDlg dlg) {
  Rec(dlg,'U',0,0,0,0,0,NULL);
}

/* Repaint procedures (amgraph.c) */

static void DrawLegend(GView gv,int bDraw) {
  Group g;
  GraphLine gl;
  Reaction r;
  double tw,th,ty0;
  char s[255];
  Index ix;
  int i,j;

  if (!bDraw && !gv->bLegendOn) return;
  gv->bLegendOn=bDraw;

  g=GetDrawnReactions(gv->dlg);
  gv->GetTextExtent(gv,"X",&tw,&th);
  ty0=max(0,(gv->height-th*GD_DENSITIES)/2);

  /* Display densities */

  for (j=i=0;i<GD_DENSITIES;i++) {
    for (gl=Group1st(gv->dlg->lines,&ix);gl!=NULL;gl=Next(&ix))
      if (gl->dNumber==i) goto found;
    continue;

    found:

    gv->SetMode(gv,bDraw? VM1_GRAPHSYMS : VM0_GRAPHSYMS);
    DrawSymbol(gv,GLX2GV(gv,gv->glMaxX)+tw/2,
      ty0+th*j+th/2,i);

    sprintf(s,"%1.2E",gl->d);
    gv->SetMode(gv,bDraw? VM1_LEGENDTEXT:VM0_LEGENDTEXT);
    gv->DrawText(gv,GLX2GV(gv,gv->glMaxX)+tw,
	ty0+th*j,s,
	0/*DT_ORAQUE*/);
    j++;
  }

  /* Display reactions */

  for (i=0;i<GroupCount(g);i++) {
    r=GroupAt(g,i);
    gv->SetMode(gv,bDraw? VM1_GRAPHLINE+i%GLVMCOUNT : VM0_GRAPHLINE);
    gv->DrawText(gv,GLX2GV(gv,gv->glMinX),i*th,r->name,0);
  }

  FreeGroup(g);
}

static void RepaintGraph(GView gv) {
  GraphLine gl;
  Index ix;
  double f;
  char s[255];

  if (RecalcGViewLayout(gv)) gv->Clear(gv,False);

  for (f=ceil(gv->glMinX);f<gv->glMaxX;f+=1) {
    gv->SetMode(gv,VM_GRIDLINE);
    DrawGViewLine(gv,GLX2GV(gv,f),GLY2GV(gv,gv->glMinY),
	GLX2GV(gv,f),GLY2GV(gv,gv->glMaxY));
  }

  for (f=ceil(gv->glMinY);f<gv->glMaxY;f+=1) {
    gv->SetMode(gv,VM_GRIDLINE);
    DrawGViewLine(gv,GLX2GV(gv,gv->glMinX),GLY2GV(gv,f),
	GLX2GV(gv,gv->glMaxX),GLY2GV(gv,f));
  }

  gv->SetMode(gv,VM_BORDER);

  DrawGViewLine(gv,GLX2GV(gv,gv->glMinX),GLY2GV(gv,gv->glMinY),
      GLX2GV(gv,gv->glMinX),GLY2GV(gv,gv->glMaxY));
  DrawGViewLine(gv,GLX2GV(gv,gv->glMinX),GLY2GV(gv,gv->glMinY),
      GLX2GV(gv,gv->glMaxX),GLY2GV(gv,gv->glMinY));
  DrawGViewLine(gv,GLX2GV(gv,gv->glMaxX),GLY2GV(gv,gv->glMinY),
      GLX2GV(gv,gv->glMaxX),GLY2GV(gv,gv->glMaxY));
  DrawGViewLine(gv,GLX2GV(gv,gv->glMinX),GLY2GV(gv,gv->glMaxY),
      GLX2GV(gv,gv->glMaxX),GLY2GV(gv,gv->glMaxY));

  for (gl=Group1st(gv->dlg->lines,&ix);gl!=NULL;gl=Next(&ix))
    DrawGraphLine(gv,gl,True);

  for (f=floor(gv->glMinX+1);f<gv->glMaxX;f+=1) {
    sprintf(s,"E%g",f);
    gv->SetMode(gv,VM_GRIDTEXT);
    gv->DrawText(gv,GLX2GV(gv,f),GLY2GV(gv,gv->glMinY),s,
	DT_CENTERX/*|DT_ORAQUE*/);
  }

  for (f=floor(gv->glMinY+1);f<gv->glMaxY;f+=1) {
    sprintf(s,"E%g",f);
    gv->SetMode(gv,VM_GRIDTEXT);
    gv->DrawText(gv,GLX2GV(gv,gv->glMinX),GLY2GV(gv,f),s,
	DT_CENTERY|/*DT_ORAQUE|*/DT_LEFT);
  }

  DrawLegend(gv,True);
}

/* GraphLine */

static GraphLine AddGraphLine(GraphDlg dlg,Reaction r,double t1,double t2,
    double d,int dNumber) {
  GraphLine gdl;

  gdl=Malloc(sizeof(*gdl));
  gdl->dlg=dlg;
  gdl->r=r;
  gdl->t1=t1;
  gdl->t2=t2;
  gdl->d=d;
  gdl->dNumber=dNumber;
  gdl->rNumber=0;

  gdl->numPoints=0;
  gdl->xy=Malloc(sizeof(*gdl->xy)*(gdl->allocedPoints=1));

  DrawLegend(dlg->gv,False);
  GroupAdd(dlg->lines,gdl);
  AddGraphDlgUpdate(dlg);

  return gdl;
}

static void* DelGraphLine(GraphLine gl) {
  DrawGraphLine(gl->dlg->gv,gl,False);
  DrawLegend(gl->dlg->gv,False);
  AddGraphDlgUpdate(gl->dlg);

  GroupDel(gl->dlg->lines,gl);

  Free(gl->xy);
  Free(gl);

  return NULL;
}

int ReadGraphDlgLines(Group lines,FILE* f) {
  GraphLine gl;
  Index ix;
  char s[256];
  double x,y;

  while (1) {
    if (fgets(s,sizeof(s)-1,f)==NULL) return -1;
    if (!strcasecmp(s,"# start of data\n")) goto found;
  }
  return -1;

  found:

  while (1) {
    if (fscanf(f,"%lf",&x)!=1) break;
    for (gl=Group1st(lines,&ix);gl!=NULL;gl=Next(&ix)) {
      if (fscanf(f,"%lf",&y)!=1) break;

      gl->xy[gl->numPoints].x=log10(x);
      gl->xy[gl->numPoints].y=log10(y);
      
      if (++gl->numPoints>=gl->allocedPoints)
	gl->xy=Realloc(gl->xy,sizeof(*gl->xy)*
	    (gl->allocedPoints+=GDL_ALLOCINCR));
    }
  }

  for (gl=Group1st(lines,&ix);gl!=NULL;gl=Next(&ix))
    DrawGraphLine(gl->dlg->gv,gl,True);

  return 0;
}

static void DrawGraphLine(GView gv,GraphLine gl,int mode) {
  Pixel pix;
  int i,n;

  GViewClipTo(gv,GLX2GV(gv,gv->glMinX),GLY2GV(gv,gv->glMinY),
      GLX2GV(gv,gv->glMaxX),GLY2GV(gv,gv->glMaxY));

  gv->SetMode(gv,mode? VM1_GRAPHLINE+gl->rNumber%GLVMCOUNT
      : VM0_GRAPHLINE);

  for (i=0;i<gl->numPoints-1;i++)
    DrawGViewLine(gv,GLX2GV(gv,gl->xy[i].x),GLY2GV(gv,gl->xy[i].y),
	GLX2GV(gv,gl->xy[i+1].x),GLY2GV(gv,gl->xy[i+1].y));

  n=gl->numPoints/SYMS_PER_LINE+1;

  gv->SetMode(gv,mode? VM1_GRAPHSYMS : VM0_GRAPHSYMS);

  for (i=0;i<gl->numPoints;i++) if (i%n==n/2)
    DrawSymbol(gv,GLX2GV(gv,gl->xy[i].x),GLY2GV(gv,gl->xy[i].y),
	gl->dNumber);

  GViewNoClip(gv);
}

static Group GetDrawnReactions(GraphDlg dlg) {
  Group g;
  GraphLine gl;
  Index ix;

  g=CreateGroup();
  for (gl=Group1st(dlg->lines,&ix);gl!=NULL;gl=Next(&ix))
    if (!InGroup(g,gl->r)) GroupAdd(g,gl->r);

  return g;
}

static void SetGraphArea(GraphDlg dlg,
    double minX,double minY,double maxX,double maxY) {

  if (minX==dlg->gv->glMinX && minY==dlg->gv->glMinY &&
      maxX==dlg->gv->glMaxX && maxY==dlg->gv->glMaxY) return;
  if (minX==maxX) return;
  if (minY==maxY) return;

  dlg->gv->glMinX=minX;
  dlg->gv->glMinY=minY;
  dlg->gv->glMaxX=maxX;
  dlg->gv->glMaxY=maxY;

  if (!dlg->realized) return;

  dlg->gv->Clear(dlg->gv,True);
}

/* The screen view: its calls as records for Python */

static void* PYG_Free(struct _GView* w) {
  Free(w);

  return NULL;
}

static void PYG_SetMode(struct _GView* w,int mode) {
  Rec((GraphDlg)w->x,'M',mode,0,0,0,0,NULL);
}

static void PYG_DrawLine(struct _GView* w,double x1,double y1,
    double x2,double y2) {
  Rec((GraphDlg)w->x,'L',0,x1,y1,x2,y2,NULL);
}

static void PYG_DrawText(struct _GView* w,double x,double y,
    char* text,int flags) {
  Rec((GraphDlg)w->x,'T',flags,x,y,0,0,text);
}

/* The extent of a text in the label font of the dialog; 1 x 1 without a
   window, as GDV_GetTextExtent */
static void PYG_GetTextExtent(GView w,char* text,double* px,double* py) {
  GraphDlg dlg=(GraphDlg)w->x;
  double dx=1,dy=1;

  if (dlg->realized && pyGraphText!=NULL) pyGraphText(dlg->id,text,&dx,&dy);
  Rec(dlg,'E',0,dx,dy,0,0,text);

  if (px!=NULL) *px=dx;
  if (py!=NULL) *py=dy;
}

static void PYG_Clear(struct _GView* gv,int bExpose) {
  Rec((GraphDlg)gv->x,'C',bExpose,0,0,0,0,NULL);
}

static GView CreateGraphDlgGView(GraphDlg dlg) {
  GView gv;

  gv=Malloc(sizeof(*gv));
  gv->dlg=dlg;

  gv->x=(void*)dlg;
  gv->Free=PYG_Free;
  gv->SetMode=PYG_SetMode;
  gv->DrawLine=PYG_DrawLine;
  gv->DrawText=PYG_DrawText;
  gv->GetTextExtent=PYG_GetTextExtent;
  gv->Clear=PYG_Clear;

  gv->width=gv->height=1;
  gv->symSize=SYMSIZE_X;
  GViewNoClip(gv);

  gv->glMinX=gv->glMinY=gv->glMaxX=gv->glMaxY=0;
  gv->bLegendOn=0;

  gv->font=(Font)NULL;

  RecalcGViewLayout(gv);

  return gv;
}

#define GVL_HASH(a,b,c,d,e,f,g,h,i,j) \
(445*a+8450*b+4251*c+8126*d+383*e+849*f+3478*g+11787*h+11727*i+414*j)

static int RecalcGViewLayout(GView gv) { /* Returns 1 if layout changed */
  double w,h,h1,h2;
  GraphLine gl;
  Group g;
  Index ix;

  g=GetDrawnReactions(gv->dlg);
  h1=GVL_HASH(gv->width,gv->height,gv->glLOff,gv->glROff,
      gv->glTOff,gv->glBOff,gv->glMinX,gv->glMinY,gv->glMaxX,gv->glMaxY);

  /* Recalculate colors of GraphLines */

  for (gl=Group1st(gv->dlg->lines,&ix);gl!=NULL;gl=Next(&ix)) {
    gl->rNumber=GroupIndex(g,gl->r);
  }

  /* Recalculate margins etc */

  gv->glTOff=gv->glBOff=gv->glLOff=gv->glROff=0;

  gv->GetTextExtent(gv,TEX_TOP,NULL,&gv->glTOff);
  gv->glTOff*=(0.5+GroupCount(g));

  gv->GetTextExtent(gv,TEX_LEFT,&gv->glLOff,NULL);
  gv->GetTextExtent(gv,TEX_BOTTOM,NULL,&gv->glBOff);
  if (!IsEmptyGroup(g)) gv->GetTextExtent(gv,TEX_RIGHT,&gv->glROff,NULL);

  gv->glW=gv->width-gv->glLOff-gv->glROff;
  gv->glH=gv->height-gv->glTOff-gv->glBOff;

  /* Clean-up */

  g=FreeGroup(g);
  h2=GVL_HASH(gv->width,gv->height,gv->glLOff,gv->glROff,
      gv->glTOff,gv->glBOff,gv->glMinX,gv->glMinY,gv->glMaxX,gv->glMaxY);

  return h1!=h2;
}

/* PostScript */

static int PsGViewOutput(GView gv,char* fName,int fd,char* title) {
  PsGViewExt x=(PsGViewExt)gv->x;

  assert(x->f==NULL);

  if (fName!=NULL) x->f=fopen(fName,"w");
  else x->f=fdopen(fd,"w");

  if (x->f==NULL) return -1;

  fprintf(x->f,
    "%%!PS-Adobe-3.0\n"
    "%%%%BoundingBox: %g %g %g %g\n"
    "%%%%Creator: amds version %g\n"
    "%%%%Pages: %d\n"
    "%%%%EndComments\n",
    x->orgMargin,x->orgMargin,
    x->orgMargin+gv->width,x->orgMargin+gv->height,
    AMDS_VERSION/100.0,
    1
  );

  fprintf(x->f,
    "%%%%Page: %d %d\n"
    "%%%%BeginPageSetup\n"
    "1 setlinecap\n"
    "%g %g translate\n"
    /*"1 -1 scale\n" */
    "%g %g moveto\n"
    "%g %g lineto\n"
    "%g %g lineto\n"
    "%g %g lineto\n"
    "closepath\n"
/*    "0.8 setgray\n"
    "fill\n"
    "0 setgray\n" */
    "clip\n"
    "newpath\n"

    "%%%%EndPageSetup\n",
    1,1,
    (double)x->orgMargin/*+gv->width*/,
    (double)x->orgMargin/*+gv->height*/,
    0.0,0.0,
    0.0,gv->height,
    gv->width,gv->height,
    gv->width,0.0
  );
/*
  fprintf(w->x->f,
    "0 setgray\n"
    "4 setlinewidth\n"
    "%g %g moveto\n"
    "%g %g lineto\n"
    "%g %g lineto\n"
    "%g %g lineto\n"
    "%g %g lineto\n"
    "%g %g moveto\n"
    "stroke\n"
    "1 setgray\n"
    "/Times-Roman findfont\n"
    "4 scalefont\n"
    "setfont\n"
    "(  XDivGeo  ) show\n"
    "stroke\n",
    (float)w->width,(float)0,
    (float)w->width,(float)w->height,
    (float)0,(float)w->height,
    (float)0,(float)0,
    (float)w->width,(float)0,
    (float)0,(float)0
  );
*/
  RepaintGraph(gv);

  fprintf(x->f,
    "showpage\n"
  );

  fprintf(x->f,
    "%%%%EOF\n"
  );

  fclose(x->f);

  x->f=NULL;

  return 0;
}

static void* PSV_Free(GView gv) {
  PsGViewExt x=(PsGViewExt)gv->x;

  assert(x->f==NULL);
  Free(gv->x);
  Free(gv);

  return NULL;
}

static void ApplyPsGViewMode(GView gv) {
  PsGViewExt x=(PsGViewExt)gv->x;

  assert(x->f!=NULL);

  fprintf(x->f,
/*    "0 setgray\n" */
    "%g %g %g setrgbcolor\n"
    "%g setlinewidth\n",
    x->r,x->g,x->b,
    x->lw
  );
}

static void PSV_Clear(GView gv,int bExpose) {
/*  assert(0); */
}

static void PSV_DrawLine(GView gv,double x1,double y1,double x2,double y2) {
  PsGViewExt x=(PsGViewExt)gv->x;

  assert(x->f!=NULL);

  ApplyPsGViewMode(gv);
  fprintf(x->f,
    "%g %g moveto\n"
    "%g %g lineto\n"
    "stroke\n"
  ,x1,gv->height-y1,x2,gv->height-y2);
}

static void PSV_DrawText(GView gv,double x1,double y1,char* text,int flags){
  PsGViewExt x=(PsGViewExt)gv->x;
  double m1,m2;

  assert(x->f!=NULL);

  if (flags & DT_LEFT) m1=-1;else
  if (flags & DT_CENTERX) m1=-0.5;else
  m1=0;

  if (flags & DT_ABOVE) m2=0;else
  if (flags & DT_CENTERY) m2=-0.5;else
  m2=-1;

  ApplyPsGViewMode(gv);

  fprintf(x->f,
    "/Times-Roman findfont\n"
    "12 scalefont\n"
    "setfont\n"
    "%g %g moveto\n"
    "(%s) dup stringwidth pop 12\n"
    "%g mul exch\n"
    "%g mul exch\n"
    "rmoveto\n"
    "show\n",
    x1,gv->height-y1,text,
    m2,m1
  );
}

static void PSV_GetTextExtent(GView gv,char* text,double* pw,double* ph) {
  if (pw!=NULL) *pw=10*strlen(text);
  if (ph!=NULL) *ph=12;
}

static void PSV_SetMode(GView gv,int mode) {
  PsGViewExt x=(PsGViewExt)gv->x;

  switch(mode) {
    case VM1_GRAPHLINE:
      x->r=0.0;x->g=0.0;x->b=0.0;x->lw=0.2;break;
    case VM2_GRAPHLINE:
      x->r=1.0;x->g=0.0;x->b=0.0;x->lw=0.2;
      if (x->bBW) x->r=x->g=x->b=0.0;break;
    case VM3_GRAPHLINE:
      x->r=0.0;x->g=1.0;x->b=0.0;x->lw=0.2;
      if (x->bBW) x->r=x->g=x->b=0.0;break;
    case VM4_GRAPHLINE:
      x->r=0.4;x->g=0.4;x->b=1.0;x->lw=0.2;
      if (x->bBW) x->r=x->g=x->b=0.0; break;
    case VM_GRIDLINE:
      x->r=0.5;x->g=0.5;x->b=0.5;x->lw=0.0;break;
    case VM_GRIDTEXT:
      x->r=0.0;x->g=0.0;x->b=0.0;x->lw=0.0;break;
    case VM1_LEGENDTEXT:
      x->r=0.0;x->g=0.0;x->b=0.0;x->lw=0.0;break;
    case VM1_GRAPHSYMS:
      x->r=0.0;x->g=0.0;x->b=0.0;x->lw=0.4;break;
    case VM_BORDER:
      x->r=0.0;x->g=0.0;x->b=0.0;x->lw=0.5;break;
    default: assert(0);break;
  }
}

static GView CreatePsGView(GView gv0,double width,double height,
    double margin,int bBW) {
  GView gv;
  PsGViewExt x;

  if (width-2*margin<=0 || height-2*margin<=0) return NULL;

  gv=Malloc(sizeof(*gv));
  gv->dlg=gv0->dlg;

  gv->glMinX=gv0->glMinX;
  gv->glMinY=gv0->glMinY;
  gv->glMaxX=gv0->glMaxX;
  gv->glMaxY=gv0->glMaxY;
  gv->glW=gv->glH=-1;

  gv->Free=PSV_Free;
  gv->SetMode=PSV_SetMode;
  gv->DrawLine=PSV_DrawLine;
  gv->DrawText=PSV_DrawText;
  gv->GetTextExtent=PSV_GetTextExtent;
  gv->Clear=PSV_Clear;

  gv->x=x=Malloc(sizeof(*x));

  x->f=NULL;
  x->orgWidth=width;
  x->orgHeight=height;
  x->orgMargin=margin;
  x->bBW=bBW;

  gv->width=x->orgWidth-2*x->orgMargin;
  gv->height=x->orgHeight-2*x->orgMargin;

  gv->symSize=2;
  GViewNoClip(gv);

  return gv;
}

#define DL(a,b,c,d) DrawGViewLine(gv,a,b,c,d)
#define SYMDX gv->symSize
#define SYMDY gv->symSize

static void DrawSymbol(struct _GView* gv,double sx,double sy,int type) {

  switch (type) {
    case 0:             /* Triangle pointing up */
      DL(sx-SYMDX,sy+SYMDY,sx,sy-SYMDY);
      DL(sx,sy-SYMDY,sx+SYMDX,sy+SYMDY);
      DL(sx+SYMDX,sy+SYMDY,sx-SYMDX,sy+SYMDY);
      break;
    case 1:             /* Square */
      DL(sx-SYMDX,sy-SYMDY,sx-SYMDX,sy+SYMDY);
      DL(sx-SYMDX,sy+SYMDY,sx+SYMDX,sy+SYMDY);
      DL(sx+SYMDX,sy+SYMDY,sx+SYMDX,sy-SYMDY);
      DL(sx+SYMDX,sy-SYMDY,sx-SYMDX,sy-SYMDY);
      break;
    case 2:             /* Rhombus */
      DL(sx,sy-SYMDY,sx-SYMDX,sy);
      DL(sx-SYMDX,sy,sx,sy+SYMDY);
      DL(sx,sy+SYMDY,sx+SYMDX,sy);
      DL(sx+SYMDX,sy,sx,sy-SYMDY);
      break;
    case 3:             /* Triangle pointing down */
      DL(sx-SYMDX,sy-SYMDY,sx,sy+SYMDY);
      DL(sx,sy+SYMDY,sx+SYMDX,sy-SYMDY);
      DL(sx+SYMDX,sy-SYMDY,sx-SYMDX,sy-SYMDY);
      break;
    case 4:             /* X */
      DL(sx-SYMDX,sy-SYMDY,sx+SYMDX,sy+SYMDY);
      DL(sx+SYMDX,sy-SYMDY,sx-SYMDX,sy+SYMDY);
      break;
    case 5:             /* + */
      DL(sx,sy-SYMDY,sx,sy+SYMDY);
      DL(sx-SYMDX,sy,sx+SYMDX,sy);
      break;
    case 6:
      DL(sx+SYMDX,sy-SYMDY,sx-SYMDX,sy-SYMDY);
      DL(sx-SYMDX,sy-SYMDY,sx+SYMDX,sy+SYMDY);
      DL(sx+SYMDX,sy+SYMDY,sx-SYMDX,sy+SYMDY);
      break;
    case 7:
      DL(sx-SYMDX,sy+SYMDY,sx-SYMDX,sy-SYMDY);
      DL(sx-SYMDX,sy-SYMDY,sx+SYMDX,sy+SYMDY);
      DL(sx+SYMDX,sy+SYMDY,sx+SYMDX,sy-SYMDY);
      break;
    case 8:
      DL(sx+SYMDX,sy-SYMDY,sx-SYMDX,sy-SYMDY);
      DL(sx,sy-SYMDY,sx,sy+SYMDY);
      DL(sx+SYMDX,sy+SYMDY,sx-SYMDX,sy+SYMDY);
      break;
    case 9:
      DL(sx+SYMDX,sy+SYMDY,sx+SYMDX,sy-SYMDY);
      DL(sx-SYMDX,sy,sx+SYMDX,sy);
      DL(sx-SYMDX,sy+SYMDY,sx-SYMDX,sy-SYMDY);
      break;
    default:assert(0);break;
  }
}
#undef DL
#undef SYMDX
#undef SYMDY


static void GViewClipTo(GView gv,double x1,double y1,double x2,double y2) {
  if (x1>x2) swap(x1,x2);
  if (y1>y2) swap(y1,y2);

  gv->clipX1=x1;
  gv->clipY1=y1;
  gv->clipX2=x2;
  gv->clipY2=y2;
}

static void GViewNoClip(GView gv) {
  GViewClipTo(gv,-MAXDOUBLE,-MAXDOUBLE,MAXDOUBLE,MAXDOUBLE);
}

static void DrawGViewLine(GView gv,double x1,double y1,double x2,double y2){
  if (x1<gv->clipX1 && x2>gv->clipX1)
    y1+=(y2-y1)*(gv->clipX1-x1)/(x2-x1),x1=gv->clipX1; else
  if (x2<gv->clipX1 && x1>gv->clipX1)
    y2+=(y1-y2)*(gv->clipX1-x2)/(x1-x2),x2=gv->clipX1;
  if (x1>gv->clipX2 && x2<gv->clipX2)
    y1+=(y2-y1)*(gv->clipX2-x1)/(x2-x1),x1=gv->clipX2; else
  if (x2>gv->clipX2 && x1<gv->clipX2)
    y2+=(y1-y2)*(gv->clipX2-x2)/(x1-x2),x2=gv->clipX2;

  if (y1<gv->clipY1 && y2>gv->clipY1)
    x1+=(x2-x1)*(gv->clipY1-y1)/(y2-y1),y1=gv->clipY1; else
  if (y2<gv->clipY1 && y1>gv->clipY1)
    x2+=(x1-x2)*(gv->clipY1-y2)/(y1-y2),y2=gv->clipY1;
  if (y1>gv->clipY2 && y2<gv->clipY2)
    x1+=(x2-x1)*(gv->clipY2-y1)/(y2-y1),y1=gv->clipY2; else
  if (y2>gv->clipY2 && y1<gv->clipY2)
    x2+=(x1-x2)*(gv->clipY2-y2)/(y1-y2),y2=gv->clipY2;

  if (x1<gv->clipX1 && x2<gv->clipX1) return;
  if (y1<gv->clipY1 && y2<gv->clipY1) return;
  if (x1>gv->clipX2 && x2>gv->clipX2) return;
  if (y1>gv->clipY2 && y2>gv->clipY2) return;

  gv->DrawLine(gv,x1,y1,x2,y2);
}

/* The dialog: the core part of the callbacks of amgraph.c *************/

/* CreateGraphDlg, the graph part */
GraphDlg PyCreateGraph(View w,int id) {
  GraphDlg dlg;

  dlg=Malloc(sizeof(*dlg));
  memset(dlg,0,sizeof(*dlg));
  dlg->w=w;
  dlg->id=id;
  dlg->lines=CreateGroup();
  dlg->gv=CreateGraphDlgGView(dlg);
  dlg->calcReaction=NULL;
  return dlg;
}

/* The drawing area got its window */
void PyGraphRealize(GraphDlg dlg) {
  dlg->realized=1;
}

/* CbGraphDlgResize (resize, and the dialog mapped) */
void PyGraphResize(GraphDlg dlg,int width,int height) {
  dlg->gv->width=width;
  dlg->gv->height=height;

  if (!dlg->realized) return;

  dlg->gv->Clear(dlg->gv,True);
}

/* CbGraphDlgExpose */
void PyGraphExpose(GraphDlg dlg) {
  CancelGraphDlgUpdate(dlg);
  RepaintGraph(dlg->gv);
}

/* ToRepaintGraphDlg when no calculation runs */
void PyGraphRepaint(GraphDlg dlg) {
  RepaintGraph(dlg->gv);
}

/* UpdateGraphDlg, a calculation just ended: the curves of its reaction
   from the output of the program (file name) */
void PyGraphCalcDone(GraphDlg dlg,char* fileName) {
  GraphLine gl;
  Group g;
  Index ix;
  int i;
  FILE* f;

  f=fopen(fileName,"r");
  if (f==NULL) return;

  for (gl=Group1st(dlg->lines,&ix);gl!=NULL;gl=Next(&ix))
    if (gl->r==dlg->calcReaction) DelGraphLine(gl);

  g=CreateGroup();
  for (i=0;i<GD_DENSITIES;i++) if (dlg->vDensity[i]!=V_NONE) GroupAdd(g,
    AddGraphLine(dlg,dlg->calcReaction,
    dlg->vT1,dlg->vT2,dlg->vDensity[i],i));

  ReadGraphDlgLines(g,f);
  FreeGroup(g);

  fclose(f);
  dlg->calcReaction=NULL;
}

/* UpdateGraphDlg after the fields are read (Python: strtod as
   GetXmTextDouble) and the selection is known: the area, the curves not
   wanted any more, then the first reaction to calculate (NULL: none) */
Reaction PyGraphUpdate(GraphDlg dlg,double vT1,double vT2,double vY1,
    double vY2,double* vDensity,Group g) {
  GraphLine gl;
  Reaction r;
  Index ix,ixr;
  int i;

  dlg->vT1=vT1;
  dlg->vT2=vT2;
  dlg->vY1=vY1;
  dlg->vY2=vY2;

  for (i=0;i<GD_DENSITIES;i++)
    dlg->vDensity[i]=vDensity[i];

  /* Change area displayed if needed */

  if (dlg->vT1!=V_NONE && dlg->vT1>0 && dlg->vT2!=V_NONE && dlg->vT2>0 &&
      dlg->vY1!=V_NONE && dlg->vY1>0 && dlg->vY2!=V_NONE && dlg->vY2>0)
    SetGraphArea(dlg,log10(dlg->vT1),log10(dlg->vY1),
        log10(dlg->vT2),log10(dlg->vY2));

  /* Remove unneeded GraphLines */

  for (gl=Group1st(dlg->lines,&ix);gl!=NULL;gl=Next(&ix)) {
    if (!InGroup(g,gl->r) || gl->t1!=dlg->vT1 || gl->t2!=dlg->vT2 ||
        gl->d!=dlg->vDensity[gl->dNumber]) DelGraphLine(gl);
  }

  if (dlg->vT1==V_NONE || dlg->vT2==V_NONE) return NULL;

  /* Look for needed but not present GraphLines */

  for (r=Group1st(g,&ixr);r!=NULL;r=Next(&ixr)) {
    for (i=0;i<GD_DENSITIES;i++) if (dlg->vDensity[i]!=V_NONE) {
      for (gl=Group1st(dlg->lines,&ix);gl!=NULL;gl=Next(&ix)) {
        if (dlg->vT1==gl->t1 && dlg->vT2==gl->t2 &&
            dlg->vDensity[i]==gl->d && r==gl->r) goto Found;
      }
      goto CalculateIt;
      Found:;
    }
  }

  return NULL; /* Everything needed is present */

  CalculateIt:

  dlg->calcReaction=r;
  return r;
}

/* CbFit: the vertical range of the curves as the texts of Y1 and Y2 */
void PyGraphFit(GraphDlg dlg,char* s1,char* s2) {
  GraphLine gl;
  Index ix;
  int i;
  double y1=MAXDOUBLE,y2=-MAXDOUBLE;

  for (gl=Group1st(dlg->lines,&ix);gl!=NULL;gl=Next(&ix)) {
    for (i=0;i<gl->numPoints;i++) {
      y1=min(y1,gl->xy[i].y);
      y2=max(y2,gl->xy[i].y);
    }
  }

  if (y1>y2) {y1=-20;y2=-10;}
  if (y1==y2) {y1-=1;y2+=1;}

  y1=pow(10,y1);
  y2=pow(10,y2);

  sprintf(s1,"%1.2e",y1);
  sprintf(s2,"%1.2e",y2);
}

/* CbPrintOk: the PostScript view (NULL: invalid size), its output to a
   file or to an open descriptor (closed), its end */
GView PyGraphPsCreate(GraphDlg dlg,double width,double height,
    double margin,int bBW) {
  return CreatePsGView(dlg->gv,width*72,height*72,margin*72,bBW);
}

int PyGraphPsOutput(GView psGV,char* fName,int fd) {
  return PsGViewOutput(psGV,fName,fd,NULL);
}

void PyGraphPsFree(GView psGV) {
  psGV->Free(psGV);
}

/* CbGraphDlgDestroy, the graph part */
void PyGraphFree(GraphDlg dlg) {
  GraphLine gl;
  Index ix;

  for (gl=Group1st(dlg->lines,&ix);gl!=NULL;gl=Next(&ix))
    DelGraphLine(gl);

  FreeGroup(dlg->lines);

  dlg->gv->Free(dlg->gv);

  Free(dlg);
}
