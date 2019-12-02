# Image compression
#
# You'll need Python 2.7 and must install these packages:
#
#   scipy, numpy
#
# You can run this *only* on PNM images, which the netpbm library is used for.
#
# You can also display a PNM image using the netpbm library as, for example:
#
#   python netpbm.py images/cortex.pnm


import sys, time, netpbm
import numpy as np


# Text at the beginning of the compressed file, to identify it


headerText = 'my compressed image - v1.0'

# creates dictionary containing +/- offset values
# returns dictionary and off set of next value
def initLZWD():
  lzwD = {}
  for i in range(256):
    lzwD[(i,)] = i
  i = 256
  for j in range(256):
    lzwD[(-j,)] = i
    i += 1
  return lzwD,i

# Compress an image

def compress( inputFile, outputFile ):

  # Read the input file into a numpy array of 8-bit values
  #
  # The img.shape is a 3-type with rows,columns,channels, where
  # channels is the number of component in each pixel.  The img.dtype
  # is 'uint8', meaning that each component is an 8-bit unsigned
  # integer.

  img = netpbm.imread( inputFile ).astype('uint8')
  
  # Compress the image
  #
  # REPLACE THIS WITH YOUR OWN CODE TO FILL THE 'outputBytes' ARRAY.
  #
  # Note that single-channel images will have a 'shape' with only two
  # components: the y dimensions and the x dimension.  So you will
  # have to detect this and set the number of channels accordingly.
  # Furthermore, single-channel images must be indexed as img[y,x]
  # instead of img[y,x,1].  You'll need two pieces of similar code:
  # one piece for the single-channel case and one piece for the
  # multi-channel case.

  startTime = time.time()
 
  outputBytes = bytearray()

  # detect shape and set channels accordingly
  if len(img.shape) == 2:
    channels = [img.flatten()]
  elif len(img.shape) == 3:
    channels = [img[:,:,i].flatten() for i in range(img.shape[2])]


  # loop through each channel to encode each individually
  for chnl in channels:
    lzwD,i = initLZWD()

    #initialize counters to keep track of previous value and previous sequence for LZW
    prevP = 0
    prevS = ()
    for p in chnl:
      pDiff = p - prevP
      currS = prevS + (pDiff,)
      # if sequence not in dict, write to stream
      if currS not in lzwD:
        # stop at max 16 bit size -1 = 65535
        if i < 65535:
          lzwD[currS] = i
          i += 1
        # get value that was prevS
        val = lzwD[prevS]
        # encode into bytes
        smallB = val % 256
        bigB = val / 256
        # append bytes to output
        outputBytes.append(bigB)
        outputBytes.append(smallB)
        # reset prevS to new previous sequence
        prevS = (pDiff,)
      # sequence in dict, don't write new sequence, add to existing sequence
      else:
        # onto next sequence
        prevS = currS
      prevP = p
    # finish LZW by encoding end data
    if len(prevS) > 1:
      # same as 'if sequence not in dict'
      val = lzwD[prevS]
      smallB = val % 256
      bigB = val / 256
      outputBytes.append(bigB)
      outputBytes.append(smallB)

    # end flags
    outputBytes.append(255)
    outputBytes.append(255)

  endTime = time.time()

  # Output the bytes
  #
  # Include the 'headerText' to identify the type of file.  Include
  # the rows, columns, channels so that the image shape can be
  # reconstructed.

  outputFile.write( '%s\n'       % headerText )
  outputFile.write( '%d %d %d\n' % (img.shape[0], img.shape[1], len(channels)) )
  outputFile.write( outputBytes )

  # Print information about the compression
  
  inSize  = img.shape[0] * img.shape[1] * len(channels)
  outSize = len(outputBytes)

  sys.stderr.write( 'Input size:         %d bytes\n' % inSize )
  sys.stderr.write( 'Output size:        %d bytes\n' % outSize )
  sys.stderr.write( 'Compression factor: %.2f\n' % (inSize/float(outSize)) )
  sys.stderr.write( 'Compression time:   %.2f seconds\n' % (endTime - startTime) )
  


