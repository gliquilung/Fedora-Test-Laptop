#!/usr/bin/bash

http="http://10.42.0.1/"

isofile=""
tftpdir=""
httpdir=""
name=""

OPTIND=1

while getopts "h?i:t:n:w:" opt; do
  case "$opt" in
    h|\?)
      echo "usage ${ARGV[0]}"
      echo "-----"
      echo " -i ISO_FILE"
      echo " -t TFTP_DIR"
      echo " -w WEB_DIR"
      echo " -n NAME"
      exit 0
      ;;
    i) isofile=$OPTARG
      ;;
    t) tftpdir=$OPTARG
      ;;
    n) name=$OPTARG
      ;;
    w) httpdir=$OPTARG
      ;;
  esac
done

if [ ! -f "$isofile" ]; then
  echo "the iso either wasn't given or does not exist"
  exit 1
fi

if [ ! -d "$tftpdir" ] || [ ! -f "$tftpdir/pxelinux.0" ]; then
  echo "tftp directory does not exist or there is no pxelinux available"
  exit 1
fi

tftpsubdir="${tftpdir}/images/${name}/"
if [ -d "$tftpsubdir" ] || [ "x$name" -eq "x" ]; then
  echo "the name wasn't given or already exists: $name"
  exit 1
fi

httpsubdir="${httpdir}/images/${name}/"
httpurl="${http}images/${name}/squashfs.img"
if [ -d "$httpsubdir" ]; then
  echo "the name wasn't given or already exists: $name"
  exit 1
fi

tempdir="$(mktemp -d)"

echo "mounting $isofile"
sudo mount -o loop $isofile $tempdir

vmlinuz="${tempdir}/images/pxeboot/vmlinuz"
initrd="${tempdir}/images/pxeboot/initrd.img"
squashfs="${tempdir}/LiveOS/squashfs.img"

if [ ! -f "$vmlinuz" ] || [ ! -f "$initrd" ]; then
  echo "could not find vmlinuz and/or initrd.img inside the iso"
  exit 1
fi

if [ -f "$squashfs" ]; then
  echo "detected live image"
fi


echo "coping files to tftp directory"
sudo mkdir -p $tftpsubdir

echo "copy vmlinuz"
sudo cp $vmlinuz $tftpsubdir

echo "copy initrd.img"
sudo cp $initrd $tftpsubdir

if [ -f "$squashfs" ]; then
  echo "copy squashfs"
  sudo cp $squashfs $httpsubdir
fi

echo "unmounting $isofile"
sudo umount $tempdir
rm -r $tempdir

cat <<EOF
label ${name}
  menu label ${name}
  kernel images/${name}/vmlinuz
  append initrd=images/${name}/initrd.img root=live:${httpurl} ro rd.live.image rd.luks=0 rd.md=0 rd.dm=0
EOF
