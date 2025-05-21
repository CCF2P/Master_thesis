from ..Databases.Schema import Feature

from ImagePreProcessing import extract_feature

def compare_image_by_features(features, model, database):
    all_features = database.query(Feature).all()
