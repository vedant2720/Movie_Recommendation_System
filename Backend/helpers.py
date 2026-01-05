import pickle
import pandas as pd
from config import occupation_map

# Load CMFRec model and features
with open("../model/cmfrec_model.pkl", "rb") as f:
    model = pickle.load(f)
    U = pickle.load(f)
    I = pickle.load(f)
    feature_cols = U.columns.tolist()

def build_user_vector(user_id, gender, age, occupation):
    new_user_dict = {
        "UserId": [user_id],
        "Gender": [gender],
        "Age": [age]
    }

    for occ in occupation_map.values():
        new_user_dict[f"occ_{occ}"] = [1 if occ == occupation else 0]

    new_user = pd.DataFrame(new_user_dict)

    # Align with training columns
    for col in feature_cols:
        if col not in new_user.columns:
            new_user[col] = 0

    new_user = new_user[feature_cols].astype(int)
    return new_user
