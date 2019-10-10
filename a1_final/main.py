# Image manipulation
#
# You'll need Python 2.7 and must install these packages:
#
#   numpy, PyOpenGL, Pillow
#
# Note that file loading and saving (with 'l' and 's') do not work on
# Mac OSX, so you will have to change 'imgFilename' below, instead, if
# you want to work with different images.
#
# Note that images, when loaded, are converted to the YCbCr
# colourspace, and that you should manipulate only the Y component of
# each pixel when doing intensity changes.

import sys
import os
import numpy
#from numpy import cumsum
import math


try:  # Pillow
    from PIL import Image
except:
    print 'Error: Pillow has not been installed.'
    sys.exit(0)

try: # PyOpenGL
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    print 'Error: PyOpenGL has not been installed.'
    sys.exit(0)



# Globals

windowWidth = 600 # window dimensions
windowHeight =  800

localHistoRadius = 5  # distance within which to apply local histogram equalization



# Current image

imgDir      = 'images'
imgFilename = 'mandrill.png'

currentImage = Image.open( os.path.join( imgDir, imgFilename ) ).convert( 'YCbCr' ).transpose( Image.FLIP_TOP_BOTTOM )
tempImage    = None



# File dialog (doesn't work on Mac OSX)

if sys.platform != 'darwin':
  import Tkinter, tkFileDialog
  root = Tkinter.Tk()
  root.withdraw()

def applyRotation(degrees):
  width = currentImage.size[0]
  height = currentImage.size[1]

  box = (0, 0, width, height)
  region = currentImage.crop(box)
  region = region.transpose(Image.ROTATE_90)
  currentImage.paste(region, box)
  
  


  #currentImage.save("output.png", "JPEG")

# Apply brightness and contrast to tempImage and store in
# currentImage.  The brightness and constrast changes are always made
# on tempImage, which stores the image when the left mouse button was
# first pressed, and are stored in currentImage, so that the user can
# see the changes immediately.  As long as left mouse button is held
# down, tempImage will not change.

def applyBrightnessAndContrast( brightness, contrast ):

    width  = currentImage.size[0]
    height = currentImage.size[1]

    srcPixels = tempImage.load()
    dstPixels = currentImage.load()

    #flatten image to 1D array
    old = numpy.zeros((width,height))
    for x in range(width):
        for y in range(height):
            old[x,y] = srcPixels[x,y][0]
    flat = old.flatten()
    middleVal = (max(flat)+min(flat))/2

    for x in range(0,width):
        for y in range(0,height):
            #record current pixel data
            src = srcPixels[x,y]

            #adjust brightness by extracting pixel information, 
            newVal = ((src[0] - middleVal)*contrast)+middleVal         
            newVal += brightness
                        
            #apply new pixel values to destination            
            dstPixels[x,y] = (int(newVal),src[1],src[2])

    print 'adjust brightness = %f, contrast = %f' % (brightness,contrast)

# Perform local histogram equalization on the current image using the given radius.

def getNbr(pixels,w,h,x,y,radius):
    neighbours = []
    
    for i in range(-radius,radius+1):
        for j in range (-radius,radius+1):
            y2 = y+i
            x2 = x+j
            if x2>=w:
                x2 = w-1
            if y2>=h:
                y2 = h-1
            if x2<0:
                x2 = 0
            if y2<0:
                y2 = 0
            neighbours.append(pixels[x2,y2])
        return numpy.array(neighbours)
    
    
def performHistoEqualization(radius):
    
    
    pixels = currentImage.load() 
    width  = currentImage.size[0]
    height = currentImage.size[1]

    
#for each pixel, get neighbours, then get neighbours that are less that or equal to original pixel
#min 16 max 235  
    newY = numpy.zeros((width,height))
    
    old_y = numpy.zeros((width,height))
    for x in range(width):
        for y in range(height):
            old_y[x,y] = pixels[x,y][0]
    
    for x in range(width):
        for y in range(height):
            val = old_y[x,y]
            
            neighbours = getNbr(old_y,width,height,x,y,radius)
            
            flat = neighbours.flatten()
            #find values that are less than or equal to and put them in new array
            newVals = []
                
            newVals = flat <= val
            
            c = sum(newVals)
            c_max = len(flat)
            
            finalVal = 16 + 219 * c / c_max + 1
            
            newY[x,y] = finalVal
            
    for x in range(width):
        for y in range(height):
            pix = pixels[x,y]
            pixels[x,y] = (newY[x,y],) + pix[1:]

    print 'perform local histogram equalization with radius %d' % radius



# Scale the tempImage by the given factor and store it in
# currentImage.  Use backward projection.  This is called when the
# mouse is moved with the right button held down.
            

