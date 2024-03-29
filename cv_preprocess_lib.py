####################################################################################################################
###                      *************** Computer Vision / Bioinformatics **************
###                      *** Automatic image normalization and dataset amplification ***
###
### Student: Tiago Filipe dos Santos     Number: 202008971
###
####################################################################################################################

#    All code contained in this script can be used under the term of GNU
#    Affero General Public License.
#
#    Final project for Computer Vision
#
#    Copyright (C) 2021  Tiago F. Santos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#####################################################################################################################

# import libraries
import cv2 as cv
import numpy as np
import pandas as pd

from scipy.spatial import distance
from scipy import fftpack as fft
import matplotlib.pyplot as plt
import seaborn as sns

import sklearn as sk
from sklearn.decomposition import PCA

debug = False

def open_img(img):
    """ opens image """
    return cv.imread(img, )

def show_img(img, title = 'Image'):
    """ shows an image within the same window """
    # copy so images are not destroyed by the text
    img_temp = img.copy()

    # add windows title
    cv.putText(img_temp, title, (30, 20),
                cv.FONT_HERSHEY_PLAIN, 1, (255,118,106))

    if debug: print(title, img.shape)

    # show image
    cv.imshow("Image Aligner", img_temp)
    cv.setWindowProperty("Image Aligner", cv.WND_PROP_TOPMOST, 1)
    cv.waitKey(0)

    pass


