#!/usr/bin/env python

"""
(c) 2012-2014 Johannes Lindenbaum
License: MIT License, see LICENSE file for details.
See README.md for usage and examples.
"""

import argparse
import os

from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

class BaseResizer(object):
    VERSION = '1.0.0'
    SILENCE = False

    SCALES = {}

    ACCEPTED_EXTENSIONS = ['.png', '.jpg']
    UNACCEPTED_EXTENSIONS = ['.9.png']

    EXCLUDE_SCALE = []

    def set_verbosity(self, silence):
        """
        Sets verbosity level of the script.
        :param silence:
        """
        if silence:
            self.SILENCE = silence

    def log(self, message):
        """
        Print to console if script hasn't been silenced
        :param message:
        """
        if self.SILENCE is False:
            print(message)

    def set_exclude_scale(self, scale):
        """
        Set a scale to exclude from processing.
        :param scale:
        """
        self.EXCLUDE_SCALE = scale

    def create_dir_if_nonexistant(self, directory):
        """
        Create directory if it does not exist.
        :param directory:
        """
        if os.path.exists(directory) is False:
            self.log("Creating output directory: " + directory)
            os.makedirs(directory)

    def resize_all_in_folder(self, input_path):
        """
        Process all files in a folder iff these do not have
        illegal extensions and are not NinePatch files
        :param input_path:
        """
        self.log("Processing folder: " + input_path)

        for file_name in os.listdir(input_path):
            # when bulk processing a folder ignore NinePatch files
            if file_name[-6:] not in self.UNACCEPTED_EXTENSIONS:
                self.process_file(input_path, file_name)

    def resize_image(self, folder_path, file_name, width, height, save=True):
        base_name, file_extension = os.path.splitext(file_name)
        if self.can_process_file(file_extension):
            self.log("Resizing file: " + file_name + " (" + str(width) + ", " + str(height) + ")")
            
            file_path = os.path.join(folder_path, file_name)
            image = Image.open(file_path)
            resized_image = image.resize((int(width), int(height)), Image.ANTIALIAS)
            
            if save:
                resized_image.save(file_path)
            return resized_image
    
    def resize_folder(self, folder_path, width, height):
        self.log("Processing folder: " + folder_path)
        
        for file_name in os.listdir(folder_path):
            self.resize_image(folder_path, file_name, width, height)

    def png_convert_image(self, folder_path, file_name):
        """
        Converts the provided folder_path/file_name to PNG.
        If a non-PNG extension file_name is passed in, the file is overwritten.
        Otherwise a .png file will be created. Ex. 'image.jpg' -> 'image.png'.
        :param folder_path:
        :param file_name:
        """
        
        base_name, file_extension = os.path.splitext(file_name)
        if self.can_process_file(file_extension):
            self.log("Converting file: " + file_name)
            
            file_path = os.path.join(folder_path, file_name)
            image = Image.open(file_path)
            save_file_path = os.path.join(folder_path, base_name + '.png')
            image.save(save_file_path, 'png')

    def png_convert_folder(self, folder_path):
        """
        Converts all images in provided folder to PNG.
        :param folder_path:
        :return:
        """
        
        self.log("Processing folder: " + folder_path)
        
        for file_name in os.listdir(folder_path):
            self.png_convert_image(folder_path, file_name)
    
    def scale_image(self, file_path, scale):
        """
        Opens the passed file_path, sacles that image with scale parameter and
        returns a new image object with the resized image.
        :rtype : Image
        :param file_path:
        :param scale:
        :return:
        """
        image = Image.open(file_path)
        image_size = image.size

        new_width = int(round(image_size[0] * scale))
        new_height = int(round(image_size[1] * scale))

        if new_width < 1:
            new_width = 1
        if new_height < 1:
            new_height = 1
        
        return self.resize_image('', file_path, new_width, new_height, save=False)

    def can_process_file(self, file_extension):
        """
        Determines if we can process the file based off the file extension
        :param file_extension:
        :return:
        """
        return file_extension in self.ACCEPTED_EXTENSIONS

    def process_file(self, input_directory, file_name):
        """
        Process an individual file. This includes NinePatch files
        """
        self.log("This does nothing in the BaseResizer")


class AndroidResResize(BaseResizer):
    """
    AndroidResResize deals with resizing assets
    in an xxxhdpi folder. Appropriately scales
    all assets and puts them into their proper
    folders.
    """
    
    SCALES = {
        'xxhdpi' : float(3) / 4, # xxhdpi is 3/4 of xxxhdpi
        'xhdpi': float(2) / 4, 
        'hdpi': float(1.5) / 4,
        'mdpi': float(1) / 4,
    }

    def process_file(self, input_directory, file_name):
        # determine file extension
        file_path = os.path.join(input_directory, file_name)
        base_name, file_extension = os.path.splitext(file_path)
        if self.can_process_file(file_extension):
            for scale_name, scale_value in self.SCALES.items():
                new_image = self.scale_image(file_path, scale_value)

                # determine if where we're writing to exists
                scale_dir = "../drawable-" + scale_name + "/"
                output_directory = os.path.join(input_directory, scale_dir)

                try:
                    self.create_dir_if_nonexistant(output_directory)
                except:
                    print("Could not create output directory: " + output_directory)
                    return

                # save processed image
                output_file_path = os.path.join(output_directory, file_name)
                new_image.save(output_file_path)


