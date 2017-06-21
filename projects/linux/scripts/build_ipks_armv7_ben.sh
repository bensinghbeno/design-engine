#!/bin/bash -e

SCRIPT_PATH=`pwd`
ALLOWED_ARCHS="armv7"
KERNEL_VERSION="3.10.53"
SW_VERSION="0"
DYNAMIC_LINKER="/lib/ld-linux-armhf.so.3"
WGET="wget --passive-ftp -nd -t 3"

function show_help {
  printf "\033[31;1mPlease specify one of the following supported architectures: ${ALLOWED_ARCHS}\033[0m\n"
  exit 1
}

if [ -z "$1" ]
then
  show_help
fi

case ${ALLOWED_ARCHS} in
  $1)
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
# Build - Linaro VALGRIND #
####################################


mkdir -p ${SCRIPT_PATH}/build/version-${SW_VERSION}/${ARCH}/bin_2
echo "Build Directory Created"
cd ${SCRIPT_PATH}
echo "Enter Source Directory - ${SCRIPT_PATH}" 

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
CFLAGS="-Wl,--dynamic-linker=/lib/ld-linux-armhf.so.3 -march=armv7-a -mfpu=neon -mfloat-abi=hard"

make -j8
make install DESTDIR=${SCRIPT_PATH}/build/version-${SW_VERSION}/${ARCH}/bin_2

