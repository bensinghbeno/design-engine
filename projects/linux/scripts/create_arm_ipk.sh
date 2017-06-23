#!/bin/bash -e

SCRIPT_PATH=`pwd`
PENDING_ARCH="x86"
ALLOWED_ARCHS="armv7a x86"
TARGET_ARCH=$1
SOURCE_DIR_NAME="${PWD##*/}"
IPK_PACKAGE_NAME=${SOURCE_DIR_NAME%-*}
IPK_PACKAGE_VERSION=${SOURCE_DIR_NAME#*-}
BUILD_ROOT_PATH=$SCRIPT_PATH/../build/$SOURCE_DIR_NAME/$TARGET_ARCH/bin
IPK_NAME="${SOURCE_DIR_NAME}_armv7a.ipk"


function show_help {
  printf "\033[31;1m Please specify one of the following supported architectures: ${ALLOWED_ARCHS}\033[0m\n"
  exit 1
}

function show_pending {
  printf "\033[31;1m x86 architecture is currently unsupported please try: armv7a \033[0m\n"
  exit 1
}


clear
printf "\n\e[44m ***** Hello, This is Ben's arm IPK package creater ******\n\e[0m"


if [ -z "$1" ]
then
  show_help
fi

case $TARGET_ARCH in
  $PENDING_ARCH) show_pending
    ;;
  "armv7a")
    TARGET_ARCH="armv7a"
    ;;
  *) show_help
     ;;
esac

printf "\n Built binary root location = $BUILD_ROOT_PATH \n\n"

rm -rf $SCRIPT_PATH/../packages
mkdir -p $SCRIPT_PATH/../packages/unsigned/ipk
cd $SCRIPT_PATH/../packages/unsigned/ipk
mkdir ./CONTROL
mkdir ./DATA
mkdir ./IPK

echo "Package: $IPK_PACKAGE_NAME
Version: $IPK_PACKAGE_VERSION
Description: $IPK_PACKAGE_NAME-$IPK_PACKAGE_VERSION
Section: base
Priority: optional
Maintainer: 
License: GPL
Architecture: $TARGET_ARCH
OE: sh
Homepage: 
Depends: libc6
Source: " > ./CONTROL/control

cp -r $BUILD_ROOT_PATH/* ./DATA

echo "2.0" > ./IPK/debian-binary

cd ./CONTROL && tar -cvzf ./control.tar.gz * && cd ../DATA && tar -cvzf ./data.tar.gz *
cd $SCRIPT_PATH/../packages/unsigned/ipk

mv ./CONTROL/control.tar.gz ./IPK
mv ./DATA/data.tar.gz ./IPK

cd ./IPK
tar -cvzf $IPK_NAME control.tar.gz data.tar.gz debian-binary

printf "\n\e[44m ***** Package Creator Completed ******\e[0m\n"