# Uncompress an image

def uncompress( inputFile, outputFile ):

  # Check that it's a known file

  if inputFile.readline() != headerText + '\n':
    sys.stderr.write( "Input is not in the '%s' format.\n" % headerText )
    sys.exit(1)
    
  # Read the rows, columns, and channels.  

  rows, columns, channels = [ int(x) for x in inputFile.readline().split() ]

  # Read the raw bytes.

  inputBytes = bytearray(inputFile.read())

  # Build the image
  #
  # REPLACE THIS WITH YOUR OWN CODE TO CONVERT THE 'inputBytes' ARRAY INTO AN IMAGE IN 'img'.

  startTime = time.time()

  img = np.empty( [rows,columns,channels], dtype=np.uint8 )

  byteIter = iter(inputBytes)

  for channel in range(channels):
    # initialize counter variable and lzw dictionary
    prevP = 0
    lzwD,i = initLZWD()

    # reverse mapping
    lzwD = {v:k for k,v in lzwD.iteritems()}

    # read sequence from inputBytes and build index to look up in lzw dictionary
    bigB = byteIter.next()
    smallB = byteIter.next()
    lzwI = bigB * 256 + smallB
    # get first sequence
    S = lzwD[lzwI]
    img[0,0,channel] = S[0]
    prevP = S[0]

    x = 0
    y = 1
    # while there are codes to decode
    while x < rows and y < columns:
      try:
        bigB = byteIter.next()
        smallB = byteIter.next()
      except StopIteration:
        print ("no more data in bitstream")
      lzwI = bigB * 256 + smallB
      # check if end of lzwI
      if lzwI == 65535:
        break
      # search for T
      if lzwI in lzwD:
        T = lzwD[lzwI]
      # case when value is encoded as is
      else:
        T = S + (S[0],)
      # write T to the image
      for byte in T:
        decodedP = prevP + byte
        img[x,y,channel] = decodedP
        prevP = decodedP

        y += 1
        if y == columns:
          y = 0
          x += 1
        # stop at image borders to stop overflow
        if (x > rows and y > columns):
          break
      # add S to decode dict with T
      lzwD[i] = S + (T[0],)
      i += 1
      S = T
    # keep iterating until channel has ended
    while lzwI < 65535:
      try:
        bigB = byteIter.next()
        smallB = byteIter.next()
      except StopIteration:
        print ("no more data in bitstream")
        break
      lzwI = bigB * 256 + smallB

  endTime = time.time()

  # Output the image

  netpbm.imsave( outputFile, img )

  sys.stderr.write( 'Uncompression time: %.2f seconds\n' % (endTime - startTime) )

  

  
# The command line is 
#
#   main.py {flag} {input image filename} {output image filename}
#
# where {flag} is one of 'c' or 'u' for compress or uncompress and
# either filename can be '-' for standard input or standard output.


if len(sys.argv) < 4:
  sys.stderr.write( 'Usage: main.py c|u {input image filename} {output image filename}\n' )
  sys.exit(1)

# Get input file
 
if sys.argv[2] == '-':
  inputFile = sys.stdin
else:
  try:
    inputFile = open( sys.argv[2], 'rb' )
  except:
    sys.stderr.write( "Could not open input file '%s'.\n" % sys.argv[2] )
    sys.exit(1)

# Get output file

if sys.argv[3] == '-':
  outputFile = sys.stdout
else:
  try:
    outputFile = open( sys.argv[3], 'wb' )
  except:
    sys.stderr.write( "Could not open output file '%s'.\n" % sys.argv[3] )
    sys.exit(1)

# Run the algorithm

if sys.argv[1] == 'c':
  compress( inputFile, outputFile )
elif sys.argv[1] == 'u':
  uncompress( inputFile, outputFile )
else:
  sys.stderr.write( 'Usage: main.py c|u {input image filename} {output image filename}\n' )
  sys.exit(1)
