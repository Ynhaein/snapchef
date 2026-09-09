# %% [markdown] 
# ## 1. Import Libraries 

# %%
import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

# %% [markdown] 
# ## 2. Model Architecture Definition 

# %%
class FoodClassifier(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        """
        Food classification model using MobileNetV3 transfer learning.
        """
        super(FoodClassifier, self).__init__() 

        # 1. Load pretrained weights and the backbone (upgraded to .DEFAULT)
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        self.backbone = mobilenet_v3_small(weights=weights) 

        # 2. Extract the input feature size from the classifier (1024)
        in_features = self.backbone.classifier[3].in_features  

        # 3. Change the final layer output to match the number of classes
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes) 

    def forward(self, x: torch.Tensor) -> torch.Tensor: 
        """
        Forward an image through the model.
        """
        return self.backbone(x)  

# %% [markdown] 
# ## 3. Helper Function 

# %%
def get_model(num_classes: int, pretrained: bool = True) -> nn.Module: 
    """
    Helper function to create and return a model instance.
    """
    model = FoodClassifier(num_classes=num_classes, pretrained=pretrained) 
    return model 

# %% [markdown] 
# ## 4. Testing & Debugging 

# %%
if __name__ == "__main__": 
    TEST_NUM_CLASSES = 10  
    model = get_model(num_classes=TEST_NUM_CLASSES, pretrained=True) 

    dummy_input = torch.randn(2, 3, 224, 224) 
    output = model(dummy_input) 

    print("=== MODEL TEST SUCCESS ===")
    print(f"Input shape  : {dummy_input.shape}")
    print(f"Output shape : {output.shape} (Batch Size, Num Classes)")