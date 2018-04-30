
# coding: utf-8

# # Industrial Defect Inspection with image segmentation

# In order to satisfy customers' needs, companies have to guarantee the quality of their products, which can often be achieved only by inspection of the finished product. Automatic visual defect detection has the potential to reduce the cost of quality assurance significantly.

# ## Data description

# [`29th Annual Symposium of the German Association for Pattern Recognition, Weakly Supervised Learning for Industrial Optical Inspection, 2007.`](http://resources.mpi-inf.mpg.de/conferences/dagm/2007/prizes.html)

# This dataset is artificially generated, but similar to real world problems. It consists of multiple data sets, each consisting of 1000 images showing the background texture without defects, and of 150 images with one labeled defect each on the background texture. The images in a single data set are very similar, but each data set is generated by a different texture model and defect model.
# 
# Not all deviations from the texture are necessarily defects. The algorithm will need to use the weak labels provided during the training phase to learn the properties that characterize a defect.
# 
# Below are sample images from 6 data sets. In these examples, defects are weakly labeled by a surrounding ellipse, shown in red. 

# In[1]:


from IPython.display import Image
import os
get_ipython().magic('matplotlib inline')
Image('./userdata/WeaklySpervisedLearningforIndustrialOpticalInspection.jpg')


# ### labeling data

# Defect exists inside an image was bounded with an ellipse. The ellipse-parameters are provided in a separate .txt-file with a format as shown below. 

# [filename] \t \n
# [semi-major axis] \t [semi-minor axis] \t [rotation angle] \t
# [x-position of the centre of the ellipsoid] \t [y-position of the centre of the ellipsoid] \n
# [filename] \t ... 

# In[2]:


get_ipython().system("cat '/data/examples/NV_public_defects/Class1_def/labels.txt'")


# ## Data Preprocessing/Exploration/Inspection



import matplotlib.pyplot as plt
get_ipython().magic('matplotlib inline')
get_ipython().system(' pip install --user xmltodict')



from coslib.Plot import plot_ellipse_seg_test
d_dataset = "/data/examples/NV_public_defects/"
plot_ellipse_seg_test(d_dataset + '/Class1_def/1.png')



plot_ellipse_seg_test(d_dataset + '/Class2_def/1.png')

plot_ellipse_seg_test(d_dataset + '/Class3_def/1.png')

plot_ellipse_seg_test(d_dataset + '/Class4_def/3.png')

plot_ellipse_seg_test(d_dataset + '/Class5_def/1.png')

plot_ellipse_seg_test(d_dataset + '/Class6_def/50.png')



from coslib.DataIO import load_images_masks
X, y = load_images_masks(d_dataset + '/Class1_def/', img_type='png', img_format='gray', resize=(512, 512), ellipse=True)


plt.imshow(X[0,:,:,0], cmap='gray')


plt.imshow(y[0,:,:,0], cmap='gray')


import sklearn


sklearn.__version__


from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)



# ## Unet - Fully Convolutional Neuralnetwork

# The u-net is convolutional network architecture for fast and precise segmentation of images. Up to now it has outperformed the prior best method (a sliding-window convolutional network) on the ISBI challenge for segmentation of neuronal structures in electron microscopic stacks. It has won the Grand Challenge for Computer-Automated Detection of Caries in Bitewing Radiography at ISBI 2015, and it has won the Cell Tracking Challenge at ISBI 2015 on the two most challenging transmitted light microscopy categories (Phase contrast and DIC microscopy) by a large margin.


Image('./userdata/Unet-model.jpg')

img_rows = 512
img_cols = 512



from keras.models import Model
from keras.layers import Input, merge, Conv2D, MaxPooling2D, UpSampling2D,Lambda, Conv2DTranspose, concatenate
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, LearningRateScheduler
from keras import backend as K
from scipy.ndimage.measurements import label
import time
### Defining a small Unet
### Smaller Unet defined so it fits in memory

def get_small_unet():
    inputs = Input((img_rows, img_cols,1))
    inputs_norm = Lambda(lambda x: x/127.5 - 1.)
    conv1 = Conv2D(8, (3, 3), activation='relu', padding='same')(inputs)
    conv1 = Conv2D(8, (3, 3), activation='relu', padding='same')(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = Conv2D(16, (3, 3), activation='relu', padding='same')(pool1)
    conv2 = Conv2D(16, (3, 3), activation='relu', padding='same')(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = Conv2D(32, (3, 3), activation='relu', padding='same')(pool2)
    conv3 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = Conv2D(64, (3, 3), activation='relu', padding='same')(pool3)
    conv4 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = Conv2D(128, (3, 3), activation='relu', padding='same')(pool4)
    conv5 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv5)

    up6 = concatenate([Conv2DTranspose(64, kernel_size=(2, 2), strides=(2, 2), padding='same')(conv5), conv4], axis=3)
    conv6 = Conv2D(64, (3, 3), activation='relu', padding='same')(up6)
    conv6 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv6)

    up7 = concatenate([Conv2DTranspose(32, kernel_size=(2, 2), strides=(2, 2), padding='same')(conv6), conv3], axis=3)
    conv7 = Conv2D(32, (3, 3), activation='relu', padding='same')(up7)
    conv7 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv7)

    up8 = concatenate([Conv2DTranspose(16, kernel_size=(2, 2), strides=(2, 2), padding='same')(conv7), conv2], axis=3)
    conv8 = Conv2D(16, (3, 3), activation='relu', padding='same')(up8)
    conv8 = Conv2D(16, (3, 3), activation='relu', padding='same')(conv8)

    up9 = concatenate([Conv2DTranspose(8, kernel_size=(2, 2), strides=(2, 2), padding='same')(conv8), conv1], axis=3)
    conv9 = Conv2D(8, (3, 3), activation='relu', padding='same')(up9)
    conv9 = Conv2D(8, (3, 3), activation='relu', padding='same')(conv9)

    conv10 = Conv2D(1, (1, 1), activation='sigmoid')(conv9)

    model = Model(inputs=inputs, outputs=conv10)

    
    return model



