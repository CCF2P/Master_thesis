import torch

model = torch.load("./PretrainedModels/DCM_compare_model.h5", weights_only=False)
print(model)
