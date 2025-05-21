from io import BytesIO
from pydicom import dcmread
from numpy import stack, expand_dims
from keras.api.applications.vgg19 import preprocess_input

def extract_feature(dcm_image, model):
    dcm_data = dcmread(BytesIO(dcm_image.file.read()))
    image_data = dcm_data.pixel_array
    image = stack((image_data,) * 3, axis=-1)
    image = image.array_to_img(image)
    image = image.resize((224, 224))
    image_array = image.img_to_array(image)
    image_array = expand_dims(image_array, axis=0)
    image_array = preprocess_input(image_array)
    features = model.predict(image_array)
    return features
