#  VERSION : 07.12.2000 22:14

TARGET=$(OBJDIR)/amds
RES2FBR=$(OBJDIR)/res2fbr
CALC=$(OBJDIR)/calc_atomic_data
VPATH=src

ifndef HOST_NAME
  $(error HOST_NAME not defined)
endif
ifndef COMPILER
  $(error COMPILER not defined)
endif

MAKES = Makefile 
# Include global SOLPS compiler settings
ifndef SOLPS_CPP
  ifeq ($(shell [ -e ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER} ] && echo yes || echo no ),yes)
    include ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER}
    MAKES += ${SOLPSTOP}/SETUP/setup.csh.${HOST_NAME}.${COMPILER} ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER}
  else
    $(warning ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER} not found.)
  endif
  ifeq ($(shell [ -e ${SOLPSTOP}/SETUP/config.common.${COMPILER} ] && echo yes || echo no ),yes)
    include ${SOLPSTOP}/SETUP/config.common.${COMPILER}
    MAKES += ${SOLPSTOP}/SETUP/config.common.${COMPILER}
  endif
else
  MAKES += ${SOLPSTOP}/Makefile ${SOLPSTOP}/SETUP/setup.csh.${HOST_NAME}.${COMPILER} ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER}
  ifeq ($(shell [ -e ${SOLPSTOP}/SETUP/config.common.${COMPILER} ] && echo yes || echo no ),yes)
    MAKES += ${SOLPSTOP}/SETUP/config.common.${COMPILER}
  endif
endif
ifeq ($(shell [ -e ${SOLPSTOP}/SETUP/setup.csh.${HOST_NAME}.${COMPILER}.local ] && echo yes || echo no ),yes)
  MAKES += ${SOLPSTOP}/SETUP/setup.csh.${HOST_NAME}.${COMPILER}.local
endif
ifeq ($(shell [ -e ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER}.local ] && echo yes || echo no ),yes)
  include ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER}.local
  MAKES += ${SOLPSTOP}/SETUP/config.${HOST_NAME}.${COMPILER}.local
endif

MAKETAGS ?= ctags -e -f

# Extensions for object directories when various options are used
ifdef SOLPS_OPENMP
EXT_OPENMP = .openmp
endif
ifdef SOLPS_DEBUG
EXT_DEBUG = .debug
endif
ifdef USE_IMPGYRO
EXT_IMPGYRO = .ig
else
ifdef SOLPS_MPI
EXT_MPI = .mpi
endif
endif

OBJDIR = ${PWD}/builds/${HOST_NAME}.${COMPILER}${EXT_DEBUG}
B2OBJ = ${SOLPSTOP}/modules/B2.5/builds/couple_SOLPS-ITER.${HOST_NAME}.${COMPILER}${EXT_OPENMP}${EXT_MPI}${EXT_DEBUG}

ifeq ($(shell [ -e config/config.${HOST_NAME}.${COMPILER} ] && echo yes || echo no ),yes)
include config/config.${HOST_NAME}.${COMPILER}
MAKES+= config/config.${HOST_NAME}.${COMPILER}
else
$(error config/config.${HOST_NAME}.${COMPILER} not found)
endif

ifeq ($(shell [ -e config/config.common.${COMPILER} ] && echo yes || echo no ),yes)
include config/config.common.${COMPILER}
MAKES+= config/config.common.${COMPILER}
endif

ifeq ($(shell [ -e config/config.${HOST_NAME}.${COMPILER}.local ] && echo yes || echo no ),yes)
include config/config.${HOST_NAME}.${COMPILER}.local
MAKES+= config/config.${HOST_NAME}.${COMPILER}.local
endif

#OBJS=amvald.o amview.o amgraph.o amxvars.o amvars.o amundo.o \
#     amfio.o amdbase.o ammenu.o aminfo.o ammain.o vacreate.o \
#     amfile.o amtext.o calc.o vars.o ngroups.o amdoc.o amxapp.o \
#     xmform2t.o x_~fbr.o

