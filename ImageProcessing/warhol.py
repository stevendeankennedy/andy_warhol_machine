#! /usr/bin/env python

from mpi4py import MPI
import PIL
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import random
import numpy
import sys

# picture width used in resizing an image
# tweak this to adjust size of image
WIDTH_SIZE=400

# upper and lower bounds of black and white shades, range 0-255
# tweak these to adjust colors
BLK_UPPER_BOUND=105
WHITE_LOWER_BOUND=145

# color dictionary, fg = foreground, bg = background, og = 'other'ground
# COLORS = [
#     {'bg' : (255,255,0), 'fg' : (50,9,125), 'og': (118,192,0)},
#     {'bg' : (0,122,240), 'fg' : (255,0,112), 'og': (255,255,0)},
#     {'bg' : (50,0,130),'fg' : (255,0,0),'og': (243,145,192)},
#     {'bg' : (255,126,0),'fg' : (134,48,149),'og': (111,185,248)},
#     {'bg' : (255,0,0),'fg' : (35,35,35),'og': (255,255,255)},
#     {'bg' : (122,192,0),'fg' : (255,89,0),'og': (250,255,160)},
#     {'bg' : (0,114,100),'fg' : (252,0,116),'og': (250,250,230)},
#     {'bg' : (250,255,0),'fg' : (254,0,0),'og': (139,198,46)},
#     {'bg' : (253,0,118),'fg' : (51,2,126),'og': (255,105,0)}
# ]
COLORS = [
    {'bg' : (50,5,0), 'fg' : (255,255,0), 'og': (118,192,0)}, # yellow
    {'bg' : (225,102,222 ), 'fg' : (158,222,255), 'og': (255,255,0)}, # bright candy
    {'bg' : (134,48,149),'fg' : (255,170,0),'og': (111,185,248)}, # orange
    {'fg' : (255,0,0),'bg' : (10,35,10),'og': (255,255,255)}, # red
    {'fg' : (122,192,0),'bg' : (255,89,0),'og': (250,255,160)}, # yellowish
    {'bg' : (0,114,100),'fg' : (252,114,116),'og': (250,250,230)}, # cyan
    {'fg' : (250,255,0),'bg' : (254,0,0),'og': (139,198,46)}, #red orange
    {'bg' : (50,0,35),'fg' : (255,2,199),'og': (255,105,0)}, # purple
    # {'bg' : (50,0,10),'fg' : (215,2,199),'og': (255,105,0)}, # pink
    {'bg' : (50,0,130),'fg' : (255,0,0),'og': (243,145,192)} # red!
]


# Resize the width of an image, maintaining aspect ratio of its height
def resizeImage(image):
  # new width of the picture
  width = WIDTH_SIZE

  # get aspect ratio percentage
  percent = (width/float(image.size[0]))

  # new height of the picture in relation to the width
  height = int((float(image.size[1])*float(percent)))

  # resize!
  image = image.resize((width,height), PIL.Image.ANTIALIAS)

  return image

# combine four images of the same size into a 4x4 grid
def aggregateImages(image1, image2, image3, image4):

  # get image size, only need one since they are all the same
  x = image1.size[0]
  y = image1.size[1]

  # create new image based on size of passed image
  canvas = Image.new("RGB", (x*2,y*2))

  # paste images into position
  canvas.paste(image1, (0,0))
  canvas.paste(image2, (x,0))
  canvas.paste(image3, (0,y))
  canvas.paste(image4, (x,y))

  # return the combined images
  return canvas

# creates a three toned vector like image mask
def warholify(image, colors):
  # convert to RGB mode, to get access to RGB channels
  image.convert('RGB')
  # get image width and height
  w,h = image.size
  # load the pixel data
  im = image.load()

  # create new image based on width and height of passed image
  mask = Image.new('RGB', (w,h))
  # load pixel data
  msk = mask.load()

  # iterate through the original image pixels
  # and modify mask pixels based on black and white bounds
  for i in range(img.size[0]):
    for j in range(img.size[1]):
      if im[i,j] < BLK_UPPER_BOUND:
        msk[i,j] = colors['bg']
      elif im[i,j] > WHITE_LOWER_BOUND:
        msk[i,j] = colors['fg']
      else:
        msk[i,j] = colors['og']

  return mask

# A different warhol technique, utilizing a posterize filter
def warholify_b(im, colors):
  # bits = random.choice([1,2]) # scale of colors
  bits = 2 # I don't know what is better, 1 or 2
  im = ImageOps.posterize(im, bits) # posterize on scale
  im = ImageOps.colorize(im, colors['bg'], colors['fg']) # recolor
  # im = im.filter(ImageFilter.SMOOTH)
  im = im.filter(ImageFilter.SHARPEN)
  enhancer = ImageEnhance.Contrast(im)
  im = enhancer.enhance(1.5)
  enhancer = ImageEnhance.Brightness(im)
  im = enhancer.enhance(1.5)

  return im

# warhol machine (cluster) stuff
comm = MPI.COMM_WORLD
rank = comm.rank

if len(sys.argv) == 3:
    WIDTH_SIZE = int(sys.argv[2])

# The parent node loads the image
if (rank == 0):
    fname = sys.argv[1]

    # Load image
    # img = Image.open(fname).convert('L')
    img = Image.open(fname)
    # Converts to numpy array for easy sending
    arr_img = numpy.array(img)
    for child in range(1, 4):
        comm.send(arr_img, dest=child)
else: # The children load images from the comm network
    arr_img = comm.recv(source=0)
    img = Image.fromarray(arr_img)

# Everyone does this part (Image processing)
img = img.convert('L') # grayscale
img = resizeImage(img) # resize
version = random.choice([1,2])
if version == 1:
    img_rand = warholify(img, random.choice(COLORS)) # warhol version 1
else:
    img_rand = warholify_b(img, random.choice(COLORS)) # warhol version 2
img_rand = img_rand.filter(ImageFilter.SMOOTH)


# Then time to aggregate the images
if (rank == 0):
    # We already have one of the images
    img0 = img_rand
    # Receive the other images
    img1a = comm.recv(source=1)
    img1 = Image.fromarray(img1a)
    img2a = comm.recv(source=2)
    img2 = Image.fromarray(img2a)
    img3a = comm.recv(source=3)
    img3 = Image.fromarray(img3a)

    # Aggregate the four images into one
    img = aggregateImages(img0, img1, img2, img3)

    #Save the Warhol Masterpiece!
    img.save('output.jpg')
else: # send result
    arr_img = numpy.array(img_rand)
    comm.send(arr_img, dest=0)
