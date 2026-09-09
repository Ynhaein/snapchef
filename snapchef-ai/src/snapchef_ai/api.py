from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException 
from fastapi.middleware.cors import CORSMiddleware 
import shutil 
from snapchef_ai.recommend import RecipeRecommender 

app = FastAPI(title="Snapchef AI API") 

# Allow React to access the API (CORS) 
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
) 

# Initiate Recommender System 
recommender = RecipeRecommender() 

# Temporary folder for saving uploaded images 
TEMP_DIR = Path("temp_uploads") 
TEMP_DIR.mkdir(exist_ok=True)  

@app.post("/api/predict")
async def predict_recipe(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="The file must be an image.")

    # Save the file temporarily
    temp_file_path = TEMP_DIR / file.filename
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Run the ML and Polars pipeline
        result = recommender.recommend(temp_file_path)
        
        # Convert the Polars DataFrame to a list of dictionaries (JSON-friendly)
        recipes_json = []
        if result["recipes"] is not None and not result["recipes"].is_empty():
            recipes_json = result["recipes"].to_dicts()

        return {
            "status": "success",
            "predicted_food": result["food_name"],
            "confidence": round(result["confidence"], 2),
            "recipes": recipes_json
        }
    finally:
        # Delete the temporary file after processing
        if temp_file_path.exists():
            temp_file_path.unlink()