class IOSResResize(BaseResizer):
    """
    IOSResResize deals with resizing app icons for iOS apps.
    Deals with scaling @3x images down to @2x and @1x
    """
    
    app_icon = False
    
    SCALES = {
        '@2x': float(0.66666666666666),
        '@1x': float(0.33333333333333)
    }
    
    APP_ICON_SIZES = [29, 40, 58, 76, 80, 87, 120, 152, 167, 180]

    def set_process_app_icon(self, process):
        self.app_icon = process

    def process_app_icon(self, input_directory, file_name):
        """
        Process provided file into app icons. The script processes
        everything required for the 4S and up.
        
        :param input_directory:
        :param file_name:
        :return:
        """
        file_path = os.path.join(input_directory, file_name)
        base_name, file_extension = os.path.splitext(file_path)
        base_file_name, extension = os.path.splitext(file_name)
        self.log(base_name + " " + file_extension)
        if self.should_process_file(base_name, file_extension):
            for img_size in self.APP_ICON_SIZES:
                image = self.resize_image('', file_path, img_size, img_size, save=False)
                new_file_name = "%s-%dx%d%s" % (base_file_name, img_size, img_size, file_extension)
                new_file_path = os.path.join(input_directory, new_file_name)
                image.save(new_file_path)

    def should_process_file(self, base_name, file_extension):
        """
        Determine if iOS should process this image based off the @2x
        in the file name
        :param base_name:
        :param file_extension:
        :return:
        """
        can_process = self.can_process_file(file_extension)
        should_process = False
        if can_process:
            if "@3x" in base_name or self.app_icon == True:
                should_process = True
        return should_process

    def process_file(self, input_directory, file_name):
        file_path = os.path.join(input_directory, file_name)
        base_name, file_extension = os.path.splitext(file_path)
        
        if self.should_process_file(base_name, file_extension):
            stripped_base_name = base_name.replace("@3x", "")
            
            for scale_name, scale_value in self.SCALES.items():
                new_image = self.scale_image(file_path, scale_value)
                new_file_path = os.path.join(input_directory, stripped_base_name + scale_name + file_extension)
                new_image.save(new_file_path)

"""
Processors for individual arguments.
Main scipt entry point.
"""

def process_png_conversion(args):
    resizer = BaseResizer()
    resizer.set_verbosity(args.silence)

    resizer.log("Converting file(s) to PNG.")
    
    if args.file_path is not None:
        input_directory, file_path = os.path.split(args.file_path)
        resizer.png_convert_image(input_directory, file_path)
    elif args.folder_path is not None:
        resizer.png_convert_folder(args.folder_path)
    else:
        print("Must specify --file or --folder to convert to PNG.")
    
    resizer.log("Done.")
    exit()

def process_resizing(args):
    resizer = BaseResizer()
    resizer.set_verbosity(args.silence)
    
    resizer.log("Resizing file(s) to " + args.resize_dimension)
    
    width, height = args.resize_dimension.split('x')
    # TODO: Verify width, height are valid numbers
    
    if args.file_path is not None:
        input_directory, file_path = os.path.split(args.file_path)
        resizer.resize_image(input_directory, file_path, width, height)
    elif args.folder_path is not None:
        resizer.resize_folder(args.folder_path, width, height)
    else:
        print("Must specify --file or --folder to resize image.")        
    
    resizer.log("Done.")
    exit();

def process_arguments(args=None):
    
    # show version, exit
    if args.show_version:
        print(BaseResizer.VERSION)
        exit()
        
    # convert to png
    if args.png_convert:
        process_png_conversion(args)
    
    # resize
    if args.resize_dimension is not None:
        process_resizing(args)

    # determine platform
    resizer = None
    if args.platform_ios:
        resizer = IOSResResize()
    elif args.platform_android:
        resizer = AndroidResResize()

    # execute
    if resizer is None:
        print("Must specify a platform to perform actions with. -i / -a")
    else:
        resizer.set_verbosity(args.silence)
        resizer.set_exclude_scale(args.scale)
        
        if args.folder_path is not None:
            resizer.resize_all_in_folder(args.folder_path)
        elif args.file_path is not None:
            input_directory, file_path = os.path.split(args.file_path)
            if args.app_icon:
                resizer.set_process_app_icon(args.app_icon)
                resizer.process_app_icon(input_directory, file_path)
            else:
                resizer.process_file(input_directory, file_path)
        else:
            print("Must specify --folder or --file to process.")

if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="Automatically resize images for iOS and Android")

    # platform agnostic operations
    argParser.add_argument("--pngconv", default=False, action="store_true", dest="png_convert", help="Convert an image to PNG format")
    
    # arguments
    argParser.add_argument("--folder", default=None, dest="folder_path", help="Resizes all images in provided folder path.")
    argParser.add_argument("--file", default=None, dest="file_path", help="Resizes individual file provided by folder path.")
    argParser.add_argument("--exclude-scale", default=None, dest="scale", nargs="+", help="Excludes a scale. Separate multiple scales by spaces.")
    
    argParser.add_argument("--resize", default=None, dest="resize_dimension", help="Resizes following --file argument to WxH dimension")

    
    argParser.add_argument("-i", default=False, action="store_true", dest="platform_ios", help="Scale images for iOS projects")
    argParser.add_argument("-a", default=False, action="store_true", dest="platform_android", help="Scale images for Android projects")
    
    argParser.add_argument("--app-icon", default=False, action="store_true", dest="app_icon", help="Takes big image and sizes it for all iOS icon sizes. Use with --i and --file")

    argParser.add_argument("--silence", default=False, action="store_true", dest="silence", help="Silences all output, except errors.")
    argParser.add_argument("-v", default=False, action="store_true", dest="show_version", help="Shows the version.")
    
    argParser.add_argument("--prod", default=None, action="store_true", dest="prod", help="Looks for res/drawable-xxxhdpi subfolder and resizes all the images in that folder.")
    
    args = argParser.parse_args()

    process_arguments(args)
