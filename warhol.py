#! /usr/bin/env python

from mpi4py import MPI
import PIL
from PIL import Image
import random
import numpy

# picture width used in resizing an image
# tweak this to adjust size of image
WIDTH_SIZE=400

# upper and lower bounds of black and white shades, range 0-255
# tweak these to adjust colors
BLK_UPPER_BOUND=105
WHITE_LOWER_BOUND=145

# color dictionary, fg = foreground, bg = background, og = 'other'ground
COLORS = [
    {'bg' : (255,255,0), 'fg' : (50,9,125), 'og': (118,192,0)},
    {'bg' : (0,122,240), 'fg' : (255,0,112), 'og': (255,255,0)},
    {'bg' : (50,0,130),'fg' : (255,0,0),'og': (243,145,192)},
    {'bg' : (255,126,0),'fg' : (134,48,149),'og': (111,185,248)},
    {'bg' : (255,0,0),'fg' : (35,35,35),'og': (255,255,255)},
    {'bg' : (122,192,0),'fg' : (255,89,0),'og': (250,255,160)},
    {'bg' : (0,114,100),'fg' : (252,0,116),'og': (250,250,230)},
    {'bg' : (250,255,0),'fg' : (254,0,0),'og': (139,198,46)},
    {'bg' : (253,0,118),'fg' : (51,2,126),'og': (255,105,0)}
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


# warhol machine (cluster) stuff
comm = MPI.COMM_WORLD
rank = comm.rank

if (rank == 0):
    img = Image.open('soupa.jpg').convert('L')
    img = resizeImage(img)
    arr_img = numpy.array(img)
    comm.send(arr_img, dest=1)
else:
    arr_img = comm.recv(source=0)
    img = Image.fromarray(arr_img)
    img.save('test.jpg')




  # # Open an image for processing and convert to greyscale
  # img = Image.open('soup.jpg').convert('L')
  # img = resizeImage(img)
  #
  # # Create random colorized vector like images
  # img1 = wharolify(img, random.choice(COLORS))
  # img2 = wharolify(img, random.choice(COLORS))
  # img3 = wharolify(img, random.choice(COLORS))
  # img4 = wharolify(img, random.choice(COLORS))
  #
  # # Aggregate the four images into one
  # img = aggregateImages(img1, img2, img3, img4)
  #
  # # Save the Warhol Masterpiece!
  # img.save('warholed.jpg')
