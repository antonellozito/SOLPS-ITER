/* Menu commands of the Python interface: the core part of the callbacks
   of the Motif front end (ammenu.c, amview.c), in the same order of core
   calls. Python passes the list positions and the menu entries chosen. */

#include "py_amds.h"

/* The reactions of the selected list positions (GetSelectedReactions;
   positions from 1, in increasing order) */
Group PyGetSelectedReactions(View w,int* positionList,int positionCount) {
  Group g;
  Reaction r;
  int i,j,k;

  g=CreateGroup();

  for (i=j=k=0;i<w->subset->reactionCount;i++) {
    if (ReactionActive(w->subset,r=w->subset->data[i].r)) {
      j++;
      if (k<positionCount && j==positionList[k]) {GroupAdd(g,r);k++;}
    }
  }

  return g;
}

/* The items of the reaction list (UpdateViewList), one call each */
void PyViewListItems(View w,PyItemProc proc) {
  int i,j,l0;
  Reaction r;
  Particle p;
  Index ix,ix1;
  char s[2000],s1[100];

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix))
      if (ReactionActive(w->subset,r)) {

    *s=0;

    sprintf(s,"%-*s %-*s %-*s : ",
      w->rdWidth,GetReactionDatabase(r),
      w->rsWidth,GetReactionSection(r),
      w->rnWidth,GetReactionNumber(r));

    l0=strlen(s);

    for (j=0,p=Group1st(w->bGroupParticles? r->inputSet : r->input,&ix1);
        p!=NULL;p=Next(&ix1)) {
      if (j++) strcat(s," + ");

      if (w->bGroupParticles) {
        i=InGroupCount(r->input,p);
        if (i>1) {
          sprintf(s1,"%d",i);
          strcat(s,s1);
        }
      }

      if (!InGroup(w->subset->data[r->number].enabled,p)) {
        strcat(s,"[");
        strcat(s,p->name);
        strcat(s,"]");
      } else
        strcat(s,p->name);
    }

    for (l0=strlen(s)-l0;l0<w->riWidth;l0++) strcat(s," ");

    strcat(s," -> ");

    for (j=0,p=Group1st(w->bGroupParticles? r->outputSet : r->output,&ix1);
        p!=NULL;p=Next(&ix1)) {
      if (j++) strcat(s," + ");

      if (w->bGroupParticles) {
        i=InGroupCount(r->output,p);
        if (i>1) {
          sprintf(s1,"%d",i);
          strcat(s,s1);
        }
      }

      strcat(s,p->name);
    }
    proc(s);
  }
}

/* Sensitivity of an entry of the Restrict particle menus when they open
   (CascadeParticleMenu); bSubclass: the * entry or a cascade */
int PyParticleEntrySensitive(View w,Particle p,int bShown,int bInput,
    int bSubclass) {
  int i;

  for (i=0;i<w->subset->reactionCount;i++)
    if (!!(ReactionActive(w->subset,w->subset->data[i].r))==!!bShown
        && ParticleInReaction(p,w->subset->data[i].r,bInput,bSubclass))
      return True;
  return False;
}

/* The same for Exclude particle (CbCascadeForbidParticle) */
int PyForbidEntrySensitive(View w,Particle p,int bSubclass) {
  Reaction r;
  int i;

  for (i=0;i<w->subset->reactionCount;i++) {
    if (!ReactionActive(w->subset,w->subset->data[i].r)) continue;
    r=w->subset->data[i].r;
    if (ParticleInReaction(p,r,True,bSubclass) ||
        ParticleInReaction(p,r,False,bSubclass)) return True;
  }
  return False;
}

/* The same for By reaction type (CbCascadeRestrictType) */
int PyTypeEntrySensitive(View w,ReactionType rt) {
  int i;

  for (i=0;i<w->subset->reactionCount;i++)
    if (ReactionActive(w->subset,w->subset->data[i].r) &&
        InGroup(w->subset->data[i].r->types,rt)) return True;
  return False;
}

/* Restrict menus (ammenu.c) ******************************************/

void PyCbRestrictInput(View w,Particle p,int bSubclass) {
  Reaction r;
  Index ix;

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix))
    if (!ParticleInReaction(p,r,True,bSubclass)) {
      ActivateReaction(w->subset,r,NULL,False);
    };

  UndoMark(w->subset);
}

void PyCbRestrictOutput(View w,Particle p,int bSubclass) {
  Reaction r;
  Index ix;

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix))
    if (!ParticleInReaction(p,r,False,bSubclass)) {
      ActivateReaction(w->subset,r,NULL,False);
    }

  UndoMark(w->subset);
}

void PyCbForbidParticle(View w,Particle p,int bSubclass) {
  Reaction r;
  Index ix;

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix))
    if (ParticleInReaction(p,r,False,bSubclass) ||
        ParticleInReaction(p,r,True,bSubclass)) {
      ActivateReaction(w->subset,r,NULL,False);
    }

  UndoMark(w->subset);
}

void PyCbRestrictType(View w,ReactionType rt) {
  Reaction r;
  Index ix;

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix))
    if (!InGroup(r->types,rt))
      ActivateReaction(w->subset,r,NULL,False);

  UndoMark(w->subset);
}

