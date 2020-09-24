#!/usr/bin/env python3

import logging
import os
import sys
import argparse
from util.file import directories, mkdir_recursive, mkdir
import shutil
#import copy
import subprocess
# import zipfile
from config import *


logging.basicConfig(stream=sys.stdout, format="%(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

job_result_dir = ""
#job_result_dir_relative = ""

# def zip_file():
#     zip_name = 'poc' +'.zip'
#     z = zipfile.ZipFile(zip_name,'w',zipfile.ZIP_DEFLATED)
#     z.write('./README.md', '..\\//')
#     z.close()
def handle_ext4_vfat(file, filetype):
    #global job_result_dir
    ext = os.path.basename(file)
    mnt_name = os.path.join(job_result_dir, "mnt_" + ext)
    if not os.path.isdir(mnt_name):
        os.makedirs(mnt_name)

    #mkdir_recursive(mnt_name)

    #new_img_path = os.path.join(os.getcwd(), new_img_directory, os.path.basename(firmware_image))
    #shutil.copy(file, job_result_dir)
    proc = subprocess.Popen("cp " + file + " " + job_result_dir, shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _ = (proc.communicate()[0]).decode()
    #log.info(foo)

    proc = subprocess.Popen("sudo mount -o ro -t " + filetype + " " + os.path.join(job_result_dir, ext) + " " + mnt_name, shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _ = (proc.communicate()[0]).decode()
    #log.info(foo)
    return

def handle_bootimg(file, working_directory):
    proc = subprocess.Popen("./tools/atsh_setup/imgtool/imgtool.ELF64 " + file + " extract", shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _ = (proc.communicate()[0]).decode()

    proc = subprocess.Popen("file -b ./extracted/ramdisk", shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    foo = (proc.communicate()[0]).decode()

    #print(foo)
    if foo.startswith("gzip"):
        pwd = os.environ["PWD"]
        os.chdir(os.path.join(pwd, "extracted"))    # does not know how to control the gunzip command
        proc = subprocess.Popen("gunzip -c ramdisk | cpio -i", shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode()
        os.remove("ramdisk")
        os.remove("kernel")
        #print(foo)

        for dirpath, dirnames, filenames in os.walk("./"):
            for filename in filenames:
                proc = subprocess.Popen(args="file -b '" + os.path.join(dirpath, filename) + "'", shell=True, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                file_format = (proc.communicate()[0]).decode().strip()
                if file_format.startswith("gzip"):
                    shutil.move(os.path.join(dirpath, filename), os.path.join(dirpath, filename) + ".gz")
                    proc = subprocess.Popen("gunzip -f " + os.path.join(dirpath, filename) + ".gz", shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    _ = (proc.communicate()[0]).decode()

        os.chdir(pwd)

        fname = os.path.basename(file)
        if not os.path.isdir(os.path.join(working_directory, fname)):
            os.makedirs(os.path.join(working_directory, fname))

        proc = subprocess.Popen(args="sudo cp -a extracted/* '" + os.path.join(working_directory, fname) + "'", shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode().strip()

        proc = subprocess.Popen(args="rm -rf extracted", shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode().strip()

    else:
        log.error("Other format bootimg")


    return

def handle_simg(file):

    nam, _ = os.path.splitext(os.path.basename(file))
    ext = nam + ".ext4"
    mnt_name = os.path.join(job_result_dir, "mnt_" + ext)

    proc = subprocess.Popen("simg2img " + file + " " + os.path.join(job_result_dir, ext), shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _ = (proc.communicate()[0]).decode()
    #log.info(foo)

    if nam.lower().startswith("super"):
        #print(foo)
        #print("foo")
        log.info("SUPER file of vendor huawei")

        if not os.path.isdir(os.path.join(job_result_dir, "super")):
            os.makedirs(os.path.join(job_result_dir, "super"))

        proc = subprocess.Popen("./tools/atsh_setup/unpack_superimg_tools/lpunpack " + os.path.join(job_result_dir, ext) + " " + os.path.join(job_result_dir, "super"), shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode()

        # walk the file system to mount one-by-one
        for dirpath, dirnames, filenames in os.walk(os.path.join(job_result_dir, "super")):
            for filename in filenames:
                nam, _ = os.path.splitext(os.path.basename(filename))
                ext = nam + ".SUPER"
                mnt_name = os.path.join(job_result_dir, "mnt_" + ext)
                if not os.path.isdir(mnt_name):
                    os.makedirs(mnt_name)

                proc = subprocess.Popen("sudo mount -o loop -t erofs " + os.path.join(dirpath, filename) + " " + mnt_name, shell=True, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                _ = (proc.communicate()[0]).decode()
                os.system("cp " + os.path.join(dirpath, filename) + " " + os.path.join(job_result_dir, ext))
                #print(foo)

    else:
        if not os.path.isdir(mnt_name):
            os.makedirs(mnt_name)

        proc = subprocess.Popen("sudo mount -o ro -t ext4 " + os.path.join(job_result_dir, ext) + " " + mnt_name, shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode()
    #log.info(foo)

    return

def proc_file(working_directory, unpack_directory, vendor):
    for dirpath, dirnames, filenames in os.walk(unpack_directory):
        for filename in filenames:
            if vendor.lower() == "huawei":
                just_name, _ = os.path.splitext(filename)

                if just_name.lower().startswith("kernel"):
                    with open(os.path.join(dirpath, filename), "rb+") as fwh:
                        fwh.seek(0x1000)
                        t = fwh.read()
                        fwh.seek(0x0)
                        fwh.write(t)
                        fwh.truncate()

                proc = subprocess.Popen(args="file -b '" + os.path.join(dirpath, filename) + "'", shell=True, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                file_format = (proc.communicate()[0]).decode().strip()
                #file_format_tag = file_format.split(' ')[0]
                fsize = os.path.getsize(os.path.join(dirpath, filename))
                fsize = fsize / float(1024 * 1024)
                print(fsize)
                print(os.path.join(dirpath, filename))
                print(file_format + "\n")
                if file_format.startswith("Android sparse image"):
                    handle_simg(os.path.join(dirpath, filename))
                elif file_format.startswith("Android bootimg"):     # Android bootimg, ramdisk (0x11000000), page size: 2048
                    handle_bootimg(os.path.join(dirpath, filename), working_directory)
                elif file_format.startswith("Linux rev") and file_format.find("ext4") != -1:
                    handle_ext4_vfat(os.path.join(dirpath, filename), "ext4")
                elif file_format.startswith("DOS/MBR boot sector"):
                    handle_ext4_vfat(os.path.join(dirpath, filename), "vfat")
                else:
                    pass
                    # fsize = os.path.getsize(os.path.join(dirpath, filename))
                    # fsize = fsize / float(1024 * 1024)
                    # if fsize > 20.0:
                    #     print(fsize)
                    #     print(os.path.join(dirpath, filename))
                    #     print(file_format + "\n")

    return

def unpack_image(working_directory, firmware_image, unpack_directory):


    if os.path.isdir(working_directory):
        log.info("Removing existing `extract` directory: %s.", working_directory)
        shutil.rmtree(working_directory)

    if not os.path.isdir(unpack_directory):
        os.makedirs(unpack_directory)
    if not os.path.isdir(job_result_dir):
        os.makedirs(job_result_dir)

    # logging.info("Creating `extract` folder.")
    # new_img_directory = os.path.join("extract", vendor.lower(), firmware_name)
    # mkdir_recursive(new_img_directory)

    # new_img_path = os.path.join(os.getcwd(), new_img_directory, os.path.basename(firmware_image))
    # shutil.copy(firmware_image, new_img_path)

    proc = subprocess.Popen(args="file -b " + firmware_image, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    image_format = (proc.communicate()[0]).decode()
    #print(image_format)
    f1 = image_format.split(" ")[0]
    #print(f1)
    if f1.lower() == 'zip' or f1.lower() == 'java':
        log.info("A valid zip file.")
        logging.info("Start extracting firmware to: %s.", unpack_directory)
        shutil.unpack_archive(firmware_image, extract_dir = unpack_directory, format = 'zip')

        proc = subprocess.Popen(args="ls '" + os.path.join(unpack_directory, "UPDATE.APP") + "'| wc -l", shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        file_c = (proc.communicate()[0]).decode().strip()

        # --------------- UPDATE.APP -----------------
        if file_c == "1":
            pwd = os.environ["PWD"]
            os.chdir(unpack_directory)

            log.info("Find UPDATE.APP in root folder.")
            proc = subprocess.Popen(os.path.join(pwd, "./tools/atsh_setup/split_updata.pl/splitupdate") + " " + os.path.join(unpack_directory, "UPDATE.APP"), shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ret = (proc.communicate()[0]).decode()
            log.info(ret)

            os.system("rm UPDATE.APP")
            os.chdir(pwd)

        # --------------- USERDATA.APP -----------------
        proc = subprocess.Popen(args="ls '" + os.path.join(unpack_directory, "USERDATA.APP") + "'| wc -l", shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        file_c = (proc.communicate()[0]).decode().strip()

        if file_c == "1":
            pwd = os.environ["PWD"]
            os.chdir(unpack_directory)

            log.info("Find USERDATA.APP in root folder.")
            proc = subprocess.Popen(os.path.join(pwd, "./tools/atsh_setup/split_updata.pl/splitupdate") + " " + os.path.join(unpack_directory, "USERDATA.APP"), shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ret = (proc.communicate()[0]).decode()
            log.info(ret)

            os.system("rm USERDATA.APP")
            os.chdir(pwd)

        # https://pro-teammt.ru/en/online-firmware-database-ru/
        # no need to consider dload-style ROMs. Related signature: dload, UPDATE.APP, update.zip
        # because huawei does not provide rom any more.
        # http://news.imobile.com.cn/articles/2017/0904/180053.shtml
    else:
        log.error("Image type not support yet.")
        exit(1)

    proc = subprocess.Popen(args="ls '" + unpack_directory + "'| wc -l", shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    file_c = (proc.communicate()[0]).decode().strip()
    #print(file_c)
    if file_c == "1":
        proc = subprocess.Popen(args="ls '" + unpack_directory + "'", shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cur_dir = (proc.communicate()[0]).decode().strip()
        #print("mv " + os.path.join(unpack_directory, cur_dir) + "/* '" + unpack_directory + "'")
        os.system("mv " + os.path.join(unpack_directory, cur_dir) + "/* '" + unpack_directory + "'")
        os.system("rm -rf '" + os.path.join(unpack_directory, cur_dir) + "'")

    return

def py_extract(firmware_image, vendor, job_id):

    global job_result_dir
    job_result_dir = os.path.join(os.environ['HOME'], 'atsh_tmp' + job_id)

    if not os.access(firmware_image, os.R_OK):
        logging.error("Image `%s` is unaccessable.", firmware_image)
        exit(1)

    # pre-extract
    if vendor.lower() == "huawei":
        logging.info("Porcessing `%s` image.", vendor)
    else:
        logging.error("Vendor %s not support yet.", vendor)
        exit(1)

    firmware_name, _ = os.path.splitext(os.path.basename(firmware_image))
    working_directory = os.path.join(os.getcwd(), "extract", vendor.lower(), firmware_name)
    unpack_directory = os.path.join(os.getcwd(), "extract", vendor.lower(), firmware_name, 'extract_sub')
    #mkdir_recursive(unpack_directory)
    #unpack_directory = os.path.join(os.getcwd(), unpack_directory)

    # clean the system first
    if os.path.isdir(job_result_dir):
        proc = subprocess.Popen("sudo umount - fl " + os.path.join(job_result_dir, "mnt_") + "* > /dev/null",
                                shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode()

        proc = subprocess.Popen("rm -rf " + job_result_dir + " > /dev/null",
                                shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _ = (proc.communicate()[0]).decode()


    unpack_image(working_directory, firmware_image, unpack_directory)
    proc_file(working_directory, unpack_directory, vendor)


    #copy.copy()


    # Unzip the file


    # post-extract
    # TODO: Special deal with UPDATE.APP, UPDATE.APP, update.zip later

    return

def main():
    # zip_file()

    print("Rewrite the original shell script for learning purpose.")

    parser = argparse.ArgumentParser()
    parser.add_argument('--vendor', required=True)
    parser.add_argument('--job_id', required=True)
    parser.add_argument("firmware_image", help='absolute path')
    args = parser.parse_args()

    #logging.info("Cleaning up temporary files from prior run (if any).")

    py_extract(args.firmware_image, args.vendor, args.job_id)

if __name__ == "__main__":
    sys.exit(main())