model = get_small_unet()

### IOU or dice coeff calculation
def IOU_calc(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    
    return 2*(intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def IOU_calc_loss(y_true, y_pred):
    return -IOU_calc(y_true, y_pred)

smooth = 1.
model.compile(optimizer=Adam(lr=1e-4), loss=IOU_calc_loss, metrics=[IOU_calc])
history = model.fit(X_train, y_train, batch_size=10, epochs=50, verbose=1, validation_split=0.1)


# ## Learning curves
plt.figure(figsize=(20, 5))
plt.plot(model.history.history['loss'], label='Train loss')
plt.plot(model.history.history['val_loss'], label='Val loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()


plt.figure(figsize=(20, 5))
plt.plot(model.history.history['IOU_calc'], label='Train IOU')
plt.plot(model.history.history['val_IOU_calc'], label='Val IOU')
plt.xlabel('Epochs')
plt.ylabel('IOU')
plt.legend()


# ## Predict on testing data


predict = model.predict(X_test)


import numpy as np
import cv2
def predict_evaluation(pred, image, label):
    '''
    '''
    # transform gray image to rgb
    img = np.array(image, np.uint8)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    # scale pred and mask's pixel range to 0~255
    im_label = np.array(255*label, dtype=np.uint8)
    im_pred = np.array(255*pred, dtype=np.uint8)
    
    # transform both of them to rgb
    rgb_label = cv2.cvtColor(im_label, cv2.COLOR_GRAY2RGB)
    rgb_pred = cv2.cvtColor(im_pred, cv2.COLOR_GRAY2RGB)
    
    rgb_label[:,:,1:3] = 0*rgb_label[:,:,1:2]
    rgb_pred[:,:,0] = 0*rgb_pred[:,:,0]
    rgb_pred[:,:,2] = 0*rgb_pred[:,:,2]
    
    img_pred = cv2.addWeighted(rgb_img, 1, rgb_pred, 0.3, 0)
    img_label = cv2.addWeighted(rgb_img, 1, rgb_label, 0.3, 0)
    
    plt.figure(figsize=(10, 10))
    
    plt.subplot(1,3,1)
    plt.imshow(rgb_img)
    plt.title('Original image')
    plt.axis('off')
    plt.subplot(1,3,2)
    plt.imshow(img_pred)
    plt.title('Prediction')
    plt.axis('off')
    plt.subplot(1,3,3)
    plt.imshow(img_label)
    plt.title('Ground truth')
    plt.axis('off')


predict_evaluation(predict[0,:,:,0], X_test[0,:,:,0], y_test[0,:,:,0])

predict_evaluation(predict[1,:,:,0], X_test[1,:,:,0], y_test[1,:,:,0])

predict_evaluation(predict[2,:,:,0], X_test[2,:,:,0], y_test[2,:,:,0])


predict_evaluation(predict[3,:,:,0], X_test[3,:,:,0], y_test[3,:,:,0])

predict_evaluation(predict[4,:,:,0], X_test[4,:,:,0], y_test[4,:,:,0])

predict_evaluation(predict[5,:,:,0], X_test[5,:,:,0], y_test[5,:,:,0])

predict_evaluation(predict[6,:,:,0], X_test[6,:,:,0], y_test[6,:,:,0])


predict_evaluation(predict[7,:,:,0], X_test[7,:,:,0], y_test[7,:,:,0])


predict_evaluation(predict[8,:,:,0], X_test[8,:,:,0], y_test[8,:,:,0])

predict_evaluation(predict[9,:,:,0], X_test[9,:,:,0], y_test[9,:,:,0])


# ## Save model for later use




model_json_string = model.to_json()




with open('./userdata/model.json', 'w') as f:
    f.write(model_json_string)




model.save_weights('./userdata/model.h5')



get_ipython().system('ls ./userdata/')



from coslib.ModelIO import convert_keras_to_pb


# In[51]:


convert_keras_to_pb('./userdata/', 'conv2d_19/Sigmoid')


# In[52]:


get_ipython().system('ls ./userdata/')

