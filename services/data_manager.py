import os
import json
import shutil
import cv2
from datetime import datetime
from dataclasses import asdict
from typing import List, Optional
from glob import glob

from models.entities import SampleRecord, LeafResult

DATA_DIR = os.path.join(os.getcwd(), "data")
RECORDS_DIR = os.path.join(DATA_DIR, "records")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

class DataManager:
    """
    Handles persistence of SampleRecords and associated images.
    Stores metadata as JSON and images as JPG.
    """
    def __init__(self):
        self._ensure_directories()

    def _ensure_directories(self):
        os.makedirs(RECORDS_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)

    def save_record(self, record: SampleRecord, image_array=None):
        """
        Saves the SampleRecord to JSON and the image to disk.
        """
        # 1. Save Image if provided and not already a path
        if image_array is not None:
            filename = f"{record.sample_id}.jpg"
            image_path = os.path.join(IMAGES_DIR, filename)
            # Convert RGB to BGR for OpenCV saving
            bgr_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            cv2.imwrite(image_path, bgr_image)
            record.raw_image_path = image_path

        # 2. Serialize Record
        data = asdict(record)
        # Convert datetime to string
        data['timestamp'] = record.timestamp.isoformat()
        
        # 3. Save JSON
        json_path = os.path.join(RECORDS_DIR, f"{record.sample_id}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Saved record {record.sample_id} to {json_path}")

    def load_all_records(self) -> List[SampleRecord]:
        """Loads all records from the records directory, sorted by date (newest first)."""
        records = []
        json_files = glob(os.path.join(RECORDS_DIR, "*.json"))
        
        for jf in json_files:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Reconstruct SampleRecord
                # Convert string back to datetime
                if isinstance(data.get('timestamp'), str):
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                
                # Reconstruct leaf_results list
                leaves_data = data.get('leaf_results', [])
                leaves = [LeafResult(**l) for l in leaves_data]
                data['leaf_results'] = leaves
                
                records.append(SampleRecord(**data))
            except Exception as e:
                print(f"Failed to load record {jf}: {e}")
        
        # Sort by timestamp descending
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records

    def delete_record(self, sample_id: str):
        """Deletes the JSON record and its associated image."""
        # Delete JSON
        json_path = os.path.join(RECORDS_DIR, f"{sample_id}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
        
        # Delete Image
        image_path = os.path.join(IMAGES_DIR, f"{sample_id}.jpg")
        if os.path.exists(image_path):
            os.remove(image_path)
            
        print(f"Deleted record {sample_id}")

    def clear_all_data(self):
        """Deletes all records and images."""
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        self._ensure_directories()

    def export_data(self, target_dir: str, export_csv=True, export_images=True):
        """
        Exports data to a target directory.
        Optionally generates a summary CSV.
        """
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        records = self.load_all_records()
        
        # 1. Export CSV
        if export_csv:
            csv_path = os.path.join(target_dir, "summary.csv")
            with open(csv_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("SampleID,Timestamp,PlotID,Cultivar,GrowthStage,MeanDS,Severity,Notes\n")
                for r in records:
                    line = f"{r.sample_id},{r.timestamp},{r.plot_id},{r.cultivar},{r.growth_stage},{r.mean_ds},{r.severity_class},{r.notes}\n"
                    f.write(line)

        # 2. Export Images
        if export_images:
            images_target_dir = os.path.join(target_dir, "images")
            os.makedirs(images_target_dir, exist_ok=True)
            for r in records:
                if r.raw_image_path and os.path.exists(r.raw_image_path):
                    shutil.copy2(r.raw_image_path, images_target_dir)