def scaleImage( factor ):

    width  = currentImage.size[0]
    height = currentImage.size[1]

    srcPixels = tempImage.load()
    dstPixels = currentImage.load()

    # YOUR CODE HERE
    #create inverse factor for backprojection equation
    inverse = 1/factor
    
    #iterate through pixels
    for x in range(width):
        for y in range(height):
            #get new coords
            x2 = x * inverse
            y2 = y * inverse
            
            #handle out of bounds and set new coords
            if x2 > width or y2 > height:
                dstPixels[x,y] = (0,0,0)
            else:
                dstPixels[x,y] = srcPixels[x2,y2]
    
    
    
    print 'scale image by %f' % factor

  

# Set up the display and draw the current image

def display():

  # Clear window

  glClearColor ( 1, 1, 1, 0 )
  glClear( GL_COLOR_BUFFER_BIT )

  # rebuild the image

  img = currentImage.convert( 'RGB' )

  width  = img.size[0]
  height = img.size[1]

  # Find where to position lower-left corner of image

  baseX = (windowWidth-width)/2
  baseY = (windowHeight-height)/2

  glWindowPos2i( baseX, baseY )

  # Get pixels and draw

  imageData = numpy.array( list( img.getdata() ), numpy.uint8 )

  glDrawPixels( width, height, GL_RGB, GL_UNSIGNED_BYTE, imageData )

  glutSwapBuffers()


  
# Handle keyboard input

def keyboard( key, x, y ):

  global localHistoRadius

  if key == '\033': # ESC = exit
    sys.exit(0)

  elif key == 'l':
    if sys.platform != 'darwin':
      path = tkFileDialog.askopenfilename( initialdir = imgDir )
      if path:
        loadImage( path )

  elif key == 's':
    if sys.platform != 'darwin':
      outputPath = tkFileDialog.asksaveasfilename( initialdir = '.' )
      if outputPath:
        saveImage( outputPath )

  elif key == 'h':
    performHistoEqualization( localHistoRadius )

  elif key in ['+','=']:
    localHistoRadius = localHistoRadius + 1
    print 'radius =', localHistoRadius

  elif key in ['-','_']:
    localHistoRadius = localHistoRadius - 1
    if localHistoRadius < 1:
      localHistoRadius = 1
    print 'radius =', localHistoRadius

  elif key in ['r']:
    applyRotation(45)
    print 'Image rotated'

  else:
    print 'key =', key    # DO NOT REMOVE THIS LINE.  It will be used during automated marking.

  glutPostRedisplay()



# Load and save images.
#
# Modify these to load to the current image and to save the current image.
#
# DO NOT CHANGE THE NAMES OR ARGUMENT LISTS OF THESE FUNCTIONS, as
# they will be used in automated marking.


def loadImage( path ):

  global currentImage

  currentImage = Image.open( path ).convert( 'YCbCr' ).transpose( Image.FLIP_TOP_BOTTOM )


def saveImage( path ):

  global currentImage

  currentImage.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB').save("output", "png")


# Handle window reshape


def reshape( newWidth, newHeight ):

  global windowWidth, windowHeight

  windowWidth  = newWidth
  windowHeight = newHeight

  glutPostRedisplay()



# Mouse state on initial click

button = None
initX = 0
initY = 0



# Handle mouse click/release

def mouse( btn, state, x, y ):

  global button, initX, initY, tempImage

  if state == GLUT_DOWN:
    tempImage = currentImage.copy()
    button = btn
    initX = x
    initY = y
  elif state == GLUT_UP:
    tempImage = None
    button = None

  glutPostRedisplay()

  

# Handle mouse motion

def motion( x, y ):

  if button == GLUT_LEFT_BUTTON:

    diffX = x - initX
    diffY = y - initY

    applyBrightnessAndContrast( 255 * diffX/float(windowWidth), 1 + diffY/float(windowHeight) )

  elif button == GLUT_RIGHT_BUTTON:

    initPosX = initX - float(windowWidth)/2.0
    initPosY = initY - float(windowHeight)/2.0
    initDist = math.sqrt( initPosX*initPosX + initPosY*initPosY )
    if initDist == 0:
      initDist = 1

    newPosX = x - float(windowWidth)/2.0
    newPosY = y - float(windowHeight)/2.0
    newDist = math.sqrt( newPosX*newPosX + newPosY*newPosY )

    scaleImage( newDist / initDist )

  glutPostRedisplay()
  


# Run OpenGL

glutInit()
glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB )
glutInitWindowSize( windowWidth, windowHeight )
glutInitWindowPosition( 50, 50 )

glutCreateWindow( 'imaging' )

glutDisplayFunc( display )
glutKeyboardFunc( keyboard )
glutReshapeFunc( reshape )
glutMouseFunc( mouse )
glutMotionFunc( motion )

glutMainLoop()
