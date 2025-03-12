import subprocess
import os
from PIL import Image
import imagequant

def compress_jpeg(input_path, output_path, quality=40):
    """
    Compress JPEG using MozJPEG.
    
    :param input_path: Path to the input JPEG file.
    :param output_path: Path to save the compressed JPEG.
    :param quality: Quality level (lower means smaller size, but lower quality).
    """
    command = f"cjpeg -quality {quality} -optimize -progressive -outfile {output_path} {input_path}"
    subprocess.run(command, shell=True)
    print(f"JPEG compressed and saved to: {output_path}")
import subprocess

def compress_png(input_path, output_path, quality=80):
    subprocess.run(["pngquant", "--quality", f"{quality}", "--output", output_path, input_path], check=True)

# Example usage
#compress_jpeg("nobita.jpg", "output1.jpg", quality=40)#32
compress_png("mounika.png", "output.png")#60
