libahff.dylib: ahff2png.c pixel.c rg_etc1.o rg_etc1wrap.o lodepng.c
	${CXX} ${CXXFLAGS} -c rg_etc1.cpp rg_etc1wrap.cpp
	${CC} ${CFLAGS} -shared -o $@ ahff2png.c lodepng.c rg_etc1.o rg_etc1wrap.o -lz -g
