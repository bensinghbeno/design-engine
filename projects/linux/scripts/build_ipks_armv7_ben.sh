#!/bin/bash -e

####################################
# Variable Defaults
####################################

SOURCE_PATH=`pwd`
ALLOWED_ARCHS="armv7"
PENDING_ARCH="x86"
KERNEL_VERSION="3.10.53"
SW_VERSION="${PWD##*/}"
DYNAMIC_LINKER="/lib/ld-linux-armhf.so.3"
WGET="wget --passive-ftp -nd -t 3"

function show_help {
  printf "\033[31;1m Please specify one of the following supported architectures: ${ALLOWED_ARCHS}\033[0m\n"
  exit 1
}

function show_pending {
  printf "\033[31;1m x86 architecture is currently unsupported please try: ${ALLOWED_ARCHS}\033[0m\n"
  exit 1
}

####################################
# Process Commandline Arguments
####################################

if [ -z "$1" ]
then
  show_help
fi

case $1 in
  $PENDING_ARCH) show_pending
    ;;
  ${ALLOWED_ARCHS})
    ARCH=$1
    ;;
  *) show_help
     ;;
esac

if [ ${ARCH} == "armv7" ]
then
  PREFIX=${ARM_HOST}/bin/arm-none-linux-gnueabi-
  HOST=armv7-none-linux-gnueabi
fi

DIST=${ARCH}-dist

####################################
# Start Script
####################################

echo -e "\n\e[44m           ***********Welcome by Ben's ipk package builder , lets build $SW_VERSION *********\e[0m\n"


####################################
# Build Commands
####################################

echo -e "\n\e[32m           *********** Clean old build *********\e[0m\n"
make clean
rm -rf ../build

echo -e "\n\e[32m           *********** Configure build *********\e[0m\n"

mkdir -p ${SOURCE_PATH}/../build/version-${SW_VERSION}/${ARCH}/bin_2
echo "Build Directory Created"
cd ${SOURCE_PATH}
echo "Enter Source Directory - ${SOURCE_PATH}" 

./configure \
    --build=x86_64-unknown-linux-gnu                        \
    --host=${HOST}                                          \
    --target=arm-none-linux-gnueabi                   \
    --prefix=/usr                                           \
CC=${PREFIX}gcc                                             \
CXX=${PREFIX}g++                                            \
AR=${PREFIX}ar                                              \
AS=${PREFIX}as                                              \
LD=${PREFIX}ld                                              \
NM=${PREFIX}nm                                              \
RANLIB=${PREFIX}ranlib                                      \
STRIP=${PREFIX}strip                                        \
OBJDUMP=${PREFIX}objdump                                    \
CFLAGS="-Wl,--dynamic-linker=$DYNAMIC_LINKER -march=armv7-a -mfpu=neon -mfloat-abi=hard"

echo -e "\n\e[32m           *********** make *********\e[0m\n"
make -j8

echo -e "\n\e[32m           *********** make install *********\e[0m\n"
make install DESTDIR=${SOURCE_PATH}/../build/version-${SW_VERSION}/${ARCH}/bin

echo -e "\n\e[44m                     ***********Packages are built successfully*********                    \e[0m\n"