def resize_img(img, ratio = 1, dim_target = None, crop = True, debug = False):
    """ resizes an image to a set ratio """
    # check input format
    # img = assure_gray_img(img)

    # if has_color(img):
    #     dim = (np.int(img.shape[0]*racio), np.int(img.shape[1]*racio), img.shape[2])
    # else:
    dim_img = img.shape[0], img.shape[1]
    dim = (np.int(img.shape[1]*ratio), np.int(img.shape[0]*ratio))

    img_resized = cv.resize(img, dim, interpolation = cv.INTER_CUBIC)
    print("img_resized.shape:", img_resized.shape, "ratio", ratio)

    if crop:
        # resized image centroid
        img_cx, img_cy = find_center(img_resized)


        if ratio > 1:
            # original image limits
            min_x, max_x, min_y, max_y = (img_cx - (img.shape[1] // 2),
                                          img_cx + (img.shape[1] // 2),
                                          img_cy - (img.shape[0] // 2),
                                          img_cy + (img.shape[0] // 2))

            # create cropped output
            img_out = img_resized[min_y:max_y, min_x:max_x]
        else:             # original image limits
            min_x, max_x, min_y, max_y = ((img.shape[1] // 2) - img_cx,
                                          (img.shape[1] // 2) + img_cx,
                                          (img.shape[0] // 2) - img_cy,
                                          (img.shape[0] // 2) + img_cy)

            # create frame with proper dimensions
            if len(img.shape) == 3:
                img_out = np.zeros((img.shape[0], img.shape[1], img.shape[2]), dtype='uint8')
            else:
                img_out = np.zeros((img.shape[0], img.shape[1]), dtype='uint8')

            # fill with border color
            img_out[:] = (img_resized[0][0])

            # fill in with centered resized image
            img_out[min_y:min_y+img_resized.shape[0], min_x:min_x+img_resized.shape[1]] = img_resized
    else:
        img_out = img_resized

    # a target dimension is set, rescale again to target dimension
    if dim_target:
        img_out = cv.resize(img_out, dim_target, interpolation = cv.INTER_CUBIC)


    if debug == 'Full': show_img(img_out, 'Resized image')

    return img_out

# create a rotation function
def rotate(img, angle, rot_point = None, debug=False):
    """ rotates an input image """
    # code adapted from https://www.youtube.com/watch?v=oXlwWbU8l2o
    (height, width) = img.shape[:2]
    if rot_point == None :
        rot_point = (width//2, height //2)

    rotMat = cv.getRotationMatrix2D(rot_point, angle, 1)
    dimensions = (width, height)

    img_out = cv.warpAffine(img, rotMat, dimensions, borderMode = cv.BORDER_REPLICATE)

    if debug: show_img(img_out, 'Rotated Image')

    return img_out

def calculate_angle(pt1, pt2):
    """ calculates the angle in degrees from a point to another """
    pt1_x, pt1_y = pt1
    pt2_x, pt2_y = pt2
    angle = np.rad2deg(np.arctan2((pt2_y-pt1_y) , (pt2_x-pt1_x)))

    return angle

def img_center(img):
    """ returns the image centroid """
    return (img.shape[0] // 2, img.shape[1] // 2)

def remove_background(img, background, show = True, video = False, debug = True):
    """ background subtraction for static images or videos
        in images, if the pixel has the same color as the blank picture, sutract the picture """
    # TODO for videos
    if video:
        # README https://docs.opencv.org/4.x/d8/d38/tutorial_bgsegm_bg_subtraction.html
        # cv.createBackgroundSubtractorKNN() and cv.createBackgroundSubtractorKNN() are used to infer background from video
        pass
    # for images if pixel if the same, subtract, else = pixel
    img_out = np.zeros((img.shape[0], img.shape[1]), dtype='uint8')

    for i in range(0,img.shape[0]):
        for j in range(0,img.shape[1]):
            if img[i][j] == background[i][j]:
                if has_color(img):
                    img_out[i][j] = (img[0][0][0], img[0][0][1], img[0][0][2])
                else:
                    img_out[i][j] = 0
            else:
                img_out[i][j] = img[i][j]

    # debug
    if debug : show_img(img_out, "Debug")

    return img_out # this is wrong, rework

def assure_gray_img(img):
    """ returns a grayscale image, converting it, if need be """
    img_gray = img if len(img.shape) == 2 else cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    return img_gray

def contrast_stretching(img, debug = True):
    """ does contrast stretching on a grayscale image """

    # assure the image is in grayscale
    img_gray = assure_gray_img(img)

    # initialize image
    img_out = np.zeros((img.shape[0], img.shape[1]), dtype='uint8')

    # calculate extremes
    min, max = np.min(img_gray), np.max(img_gray)
    delta = max - min

    for i in range(0,img.shape[0]):
        for j in range(0,img.shape[1]):
             img_out[i][j] = np.int(((img_gray[i][j] - min) / delta)*255)

    if debug : show_img(img_out, "Contrast Streching")

    return img_out

def otsu_thresholding(img, debug = True, app = False):
    """ calculates Otsu's threshold after a Gaussian filter

    NOTE: Otsu's thresholding requires grayscale images"""
    # https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html

    blured_img = cv.GaussianBlur(src=img, ksize=(5,5), sigmaX=0)
    value, th_img = cv.threshold(blured_img, thresh = 0, maxval = 255,
                                 type = cv.THRESH_BINARY+cv.THRESH_OTSU)

    if app:   return th_img

    if debug: show_img(th_img, "Otsu's thresholding")

    return value

def binarize_image(img, threshold = None, debug = True):
    """ binarizes an image, i.e., conversion to black and white """
    # NOTE: Otsu's thresholding already provides a binarized image, but for the sake of this exercize...

    # assure the image is in grayscale
    img_gray = assure_gray_img(img)

    # set threshold using Otsu's tresholding
    if threshold is None:
        threshold = otsu_thresholding(img_gray, debug = debug) if threshold is None else threshold
    # NOTE: regular numerical thresholding works better for skull definition (e.g., threshold = 200)

    # initialize BW output
    img_bw = np.zeros((img.shape[0], img.shape[1]), dtype='uint8')

    # for each value above 0, convert to one
    for i in range(0,img.shape[0]):
        for j in range(0,img.shape[1]):
            if img_gray[i][j] > threshold:
                img_bw[i][j] = 255

    if debug:
        # test remove_background.
        # Note: background should be a image taken by the sensor when no object is on sight
        # img2 = remove_background(img_gray, img_bw, debug = debug)

        show_img(img_bw, 'Binarized image')

    return img_bw

def denoise_img(img, radius = 13, debug = True):
    """ denoises an image through median passthrough """
    # cv.imshow('')
    img_out = cv.medianBlur(img, ksize=radius)

    if debug:
        show_img(img_out, 'Denoised image')

    return img_out

def find_boundaries(img, threshold = 125, debug = True):
    """ finds image boundaries horizontal and vertical boundaries """
    min_x, max_x, min_y, max_y = img.shape[1], 0, img.shape[0], 0

    for i in range(0,img.shape[0]):
        for j in range(0,img.shape[1]):
            if img[i][j] > threshold:
                if j < min_x: min_x = j
                if j > max_x: max_x = j
                if i < min_y: min_y = i
                if i > max_y: max_y = i

    boundaries = (min_x, max_x, min_y, max_y)

    if debug : print(boundaries)

    return boundaries

def find_center(img):
    """ find image centroid """
    return img.shape[1] // 2, img.shape[0] // 2

def find_centering_vector(img, boundaries, debug = True):
    """ finds the offset of a segment in relation to the
    center of an image, and returns the centering vector """

    # pass boundaries and vector to a more manageable format
    # print("Boundaries:", boundaries)
    min_x, max_x, min_y, max_y = boundaries

    img_cx, img_cy = find_center(img)
    seg_cx, seg_cy = min_x + (max_x - min_x) // 2, min_y + (max_y - min_y) // 2

    vector = (img_cx - seg_cx, img_cy - seg_cy)

    if debug : print("Vector:", vector)

    return vector

def get_segment_poss(img, threshold = None, background = None, preprocessed = False, c_vector = None, debug = True):
    """ returns a list of tuples of each pixel in the segment """
    # based on:
        # https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=8540825
        # https://stackoverflow.com/questions/46109338/find-orientation-of-object-using-pca

    ####### preprocessing steps ######
    # convert image to grayscale for easier analysis
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    if background is not None:
        img = remove_background(img, background)
        cv.imshow('Object', remove_background(img_gray, img_bw)) # change img_bw in the end of debugging
        cv.waitKey(0)

    if not preprocessed:
        # segment image by binarization
        img_bw = binarize_image(img_gray, threshold, debug = debug)

        # denoise image
        img_denoised = denoise_img(img_bw)

        # find image center
        centered_img, c_vector = center_img(img_denoised, debug = debug)

        # if centered: # some centered images have issues. investigate.
        #     # fill the shape of the object
        #     img_filled = fill_obj(centered_img, debug = debug)
        # else:
        #     img_filled = fill_obj(img_denoised, debug = debug)

        # fill in gaps
        img_filled = fill_obj(centered_img, debug = debug)
    else:
        img_filled = img_gray.copy()

    # convert black and white to coordinates for orientation PCA
    obj_poss = []

    # print(img_bw.shape)
    # print(img_filled.shape)

    for i in range(0, img_filled.shape[0]):
        for j in range(0, img_filled.shape[1]):
            if img_filled[i][j] > 0:
                obj_poss.append([i,j])

    # print(obj_poss)

    return obj_poss, c_vector

def has_color(img):
    """" check if the image has color or is grayscale """
    color = True if len(img.shape) > 2 else  False

    return color


def move_segment(img, boundaries = None, vector = None, output_shape = None, debug = True):
    """ move one segment of the image to another segment

    Usage:
    move_segment(img, boundaries, vector)

    Where:
    img        - a bidemensional numpy matrix
    boundaries - a list or tuple with the format min_x, max_x, min_y, max_y
    vector     - a list or tuple with the format x, y
    """

    # pass boundaries and vector to a more manageable format
    if boundaries is None:
        min_x, max_x, min_y, max_y = 0, img.shape[1], 0, img.shape[0]
    else:
        min_x, max_x, min_y, max_y = boundaries
        channels = 0
    vector_x, vector_y = vector

    # translate image
    if has_color(img):
        # assure the canvas shape is bigger even when the original when vectors are negative
        canvas = np.zeros((img.shape[0]+np.abs(vector_y),
                           img.shape[1]+np.abs(vector_x),
                           img.shape[2]), dtype='uint8')
        # color with border color
        canvas[:] = (img[0][0][0], img[0][0][1], img[0][0][2])

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                for c in range(img.shape[2]):
                    canvas[y + vector_y][x + vector_x][c] = img[y][x][c]

    else:
        canvas = np.zeros((img.shape[0]+np.abs(vector_y),
                           img.shape[1]+np.abs(vector_x)),
                           dtype='uint8')
        # color with border color
        canvas[:] = (img[0][0])

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                canvas[y + vector_y][x + vector_x] = img[y][x]

    # crop image to original shape
    img_out = canvas[:img.shape[0], :img.shape[1]]

    # debug
    if debug : show_img(img_out, "Moved segment")

    return img_out

def center_img(img, debug = True):
    """ centers an object in a grayscale image """
    boundaries = find_boundaries(img, debug = False)
    c_vector = find_centering_vector(img, boundaries, debug = False)
    # NOTE previous steps could have been done with x,y, radius = cv.minEnclosingCircle()

    c_img = move_segment(img, boundaries, c_vector, debug = debug)

    return c_img, c_vector

def preprocess_img(img, threshold = 20, debug = True):
    """
    preprocessing pipeline, including contrast stretching, binarizarion,
    denoising, and find image centroid
    """
    # pre-process
    # contrast stretching
    img_stretch = contrast_stretching(img, debug = debug)

    # segment image by binarization
    img_bw = binarize_image(img_stretch, threshold = threshold, debug = debug)

    # denoise image
    img_denoised = denoise_img(img_bw, debug = debug)

    # find image center
    centered_img, c_vector = center_img(img_denoised, debug = debug)

    return centered_img

def find_best_contour(img, preprocessed = False, debug = True, app = False):
    """ returns the external countour of an object within a picture """
    # preprocess image
    if not preprocessed :
        centered_img = preprocess_img(img, debug = False)
    else:
        centered_img = img

    all_contours = cv.findContours(assure_gray_img(centered_img), cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    contour_img = cv.drawContours(cv.cvtColor(centered_img ,cv.COLOR_GRAY2RGB), all_contours[0][0], -1, (0,255,0), 3)

    # debug
    if debug :
        if not app:
            show_img(centered_img, 'find_best_contour')
        # print(all_contours)
        clist = []
        for i in range(len(all_contours[0])):
            clist.append(len(all_contours[0][i]))
        print(clist, np.argmax(clist), np.max(clist))

        # if debug or not app:
        show_img(contour_img, "Contour drawn")

    if app : return contour_img

    return all_contours[0][0]

def fill_obj(img, contours = -1, debug = True):
    """ fills object found """
    if contours == -1:
        contours, _ = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    img_filled = cv.fillPoly(img, [contours[0]], color=(255,0,0))

    # debug
    if debug : show_img(img_filled, 'Filled Image')

    return img_filled


def needs_rotation(template, img, threshold=125):
    """ returns True if the target image needs a 90 flip """
    # get objects boundaries
    # cv.imshow("Template boundary", assure_gray_img(template)); cv.waitKey(0)
    t_bound = find_boundaries(assure_gray_img(template), threshold)
    # cv.imshow("Image boundary", assure_gray_img(img)); cv.waitKey(0)
    i_bound = find_boundaries(assure_gray_img(img), threshold)

    # get object lengths in each axis
    t_x_len = (t_bound[3] - t_bound[2])
    t_y_len = (t_bound[1] - t_bound[0])
    i_x_len = (i_bound[3] - i_bound[2])
    i_y_len = (i_bound[1] - i_bound[0])

    # check horizontality
    temp_horizontal = 1 if ( t_x_len / t_y_len ) > 1 else 0
    img_horizontal  = 1 if ( i_x_len / i_y_len ) > 1 else 0

    needs_90_rot = temp_horizontal - img_horizontal

    return needs_90_rot

def calculate_gradients(img, debug = False):
    """ calculates average horizontal and vertical intensities of the image
    and compares intensity across quadrants to get the right orientation """

    # convert to grayscale
    img_gray = assure_gray_img(img)

    # get average for each row and column
    ravgs = np.float32(cv.reduce(img_gray, 1, cv.REDUCE_AVG, cv.CV_32S))
    cavgs = np.float32(cv.reduce(img_gray, 0, cv.REDUCE_AVG, cv.CV_32S))

    # print(ravgs.T)

    # get gradients
    rdiffs = np.diff(ravgs, axis=0)
    cdiffs = np.diff(cavgs, axis=1).T

    # calcute difference between sections
    vseg   = np.average(ravgs[:ravgs.shape[0]//2])
    vseg_2 = np.average(ravgs[ravgs.shape[0]//2:])
    hseg   = np.average(cavgs.T[:cavgs.shape[1]//2])
    hseg_2 = np.average(cavgs.T[cavgs.shape[1]//2:])

    # calcute difference between sections
    hgrad   = "left" if hseg >= hseg_2 else "right"
    vgrad   = "up"   if vseg >= vseg_2 else "down"

    if debug:
        print(hgrad, vgrad)
        print(hseg, hseg_2, vseg, vseg_2)

    return hgrad, vgrad

def orientate(img, template, debug = False):
    """ determines if the image has the right orientation based on image quandrants intensity """
    img_h, img_v = calculate_gradients(assure_gray_img(img), debug = debug) # FIXME need to add image recenterint to preprocessing
    img2_h, img2_v = calculate_gradients(assure_gray_img(template), debug = debug)
    if img_h != img2_h and img_v != img2_v:
        img_rotated = rotate(img, angle = 180, rot_point = None, debug = False)

        if debug:
            print("Image reoriented")
            show_img(img_rotated, title='Image Reoriented')
    else:
        img_rotated = img.copy()

    return img_rotated

def find_img_quadrants(img):
    """ returns an ordered list of image quadrants, sorted by their proportions """
    # find image center
    cx, cy = find_center(img)

    # split quadrants by image center
    quadrants = []

    quadrants.append(img[:cy, cx:])    # quad I
    quadrants.append(img[:cy, :cx])    # quad II
    quadrants.append(img[cy:, :cx])    # quad III
    quadrants.append(img[cy:, cx:])    # quad IV

    # find quadrant proportions
    prop_list = []

    for quadrant in quadrants:
        prop_list.append(np.round(get_proportion(quadrant, threshold = 0), decimals = 3))
        # NOTE round proportion to avoid pixelwise errors
        # centered images have all the same proporttions
    if debug : print(prop_list)

    # calculate proportions
    prop_list_order = [1, 2, 3, 4]

    for i in range(0, 3) :
        for j in range(1, 4) :
            if prop_list[i] > prop_list[j]:
                temp = prop_list[i]
                prop_list[i] = prop_list[j]
                prop_list[j] = temp

    if debug: print(prop_list_order)

    return prop_list, prop_list_order

def find_orientation(img, threshold = None, preprocessed = False, c_vector = None, debug = False):
    """ finds the orientation given an image """

    # get segment raster positions
    obj_pos_matrix, c_vector = get_segment_poss(img, threshold = threshold, preprocessed = preprocessed, c_vector = c_vector, debug = debug)

    # make PCA on the image to get vectors of major change (PCA's eigenvectors)
    pca = PCA(n_components=2)
    pca.fit(obj_pos_matrix)

    # assign PC1 eigenvector values
    # print(pca.components_)
    x, y = pca.components_[0,0], pca.components_[1,0] # first value of each row is PC1
    # print(pca.components_)

    # debug string
    if debug : print(x,y, -y/x) # for a 45º rotation, x and y should be the same

    # maths reference https://stats.stackexchange.com/questions/239959/how-to-obtain-the-angle-of-rotation-produced-by-a-pca-on-a-2d-dataset
    rot_rad = -np.arctan(y/x)
    rot_deg = np.round(90 - (rot_rad/(np.pi*2))*360, decimals=0)
    if debug : print(f"Rotation angle is:\t {np.int(rot_deg)}º") # sometimes it finds the perpendicular angle

    return rot_deg, c_vector

def get_proportion(img, threshold = 125, debug = False):
    """ gets the proportion of pixels above a threshold in a rectangular matrix """
    # inialize
    count = 0

    img = fill_obj(preprocess_img(img, threshold = threshold, debug = False), debug = False)

    total = img.shape[0] * img.shape[1]

    # get proportions
    for x in range(img.shape[0]):
        for y in range(img.shape[1]):
            if img[x][y] > threshold:
                count += 1

    prop = count / total

    if debug == 'Full':
        print("Segment proportion", prop)

    return prop

def get_ratio(template, img, threshold = 20, debug = True):
    """ returns object proportion between two images """
    # FIXME this code only works with good base images. Needs to be inserted in pipeline, after boundary detection
    prop_template = get_proportion(template, threshold, debug = debug)
    prop_img = get_proportion(img, threshold, debug = debug)

    if debug:
        print("Proportion template:", prop_template)
        print("Proportion image", prop_img)

    return (prop_template ** (1/2)) / (prop_img ** (1/2))


def find_n_axis(img, contour = None, center = None, debug = False):
    """ returns the number of axis of simmetry of the image """
    # NOTE check also http://www.cse.psu.edu/~yul11/CourseFall2006_files/loy_eccv2006.pdf
    #      code in https://github.com/dramenti/symmetry

    # initialize
    if contour is None :
        contour = find_best_contour(img, debug = False)
        if debug :
            print("No contour passed")
            print(contour)
    else:
        if debug :
            print("Contour passed\n", contour)
        else:
            pass

    # create image
    # centered_img = preprocess_img(img, debug = False)
    # contour_img = cv.drawContours(cv.cvtColor(centered_img ,cv.COLOR_GRAY2RGB), contour, -1, (0,255,0), 3)
    contour_img = cv.drawContours(cv.cvtColor(img, cv.COLOR_GRAY2BGR), contour, -1, (0,255,0), 3)

    # set center
    if center :
        print(center)
        cx, cy = center
    else:
        cx, cy = center = find_center(img)

    # calculate list with distances to each external countour point
    dist_list = []
    angle_list = []
    for edge in contour:
        # print(center, edge)
        dist_list.append(distance.euclidean(center, *edge))
        angle_list.append(calculate_angle(center, *edge))
        lists_merged = zip(center, edge)
        # print(lists_merged)
    sort_angles = sorted(zip(angle_list, dist_list), key=lambda x: x[0])

    # sort list by angle
    dist_list = []
    angle_list = []
    for angle, dist in sort_angles:
        dist_list.append(dist)
        angle_list.append(angle)
        lists_merged = zip(center, edge)

    # calculate mean angle step
    angle_1 = angle_list[1:]
    angle_2 = angle_list[:-1]
    angle_diffs = [angle_1 - angle_2 for angle_1, angle_2 in zip(angle_1, angle_2)]
    mean_angle = np.mean(angle_diffs)

    # Fourier transform the distance versus angle function to get the period of the contour
    # based on https://scipy-lectures.org/intro/scipy/auto_examples/solutions/plot_periodicity_finder.html

    # calculate Fourier transform and FT frequencies
    ft = fft.fft(dist_list, axis = 0)
    ft_freqs = fft.fftfreq(n = len(dist_list), d = mean_angle)

    # fix for div by 0 in ft_periods
    ft_freqs_2 = np.where(0, 1e-20, ft_freqs)

    # calculate function period
    ft_periods = 1 / ft_freqs_2

    # crop negative angles and first value since it has border condition bias in their calculations
    # print(ft_periods)
    ft_cropped = ft[1:len(ft)//2]
    ft_periods_cropped = ft_periods[1:len(ft)//2]

    # get the angular period
    prob_period = ft_periods_cropped[np.argmax(np.abs(ft_cropped))]
    print("Angular Period", prob_period)

    # get number of simmetry angles
    n_axis = np.int(360/prob_period)
    n_axis = n_axis // 2 if n_axis % 2 == 0 else n_axis

    print("Probable number of axis:", n_axis)

    if debug:
        print("Mean angle step:", mean_angle)
        #     print(dist_list)
        #     print(angle_list)
        # print("Sorted_angles list\n\n" , sort_angles)

        # debug period
        # print("length Periods", len(ft_periods), "Max Periods", max(ft_periods), ft_periods[np.argmax(ft)])

        # pretify plots
        sns.set_theme()
        plt.rcParams["figure.figsize"] = (12, 6.75)
        plt.rcParams["axes.titlesize"] = "large"
        plt.rcParams["axes.labelsize"] = "medium"
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['font.sans-serif'] = ['Times New Roman']

        # get most relevant period for FFT frequencies list
        fig = plt.figure()
        fig.set_tight_layout(tight=True)

        # set subplots
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        # countour distance plot
        s_contour = np.vstack((x.reshape(-1,2) for x in contour)) # https://stackoverflow.com/questions/52206407/simplify-getting-coordinates-from-cv2-findcontours
        # print(s_contour)
        ax1.plot(angle_list, dist_list, marker='o')
        ax1.set(xlabel = 'Point in Countour List', ylabel = 'Euclidean Distance',
                title = 'Countour Distance to Center Function')

        # get most relevant period for FFT frequencies list
        ax2.plot(ft_periods, abs(ft), marker='o')
        ax2.set(xlim = (0, 360),
                xlabel = 'Period (degrees)', ylabel = 'Power',
                title = 'Relative Importance of Each Fourier Period')
        plt.show()

    cv.putText(contour_img, "  Image has a period of aprox. "+str(np.round(prob_period))+", which suggests "+ str(n_axis)+" axis.", (50, 50), cv.FONT_HERSHEY_PLAIN, 1, (255,118,106))
    cv.imshow("Periodicity Analysis", contour_img.copy())

    return n_axis, contour_img
