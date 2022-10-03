from email.header import decode_header
from defs import *
from pdf2image import convert_from_path
import os
import cv2
import shutil


def check_decoded_file_name(file_name_decode):
    if file_name_decode[0][0] is not None and file_name_decode[0][1] is not None:
        print(file_name_decode[0][0])
        print('charset = ' + file_name_decode[0][1])
        file_name_decode = file_name_decode[0][0].decode('utf-8',
                                                         'backslashreplace')
    else:
        file_name_decode = str(file_name_decode[0][0])

    return file_name_decode


def rename_with_extension(file_path, current_file_path, folder_path="", s_name="", f_name=""):
    extension_low = (os.path.splitext(file_path)[1]).lower()
    # extension_low = extension.lower()
    original_file = os.path.join(current_file_path, 'original' + extension_low)
    if folder_path and f_name:
        shutil.move(os.path.join(folder_path, s_name, 'upload/scans', f_name), original_file)
    else:
        os.rename(file_path, original_file)
    os.chmod(original_file, 0o0777)
    return original_file, extension_low


def find_attachment(part, current_mail_path, part_counter):
    if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
        file_name = part.get_filename()
        if bool(file_name):
            current_file_path = os.path.join(current_mail_path, 'file_' + str(part_counter))
            try:
                os.mkdir(current_file_path, 0o777)
                os.chmod(current_file_path, 0o0777)
            except FileExistsError as e:
                print('directory_exist')

            decoded_file_name = check_decoded_file_name(decode_header(file_name))
            file_path = (os.path.join(current_file_path, decoded_file_name)).replace(' ', '')
            if not os.path.isfile(file_path):
                fp = open(file_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
            return current_file_path, file_path
        return "", ""
    return "", ""


def pdf_processing(original, path, current_file_path):
    page = 1
    try:
        images = convert_from_path(original, output_folder=path)
        for item in images:
            image_processing(original, current_file_path, page, item)
            page += 1
    except Exception as e:
        print(e)


def image_processing(original, current_file_path, page=1, item=None):
    page_name_without_extension = 'page_' + str(page)
    page_name = 'page_' + str(page) + '.jpg'
    page_file = os.path.join(current_file_path, page_name)
    print("pg: ", page_file)
    if item:
        print(item)
        item.save(page_file, 'JPEG')
        os.chmod(page_file, 0o0777)
        img = cv2.imread(page_file)
    else:
        img = cv2.imread(original)
    img = resizing(img, 'mail')
    rotate(img, page_file)
    cv_start(page_file, current_file_path, page_name_without_extension)