OBJS=amvald.o amview.o amgraph.o amxvars.o amvars.o amundo.o \
     amfio.o amdbase.o ammenu.o aminfo.o ammain.o vacreate.o \
     amfile.o amtext.o calc.o vars.o ngroups.o amdoc.o amxapp.o \
     x_~fbr.o

DEST = $(OBJS:%.o=$(OBJDIR)/%.o)

ifdef USE_MOTIF
# AMDS with the Motif interface
ifneq ($(shell printf '\043include <Xm/Xm.h>\n' | $(CC) $(INCLUDES) -x c -E - >/dev/null 2>&1 && echo yes),yes)
$(error AMDS with USE_MOTIF needs Motif: Xm/Xm.h not found by $(CC) $(INCLUDES))
endif
GUISTAMP = ${OBJDIR}/.gui_motif

all: $(RES2FBR) $(TARGET) $(CALC)

.PHONY: VERSION clean neat all depend listobj force

$(OBJDIR)/vacreate.o:
	$(CC) $(CFLAGS) $(INCLUDES) -DCbFree=CbFree_ignore -c src/vacreate.c -o $(OBJDIR)/vacreate.o

$(OBJDIR)/%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(TARGET): $(DEST) $(MAKES) | ${GUISTAMP}
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $(DEST) $(LIBS)
else
# AMDS with the Python interface: the core, the resources and src/py as a
# shared library for lib/python/amds, without Motif and X11; the X and
# Motif headers named by amds.h are src/py/Xm/Xm.h and empty files
GUISTAMP = ${OBJDIR}/.gui_python
PYDIR    = ${OBJDIR}/python
PYSTUB   = ${PYDIR}/stub
ifeq ($(shell uname -s),Darwin)
PYLIB    = ${PYDIR}/libamds.dylib
PYLIBOPT = -dynamiclib
else
PYLIB    = ${PYDIR}/libamds.so
PYLIBOPT = -shared
endif
PYSRC    = $(addprefix src/,amdbase.c amdoc.c amfile.c amundo.c amvars.c \
             calc.c vars.c ngroups.c x_~fbr.c) $(wildcard src/py/*.c)
PYDEST   = $(addprefix ${PYDIR}/,$(notdir $(PYSRC:.c=.o)))
PYHDR    = $(addprefix ${PYSTUB}/,X11/Shell.h $(addprefix Xm/,$(addsuffix .h, \
             Protocols MainW RowColumn Separator ToggleB CascadeB Text Form \
             PushB DrawingA DialogS MessageB ArrowB Label FileSB List TextF \
             Frame ScrolledW PanedW)))
PYINC    = -Isrc/py -I${PYSTUB} -Isrc
VPATH   += src/py

all: $(RES2FBR) ${PYLIB} $(CALC)

.PHONY: VERSION clean neat all depend listobj force

${PYLIB}: $(PYDEST) $(MAKES) | ${GUISTAMP}
	$(CC) $(CFLAGS) $(PYLIBOPT) -o $@ $(PYDEST) -lpthread -lm

${PYDIR}/%.o : %.c | $(PYHDR)
	$(CC) $(CFLAGS) -fPIC $(PYINC) -c $< -o $@

$(PYHDR):
	mkdir -p $(dir $@)
	: > $@

$(OBJDIR)/res2fbr.o: src/res2fbr.c
	-mkdir -p ${OBJDIR}
	$(CC) $(CFLAGS) -c src/res2fbr.c -o $@
endif

# The stamp tells scripts/amds which AMDS was built last
${GUISTAMP}:
	-mkdir -p ${OBJDIR}
	rm -f ${OBJDIR}/.gui_python ${OBJDIR}/.gui_motif
	touch $@

src/x_~fbr.c: src/amds.xrs $(RES2FBR)
	$(RES2FBR) amdsResources < src/amds.xrs > src/x_~fbr.c

$(RES2FBR): $(OBJDIR)/res2fbr.o $(MAKES)
	$(CC) $(CFLAGS) -o $(RES2FBR) $(OBJDIR)/res2fbr.o

$(CALC): ${B2OBJ}/calc_atomic_data.exe $(MAKES)
	cp ${B2OBJ}/calc_atomic_data.exe $(CALC)
	touch $(CALC)

dirs: $(OBJDIR)

neat:
	rm -rf ${OBJDIR}/*.o src/x_~fbr.c

$(OBJDIR):
	mkdir -p $(OBJDIR)

ifdef USE_MOTIF
clean:
	/bin/rm -f $(OBJDIR)/*.o src/x_~fbr.c $(TARGET) $(RES2FBR) $(CALC) \
	$(OBJDIR)/dependencies* $(OBJDIR)/LISTOBJ
else
clean:
	/bin/rm -f ${PYDIR}/*.o ${PYLIB} ${PYDIR}/dependencies* $(PYHDR) \
	$(OBJDIR)/res2fbr.o src/x_~fbr.c $(RES2FBR) $(CALC)
endif

TAGS:	tags

tags:
	rm -f TAGS ; ${MAKETAGS} TAGS src/*.c src/*.h || touch TAGS

ifdef USE_MOTIF
depend: ${OBJS:.o=.c}
	@$(CC) $(INCLUDES) -M $^ | sed '/^[^ ]*.o: / s|^|${OBJDIR}/|' | \
	sed -e 's,^${OBJDIR}/,\$${OBJDIR}/,' | \
	sed 's,: ${SOLPSTOP},: $${SOLPSTOP},' > ${OBJDIR}/dependencies.${COMPILER}
else
depend: $(PYSRC) | $(PYHDR)
	@$(CC) $(PYINC) -M $(PYSRC) | sed '/^[^ ]*.o: / s|^|${PYDIR}/|' | \
	sed -e 's,^${PYDIR}/,\$${PYDIR}/,' | \
	sed 's,: ${SOLPSTOP},: $${SOLPSTOP},' > ${PYDIR}/dependencies.${COMPILER}
endif

listobj:
	@P=${OBJDIR}; cd src ; rm -f $${P}/LISTOBJ; touch $${P}/LISTOBJ; \
	echo "OBJS =" *.c | sed -e 's/ [^ /]*\// /g' -e 's/\.c/.o/g' -e 's/res2fbr\.o//g' > $${P}/LISTOBJ

${OBJDIR}/LISTOBJ: listobj

VERSION: src/git_version.h

src/git_version.h: force
	@echo "#define GIT_VERSION \"`git describe --tags --dirty --always`\"" > src/git_version_new.h
	@if cmp -s src/git_version_new.h src/git_version.h; then rm src/git_version_new.h; else mv src/git_version_new.h src/git_version.h; fi

ifdef USE_MOTIF
${OBJDIR}/dependencies.${COMPILER}:
	-mkdir -p ${OBJDIR}
	printf '# Dummy dependencies file for amds\n' > ${OBJDIR}/dependencies.${COMPILER}
	${MAKE} VERSION
	${MAKE} tags
	${MAKE} listobj
	${MAKE} depend

$(shell [ -s ${OBJDIR}/dependencies.${COMPILER} ] || rm -f ${OBJDIR}/dependencies.${COMPILER})
include ${OBJDIR}/dependencies.${COMPILER}
else
${PYDIR}/dependencies.${COMPILER}:
	-mkdir -p ${PYDIR}
	printf '# Dummy dependencies file for amds\n' > ${PYDIR}/dependencies.${COMPILER}
	${MAKE} VERSION
	${MAKE} tags
	${MAKE} depend

$(shell [ -s ${PYDIR}/dependencies.${COMPILER} ] || rm -f ${PYDIR}/dependencies.${COMPILER})
include ${PYDIR}/dependencies.${COMPILER}
endif
