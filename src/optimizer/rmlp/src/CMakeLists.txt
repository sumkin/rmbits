set(CMAKE_C_FLAGS_RELEASE "-0fast")
set(CMAKE_C_FLAGS_DEBUG "-lprofiler")

project (rmlp)
add_library(rmlp SHARED posval.c
                        smplx.c
                        smplxtblrow.c
                        smplxtblclmn.c
                        smplxtbl.c)


