include_directories( src/hellocmakemain
		     src/hellocmakemainapplication)

add_executable(app-hellocmake 
				src/hellocmakemain/HelloCmakeMain.cpp
				src/hellocmakemainapplication/HelloCmakeMainApplication.cpp		
				)