/* Edit menu (ammenu.c) ***********************************************/

void PyCbEditRedoAll(View w) {
  while (!IsEmptyGroup(w->subset->redoStack)) Redo(w->subset);
}

void PyCbActivate(View w,int* positionList,int positionCount) {
  Group g;
  Reaction r;
  Index ix;

  assert(w->mainView!=NULL);

  g=PyGetSelectedReactions(w,positionList,positionCount);

  for (r=Group1st(g,&ix);r!=NULL;r=Next(&ix))
    CopyReaction(w->subset,w->mainView->subset,r,True);
  FreeGroup(g);

  UndoMark(w->mainView->subset);
}

void PyCbDeactivate(View w,int* positionList,int positionCount) {
  Group g;
  Reaction r;
  Index ix;

  assert(w->mainView!=NULL);

  g=PyGetSelectedReactions(w,positionList,positionCount);

  for (r=Group1st(g,&ix);r!=NULL;r=Next(&ix))
    ActivateReaction(w->mainView->subset,r,NULL,False);
  FreeGroup(g);

  UndoMark(w->mainView->subset);
}

void PyCbCut(View w,int* positionList,int positionCount) {
  Group g;
  Reaction r;
  Index ix;

  ClearDoc(w->xapp->clipboard);

  g=PyGetSelectedReactions(w,positionList,positionCount);

  for (r=Group1st(g,&ix);r!=NULL;r=Next(&ix)) {
    CopyReaction(w->subset,w->xapp->clipboard,r,True);
    ActivateReaction(w->subset,r,NULL,False);
  }
  FreeGroup(g);

  UndoMark(w->subset);
  UndoMark(w->xapp->clipboard);
}

void PyCbCopy(View w,int* positionList,int positionCount) {
  Group g;
  Reaction r;
  Index ix;

  ClearDoc(w->xapp->clipboard);

  g=PyGetSelectedReactions(w,positionList,positionCount);

  for (r=Group1st(g,&ix);r!=NULL;r=Next(&ix))
    CopyReaction(w->subset,w->xapp->clipboard,r,True);

  FreeGroup(g);

  UndoMark(w->xapp->clipboard);
}

void PyCbCrop(View w,int* positionList,int positionCount) {
  Group g;
  Reaction r;
  Index ix;

  ClearDoc(w->xapp->clipboard);

  g=PyGetSelectedReactions(w,positionList,positionCount);

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix))
      if (!InGroup(g,r)) {
    CopyReaction(w->subset,w->xapp->clipboard,r,True);
    ActivateReaction(w->subset,r,NULL,False);
  }
  FreeGroup(g);

  UndoMark(w->subset);
  UndoMark(w->xapp->clipboard);
}

void PyCbPasteOr(View w) {
  Reaction r;
  Index ix;

  for (r=Group1st(w->db->reactions,&ix);r!=NULL;r=Next(&ix)) {
    if (ReactionActive(w->xapp->clipboard,r))
      CopyReaction(w->xapp->clipboard,w->subset,r,True);
  }

  UndoMark(w->subset);
}

/* Documents of new and cloned subsets (CbNewView, CbCloneView before
   CreateView) */
Doc PyNewSubsetDoc(View w0) {
  Doc ss;
  Reaction r;
  Index ix;

  ss=CreateDoc(w0->db);
  CopyDoc(w0->subset,ss);
  for (r=Group1st(w0->db->reactions,&ix);r!=NULL;r=Next(&ix))
    ActivateReaction(ss,r,NULL,True);
  return ss;
}

Doc PyCloneSubsetDoc(View w0) {
  Doc ss;

  ss=CreateDoc(w0->db);
  CopyDoc(w0->subset,ss);
  return ss;
}

/* The document of a new main view (NewView before CreateView) */
Doc PyNewViewDoc(XApp xap) {
  Doc d;

  d=CreateDoc(xap->db);
  if (xap->config!=NULL) LoadDoc(d,xap->config->fileName);
  SetDocFilename(d,"");
  d->alt=0;
  FreeUndoInfo(d);
  return d;
}

/* Quit (CbFileQuit): every view closed in the order of the views */
void PyCbFileQuit(View w) {
  Index ix;

  for (w=Group1st(w->xapp->views,&ix);w!=NULL;w=Next(&ix))
    PyCloseView(w,w->mainView==NULL);
}

/* Go to (amview.c) ***************************************************/

/* AltReactionName: database, section and number with a space after each
   dot of the number */
char* PyAltReactionName(Reaction r) {
  static char s[256];
  char* s1,*s2;

  strcpy(s,GetReactionDatabase(r));
  strcat(s," ");
  strcat(s,GetReactionSection(r));
  strcat(s," ");
  for (s1=GetReactionNumber(r),s2=s+strlen(s);*s1;)
    if ((*s2++=*s1++)=='.') *s2++=' ';
  *s2++=' ';
  *s2++=0;

  return s;
}

/* The list position (from 0) of a reaction chosen in Go to, -1 if it is
   not active (CbGoto) */
int PyGotoIndex(View w,Reaction r) {
  Group g;
  int i;

  g=GetActiveReactions(w->subset);
  if (!InGroup(g,r)) i=-1; else
  i=GroupIndex(g,r);
  FreeGroup(g);
  return i;
}
