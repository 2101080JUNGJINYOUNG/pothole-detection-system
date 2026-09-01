"""
Deep-Guardian AI Core
Pothole Detection and Validation Processing
"""

import cv2
import numpy as np
import requests
# Django ORM setup
import sys
import django
import os
# Add parent directory to path for Django app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
django.setup()

from django_app.models import Pothole, User
from django.db.models import Q
from ultralytics import YOLO
from synthetic_pothole_generator import SyntheticPotholeGenerator
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
from datetime import datetime, timedelta
import time
import json
import shutil
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class AICore:
    def __init__(self):
        # 설정
        self.npu_worker_url = os.getenv("NPU_WORKER_URL", "http://host.docker.internal:9001/depth")
        self.db_url = os.getenv("DATABASE_URL", "mysql://pothole_user:pothole_pass@lamp:3306/pothole_db")
        
        # Kakao Map API 설정
        self.kakao_api_key = os.getenv("KAKAO_MAP_APP_KEY", "")
        self.kakao_api_base = "https://dapi.kakao.com/v2/local"
        
        # 위험도 설정 로드
        self.risk_zones = self.load_risk_zones()
        
        # GPU 디바이스 설정
        self.device = self.get_device()
        
        # YOLOv8 모델 로드
        self.yolo_model = None
        self.load_yolo_model()
        
        # Django ORM 사용 (별도 연결 불필요)
        
        # 모델 경로 설정
        self.model_dir = "/app/models"
        self.current_model_path = None
        self.backup_model_dir = "/app/models/backup"
        os.makedirs(self.backup_model_dir, exist_ok=True)
        
        # 파인튜닝 설정
        self.finetune_threshold = 100  # 100장 이상이면 파인튜닝
        self.last_finetune_date = None
        
        # 스케줄러 초기화 및 시작
        self.scheduler = BackgroundScheduler()
        self.setup_scheduler()
        self.scheduler.start()
        print("[OK] Scheduler started - Fine-tuning will run daily at 00:00")
    
    def get_device(self):
        """Get device for YOLOv8 (GPU or CPU)"""
        try:
            import intel_extension_for_pytorch as ipex
            # Intel Extension for PyTorch가 있으면 GPU 사용
            device = 'xpu'  # Intel Arc GPU
            print(f"[OK] GPU device available: {device}")
            return device
        except (ImportError, AttributeError, Exception) as e:
            # Intel Extension for PyTorch가 없거나 오류가 발생하면 CPU 사용
            print(f"[INFO] Intel Extension for PyTorch not available - using CPU: {str(e)}")
            return 'cpu'
    
    def load_risk_zones(self):
        """위험도 구역 설정 로드"""
        try:
            risk_zones_path = "/app/risk_zones.json"
            if not os.path.exists(risk_zones_path):
                # Fallback to database directory
                risk_zones_path = "/app/../database/risk_zones.json"
            
            if os.path.exists(risk_zones_path):
                with open(risk_zones_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"[OK] Risk zones loaded from {risk_zones_path}")
                    return config
            else:
                print(f"[WARNING] Risk zones file not found, using defaults")
                return {
                    "risk_zones": [],
                    "default_priority_weight": 1.0,
                    "depth_weight": 0.3,
                    "validation_weight": 0.2
                }
        except Exception as e:
            print(f"[ERROR] Failed to load risk zones: {str(e)}")
            return {
                "risk_zones": [],
                "default_priority_weight": 1.0,
                "depth_weight": 0.3,
                "validation_weight": 0.2
            }
    
    def get_address_from_coords(self, latitude, longitude):
        """
        Kakao Map API를 사용하여 좌표를 주소로 변환
        
        Args:
            latitude: 위도
            longitude: 경도
            
        Returns:
            dict: 주소 정보 또는 None
        """
        if not self.kakao_api_key or self.kakao_api_key == "":
            print("[WARNING] Kakao Map API key not set")
            return None
            
        try:
            url = f"{self.kakao_api_base}/geo/coord2address.json"
            headers = {
                "Authorization": f"KakaoAK {self.kakao_api_key}"
            }
            params = {
                "x": longitude,
                "y": latitude,
                "input_coord": "WGS84"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 401:
                print(f"[ERROR] Kakao Map API authentication failed. Please check your REST API key.")
                print(f"[INFO] Make sure you're using REST API key (not JavaScript key) from https://developers.kakao.com/")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            if data.get('documents') and len(data['documents']) > 0:
                return data['documents'][0]
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"[ERROR] Kakao Map API authentication failed. Please check your REST API key.")
            else:
                print(f"[WARNING] Failed to get address from Kakao API: {str(e)}")
            return None
        except Exception as e:
            print(f"[WARNING] Failed to get address from Kakao API: {str(e)}")
            return None
    
    def search_nearby_facilities(self, latitude, longitude, category_code, radius=500):
        """
        Kakao Map API를 사용하여 주변 시설물 검색
        
        Args:
            latitude: 위도
            longitude: 경도
            category_code: 카테고리 코드 (예: 'SC4'=학교, 'HP8'=병원)
            radius: 검색 반경 (미터, 기본값: 500m)
            
        Returns:
            list: 시설물 목록 또는 빈 리스트
        """
        if not self.kakao_api_key or self.kakao_api_key == "":
            return []
            
        try:
            url = f"{self.kakao_api_base}/search/category.json"
            headers = {
                "Authorization": f"KakaoAK {self.kakao_api_key}"
            }
            params = {
                "category_group_code": category_code,
                "x": longitude,
                "y": latitude,
                "radius": radius,
                "size": 15
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 401:
                # 401 오류는 이미 주소 변환에서 로그가 출력되므로 여기서는 조용히 처리
                return []
            
            response.raise_for_status()
            
            data = response.json()
            if data.get('documents'):
                return data['documents']
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 401:  # 401은 이미 처리됨
                print(f"[WARNING] Failed to search nearby facilities: {str(e)}")
            return []
        except Exception as e:
            print(f"[WARNING] Failed to search nearby facilities: {str(e)}")
            return []
    
    def calculate_location_risk(self, latitude, longitude):
        """
        Kakao Map API를 사용한 위치 기반 위험도 계산
        
        Args:
            latitude: 위도
            longitude: 경도
            
        Returns:
            dict: {
                'location_type': str,
                'risk_level': str,
                'priority_weight': float,
                'location_description': str
            }
        """
        # 기본값
        result = {
            'location_type': 'general',
            'risk_level': 'medium',
            'priority_weight': self.risk_zones.get('default_priority_weight', 1.0),
            'location_description': '일반 도로'
        }
        
        try:
            # 1. 좌표를 주소로 변환
            address_info = self.get_address_from_coords(latitude, longitude)
            
            if address_info:
                # 도로명 주소 또는 지번 주소 사용
                road_address = address_info.get('road_address')
                region_address = address_info.get('address')
                
                address_text = ""
                if road_address:
                    address_text = road_address.get('address_name', '')
                    # 도로명에서 도로 유형 추출
                    road_name = road_address.get('road_name', '')
                    
                    # 고속도로 및 자동차 전용도로 검색
                    highway_keywords = ['고속도로', '자동차전용', '고속', '경부', '경인', '서해안', '중앙', '영동', '호남', '중부']
                    if any(keyword in road_name for keyword in highway_keywords):
                        result['location_type'] = 'highway'
                        result['priority_weight'] = 3.0
                        result['location_description'] = '고속도로 및 자동차 전용도로'
                        return result
                    
                    # 버스 전용차로 검색
                    if '버스전용' in road_name or '전용차로' in road_name:
                        result['location_type'] = 'bus_lane'
                        result['priority_weight'] = 2.0
                        result['location_description'] = '시내버스 전용차로'
                        return result
                
                if not address_text and region_address:
                    address_text = region_address.get('address_name', '')
                
                # 주소에서 지역 유형 추출
                if address_text:
                    # 주거 지역 키워드
                    residential_keywords = ['동', '아파트', '주택', '단지', '마을']
                    if any(keyword in address_text for keyword in residential_keywords):
                        result['location_type'] = 'residential'
                        result['priority_weight'] = 1.2
                        result['location_description'] = '주거 밀집 지역'
                    
                    # 상업 지역 키워드
                    commercial_keywords = ['상가', '상권', '시장', '거리', '번화가']
                    if any(keyword in address_text for keyword in commercial_keywords):
                        result['location_type'] = 'commercial'
                        result['priority_weight'] = 1.0
                        result['location_description'] = '상업 지역'
                    
                    # 공원/녹지 키워드
                    park_keywords = ['공원', '녹지', '산', '숲']
                    if any(keyword in address_text for keyword in park_keywords):
                        result['location_type'] = 'park'
                        result['priority_weight'] = 0.8
                        result['location_description'] = '공원 및 녹지 지역'
            
            # 2. 주변 시설물 검색 (학교, 병원)
            # 학교 검색 (카테고리 코드: SC4)
            schools = self.search_nearby_facilities(latitude, longitude, 'SC4', radius=500)
            if schools:
                # 학교가 500m 이내에 있으면 학교 주변으로 판단
                result['location_type'] = 'school_area'
                result['priority_weight'] = 2.5
                result['location_description'] = '학교 주변 500m 이내'
                
                # 어린이 보호구역 확인 (학교가 매우 가까운 경우)
                if schools and len(schools) > 0:
                    # 가장 가까운 학교까지의 거리 확인
                    closest_school = schools[0]
                    distance = float(closest_school.get('distance', 999))
                    if distance < 200:  # 200m 이내면 어린이 보호구역으로 판단
                        result['location_type'] = 'school_zone'
                        result['priority_weight'] = 3.0
                        result['location_description'] = '어린이 보호구역 및 학교 주변'
                        return result
                
                return result
            
            # 병원 검색 (카테고리 코드: HP8)
            hospitals = self.search_nearby_facilities(latitude, longitude, 'HP8', radius=500)
            if hospitals:
                result['location_type'] = 'hospital_area'
                result['priority_weight'] = 2.5
                result['location_description'] = '병원 및 응급의료기관 주변'
                return result
            
        except Exception as e:
            print(f"[WARNING] Location risk calculation error: {str(e)}")
            # 에러 발생 시 기본값 반환
        
        return result
    
    def calculate_priority_score(self, location_risk, depth_ratio, validation_result):
        """
        우선순위 점수 계산
        
        Args:
            location_risk: 위치 기반 위험도 정보
            depth_ratio: 깊이 비율
            validation_result: 검증 결과
            
        Returns:
            float: 우선순위 점수
        """
        # 위치 가중치
        location_weight = location_risk['priority_weight']
        
        # 깊이 가중치 (깊을수록 높은 점수)
        depth_weight = self.risk_zones.get('depth_weight', 0.3)
        depth_score = depth_ratio * depth_weight * 10  # 0-1 범위를 0-10으로 확대
        
        # 검증 결과 가중치
        validation_weight = self.risk_zones.get('validation_weight', 0.2)
        validation_score = 1.0 if validation_result else 0.0
        
        # 최종 우선순위 점수
        priority_score = (
            location_weight * 10 +  # 위치 가중치 (주요 요소)
            depth_score +          # 깊이 점수
            validation_score * validation_weight * 10  # 검증 점수
        )
        
        return round(priority_score, 4)
    
    def determine_risk_level(self, priority_score):
        """
        우선순위 점수에 따른 위험도 레벨 결정
        
        Args:
            priority_score: 우선순위 점수
            
        Returns:
            str: 위험도 레벨 ('low', 'medium', 'high', 'critical')
        """
        if priority_score >= 30:
            return 'critical'
        elif priority_score >= 20:
            return 'high'
        elif priority_score >= 10:
            return 'medium'
        else:
            return 'low'
    
    def load_yolo_model(self, model_path=None):
        """Load YOLOv8 model with GPU support"""
        try:
            # 모델 경로가 지정되지 않으면 환경 변수 또는 기본 경로 사용
            if model_path is None:
                model_path = os.getenv("YOLO_MODEL_PATH", "/app/models/best2.pt")
            
            # Fallback paths
            fallback_paths = [
                model_path,
                "/app/models/best2.pt",
                "/app/models/external/best2.pt",
                "/app/models/yolov8n.pt"
            ]
            
            loaded = False
            for path in fallback_paths:
                if os.path.exists(path):
                    # YOLOv8 모델 로드 (device 지정)
                    self.yolo_model = YOLO(path)
                    self.current_model_path = path
                    print(f"[OK] YOLOv8 model loaded: {path}")
                    print(f"[OK] Using device: {self.device}")
                    loaded = True
                    break
            
            if not loaded:
                # If model not found, try auto-download
                print("[WARNING] YOLOv8 model file not found, downloading default model...")
                self.yolo_model = YOLO("yolov8n.pt")
                self.current_model_path = "yolov8n.pt"
                print(f"[OK] YOLOv8 model loaded (auto-downloaded)")
                print(f"[OK] Using device: {self.device}")
        except Exception as e:
            print(f"[ERROR] Failed to load YOLOv8 model: {str(e)}")
            raise
    
    def connect_db(self):
        """Django ORM 연결 확인 (이미 setup에서 처리됨)"""
        try:
            # Django ORM 연결 테스트
            Pothole.objects.first()
            print("[OK] Django ORM database connection ready")
        except Exception as e:
            print(f"[ERROR] Django ORM connection failed: {str(e)}")
    
    def get_gps_from_image(self, image_path):
        """
        Extract GPS coordinates from image EXIF data
        
        Args:
            image_path: Path to image file
            
        Returns:
            (latitude, longitude) tuple or (None, None) if not found
        """
        try:
            image = Image.open(image_path)
            exifdata = image.getexif()
            
            if exifdata is None:
                return None, None
            
            # Find GPS info
            gps_info = None
            for tag_id in exifdata:
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps_info = exifdata.get(tag_id)
                    break
            
            if gps_info is None:
                return None, None
            
            # Parse GPS coordinates
            def get_decimal_from_dms(dms, ref):
                degrees = float(dms[0])
                minutes = float(dms[1])
                seconds = float(dms[2])
                decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
                if ref in ['S', 'W']:
                    decimal = -decimal
                return decimal
            
            lat = None
            lon = None
            
            for key in gps_info.keys():
                sub_tag = GPSTAGS.get(key, key)
                if sub_tag == 'GPSLatitude':
                    lat_ref = gps_info.get(GPSTAGS.get(1, 1), 'N')
                    lat = get_decimal_from_dms(gps_info[key], lat_ref)
                elif sub_tag == 'GPSLongitude':
                    lon_ref = gps_info.get(GPSTAGS.get(3, 3), 'E')
                    lon = get_decimal_from_dms(gps_info[key], lon_ref)
            
            if lat is not None and lon is not None:
                print(f"[INFO] GPS coordinates extracted from image: {lat:.6f}, {lon:.6f}")
                return lat, lon
            
            return None, None
        except Exception as e:
            print(f"[WARNING] Failed to extract GPS from image: {str(e)}")
            return None, None
    
    def detect_potholes(self, image_path):
        """
        Detect potholes using YOLOv8
        
        Args:
            image_path: Input image path
            
        Returns:
            bboxes: List of detected bounding boxes [(x1, y1, x2, y2, confidence), ...]
        """
        try:
            # YOLOv8 추론 (최적화된 설정)
            results = self.yolo_model(
                image_path, 
                device=self.device,
                imgsz=416,  # 작은 이미지 크기로 속도 향상
                half=True if self.device != 'cpu' else False,  # GPU일 때 FP16 사용
                verbose=False
            )
            bboxes = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Class check (pothole class ID may vary by model)
                    # Here we use all detections (in practice, filter by pothole class only)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    bboxes.append((int(x1), int(y1), int(x2), int(y2), float(confidence)))
            
            return bboxes
        except Exception as e:
            print(f"[ERROR] Pothole detection failed: {str(e)}")
            return []
    
    def crop_pothole(self, image_path, bbox):
        """
        Crop pothole region only
        
        Args:
            image_path: Original image path
            bbox: (x1, y1, x2, y2, confidence)
            
        Returns:
            cropped_image: PIL Image
        """
        x1, y1, x2, y2, _ = bbox
        image = Image.open(image_path)
        cropped = image.crop((x1, y1, x2, y2))
        return cropped
    
    def validate_depth(self, image, max_retries=3, retry_delay=2):
        """
        Validate depth using NPU Worker with retry logic
        
        Args:
            image: PIL Image
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            result: {"success": bool, "depth_ratio": float, "validation_result": bool}
        """
        for attempt in range(max_retries):
            try:
                # Convert image to bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='JPEG')
                img_bytes.seek(0)
                
                # Call NPU Worker
                files = {'image': img_bytes}
                response = requests.post(self.npu_worker_url, files=files, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", False):
                        return result
                    else:
                        print(f"[WARNING] NPU Worker returned unsuccessful result: {result.get('error', 'Unknown error')}")
                        if attempt < max_retries - 1:
                            print(f"[INFO] Retrying... ({attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            continue
                        return result
                else:
                    print(f"[ERROR] NPU Worker response error: {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"[INFO] Retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    return {"success": False, "error": f"HTTP {response.status_code}"}
            except requests.exceptions.Timeout:
                print(f"[ERROR] NPU Worker request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                return {"success": False, "error": "Request timeout"}
            except requests.exceptions.ConnectionError:
                print(f"[ERROR] NPU Worker connection error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                return {"success": False, "error": "Connection error - NPU Worker may be down"}
            except Exception as e:
                print(f"[ERROR] Depth validation failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def save_to_db(self, latitude, longitude, depth_ratio, validation_result, 
                   image_path=None, bbox=None, confidence=None,
                   location_type=None, risk_level=None, priority_score=None,
                   location_description=None):
        """
        Save to database using Django ORM
        
        Args:
            latitude: Latitude
            longitude: Longitude
            depth_ratio: Depth ratio
            validation_result: Validation result
            image_path: Image path
            bbox: (x1, y1, x2, y2)
            confidence: Confidence score
            location_type: Location type (e.g., 'highway', 'school_zone')
            risk_level: Risk level ('low', 'medium', 'high', 'critical')
            priority_score: Priority score
            location_description: Location description
        """
        # 위험도 정보가 제공되지 않은 경우 자동 계산
        if location_type is None or risk_level is None or priority_score is None:
            location_risk = self.calculate_location_risk(latitude, longitude)
            if location_type is None:
                location_type = location_risk['location_type']
            if location_description is None:
                location_description = location_risk['location_description']
            if priority_score is None:
                priority_score = self.calculate_priority_score(location_risk, depth_ratio, validation_result)
            if risk_level is None:
                risk_level = self.determine_risk_level(priority_score)
        
        try:
            bbox_x1, bbox_y1, bbox_x2, bbox_y2 = bbox if bbox else (None, None, None, None)
            
            pothole = Pothole.objects.create(
                latitude=latitude,
                longitude=longitude,
                depth_ratio=depth_ratio,
                validation_result=validation_result,
                image_path=image_path,
                bbox_x1=bbox_x1,
                bbox_y1=bbox_y1,
                bbox_x2=bbox_x2,
                bbox_y2=bbox_y2,
                confidence_score=confidence,
                location_type=location_type,
                risk_level=risk_level,
                priority_score=priority_score,
                location_description=location_description
            )
            print(f"[OK] Saved to database: {latitude}, {longitude} (Priority: {priority_score}, Risk: {risk_level})")
            return True
        except Exception as e:
            print(f"[ERROR] Database save failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_image(self, image_path, latitude=None, longitude=None):
        """
        Image processing pipeline
        
        1) Extract GPS coordinates from image EXIF (if not provided)
        2) YOLOv8 → pothole bbox detection
        3) Crop pothole region only
        4) Depth validation using NPU depth model
        5) Save only validated data to DB
        
        Args:
            image_path: Path to image file
            latitude: GPS latitude (optional, will extract from EXIF if not provided)
            longitude: GPS longitude (optional, will extract from EXIF if not provided)
        """
        print(f"\n[INFO] Starting image processing: {image_path}")
        
        # 0. Extract GPS coordinates if not provided
        if latitude is None or longitude is None:
            lat, lon = self.get_gps_from_image(image_path)
            if lat is not None and lon is not None:
                latitude = lat
                longitude = lon
            else:
                # Use default coordinates (Seoul) if GPS not found
                latitude = latitude if latitude is not None else 37.5665
                longitude = longitude if longitude is not None else 126.9780
                print(f"[INFO] GPS not found in image, using default: {latitude}, {longitude}")
        
        # 1. Pothole detection
        bboxes = self.detect_potholes(image_path)
        print(f"[INFO] Detected potholes: {len(bboxes)}")
        
        if not bboxes:
            print("[INFO] No potholes detected")
            return
        
        # 2-4. Process each pothole
        for bbox in bboxes:
            x1, y1, x2, y2, confidence = bbox
            print(f"[INFO] Processing pothole: bbox=({x1}, {y1}, {x2}, {y2}), confidence={confidence:.3f}")
            
            # 2. Crop
            cropped = self.crop_pothole(image_path, bbox)
            
            # 3. Depth validation
            depth_result = self.validate_depth(cropped)
            
            if not depth_result.get("success"):
                print(f"[ERROR] Depth validation failed: {depth_result.get('error')}")
                continue
            
            depth_ratio = depth_result.get("depth_ratio", 0.0)
            validation_result = depth_result.get("validation_result", False)
            
            print(f"[INFO] Depth ratio: {depth_ratio:.4f}, Validation: {'PASS' if validation_result else 'FAIL'}")
            
            # 4. Save to DB only if validation passed
            if validation_result:
                # Save cropped image to shared directory
                shared_image_path = self.save_cropped_image(cropped, image_path, bbox)
                
                self.save_to_db(
                    latitude=latitude,
                    longitude=longitude,
                    depth_ratio=depth_ratio,
                    validation_result=validation_result,
                    image_path=shared_image_path,  # Use shared path
                    bbox=(x1, y1, x2, y2),
                    confidence=confidence
                )
                print("[OK] Validation passed - Saved to DB")
            else:
                print("[INFO] Validation failed - Not saved to DB")
    
    def save_cropped_image(self, cropped_image, original_path, bbox):
        """
        Save cropped pothole image to shared directory
        
        Args:
            cropped_image: PIL Image (cropped pothole)
            original_path: Original image path
            bbox: (x1, y1, x2, y2)
            
        Returns:
            shared_image_path: Path in shared directory
        """
        try:
            # Create shared images directory if not exists
            shared_dir = "/app/shared_images"
            os.makedirs(shared_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"pothole_{timestamp}.jpg"
            shared_path = os.path.join(shared_dir, filename)
            
            # Save image
            cropped_image.save(shared_path, "JPEG", quality=85)
            print(f"[INFO] Saved cropped image: {shared_path}")
            
            return shared_path
        except Exception as e:
            print(f"[ERROR] Failed to save cropped image: {str(e)}")
            # Return original path as fallback
            return image_path
    
    def create_result_video_from_original(self, original_video_path, video_result_dir, processed_frames_dict, fps, video_basename, total_frames):
        """
        원본 비디오를 다시 읽어서 모든 프레임을 포함한 동영상 생성
        처리된 프레임은 추론 결과가 그려진 프레임을 사용하고, 나머지는 원본 프레임 사용
        
        Args:
            original_video_path: 원본 비디오 파일 경로
            video_result_dir: 결과 디렉토리
            processed_frames_dict: {frame_number: frame_info} 딕셔너리
            fps: 원본 비디오 FPS
            video_basename: 비디오 파일명 (확장자 제외)
            total_frames: 전체 프레임 수
            
        Returns:
            result_video_path: 생성된 동영상 경로 또는 None
        """
        print(f"[INFO] Creating result video from original video: {original_video_path}")
        print(f"[INFO] Total frames: {total_frames}, Processed frames: {len(processed_frames_dict)}")
        
        # 원본 비디오 다시 열기
        cap = cv2.VideoCapture(original_video_path)
        if not cap.isOpened():
            print(f"[ERROR] Failed to reopen original video: {original_video_path}")
            return None
        
        try:
            # 첫 번째 프레임으로 크기 확인
            ret, first_frame = cap.read()
            if not ret:
                print("[ERROR] Failed to read first frame from original video")
                return None
            
            height, width = first_frame.shape[:2]
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 처음으로 되돌리기
            
            # 동영상 파일 경로
            result_video_path = os.path.join(video_result_dir, f"{video_basename}_result.mp4")
            
            # VideoWriter 설정
            fourcc = None
            out = None
            
            # 코덱 우선순위: H264 > XVID > MJPG > mp4v
            codecs_to_try = [
                ('avc1', 'H.264 (avc1)'),
                ('H264', 'H.264 (H264)'),
                ('XVID', 'XVID'),
                ('MJPG', 'Motion JPEG'),
                ('mp4v', 'MPEG-4')
            ]
            
            output_fps = fps if fps > 0 else 30.0
            
            for codec_name, codec_desc in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_name)
                    out = cv2.VideoWriter(result_video_path, fourcc, output_fps, (width, height))
                    if out.isOpened():
                        print(f"[INFO] 비디오 코덱 사용: {codec_desc}")
                        break
                    else:
                        out.release()
                        out = None
                except Exception as e:
                    print(f"[WARNING] 코덱 {codec_name} 실패: {str(e)}")
                    if out:
                        out.release()
                        out = None
                    continue
            
            # 모든 코덱 실패 시 기본값 사용
            if out is None or not out.isOpened():
                print("[WARNING] 모든 코덱 실패, 기본값(mp4v) 사용")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(result_video_path, fourcc, output_fps, (width, height))
            
            if not out.isOpened():
                print(f"[ERROR] Failed to create video writer for: {result_video_path}")
                return None
            
            # 모든 프레임을 읽어서 동영상에 추가
            print(f"[INFO] Starting to add {total_frames} frames to video...")
            print(f"[INFO] Video output: {result_video_path}")
            print(f"[INFO] Video settings: {width}x{height} @ {output_fps} fps")
            
            frame_count = 0
            frames_written = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 처리된 프레임인지 확인
                if frame_count in processed_frames_dict:
                    # 처리된 프레임: 추론 결과가 그려진 프레임 사용
                    frame_info = processed_frames_dict[frame_count]
                    frame_image_path = frame_info.get("frame_image_path")
                    if frame_image_path and os.path.exists(frame_image_path):
                        # 디스크에서 처리된 프레임 이미지 로드
                        frame_image = cv2.imread(frame_image_path)
                        if frame_image is not None:
                            # 크기가 다른 경우 리사이즈
                            if frame_image.shape[:2] != (height, width):
                                frame_image = cv2.resize(frame_image, (width, height))
                            frame = frame_image
                        else:
                            print(f"[WARNING] Failed to load processed frame image: {frame_image_path}")
                    else:
                        # 프레임 이미지 파일이 없으면 원본 프레임에 바운딩 박스 다시 그리기
                        detections = frame_info.get("detections", [])
                        if detections:
                            for det in detections:
                                bbox = det.get("bbox", [])
                                confidence = det.get("confidence", 0.0)
                                if len(bbox) == 4:
                                    x1, y1, x2, y2 = bbox
                                    # 바운딩 박스 그리기
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                    # 신뢰도 텍스트
                                    label = f"Pothole {confidence:.2f}"
                                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                                    cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                                 (x1 + label_size[0], y1), (0, 255, 0), -1)
                                    cv2.putText(frame, label, (x1, y1 - 5),
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                            
                            # FPS 정보 표시 (원본 FPS 사용)
                            info_text = f"FPS: {fps:.1f} | Detections: {len(detections)}"
                            cv2.putText(frame, info_text, (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            cv2.putText(frame, info_text, (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
                # else: 처리되지 않은 프레임은 원본 프레임 그대로 사용
                
                # 프레임을 비디오에 쓰기
                try:
                    success = out.write(frame)
                    if success:
                        frames_written += 1
                    else:
                        print(f"[WARNING] Failed to write frame {frame_count + 1}")
                    
                    # 진행 상황 출력 (100프레임마다 또는 마지막 프레임)
                    if (frame_count + 1) % 100 == 0 or (frame_count + 1) == total_frames:
                        progress = ((frame_count + 1) / total_frames * 100) if total_frames > 0 else 0
                        print(f"[INFO] Added {frame_count + 1}/{total_frames} frames to video ({progress:.1f}%)")
                except Exception as e:
                    print(f"[ERROR] Error processing frame {frame_count + 1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
                
                frame_count += 1
            
            cap.release()
            out.release()
            
            # 생성된 비디오 정보 확인
            if os.path.exists(result_video_path):
                file_size = os.path.getsize(result_video_path)
                estimated_duration = frames_written / output_fps if output_fps > 0 else 0
                print(f"[INFO] Video created successfully: {result_video_path}")
                print(f"[INFO] Video file size: {file_size / (1024*1024):.2f} MB")
                print(f"[INFO] Frames written: {frames_written}/{total_frames}")
                print(f"[INFO] Estimated duration: {estimated_duration:.2f} seconds")
                return result_video_path
            else:
                print(f"[ERROR] Video file was not created: {result_video_path}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to create result video from original: {str(e)}")
            import traceback
            traceback.print_exc()
            if cap.isOpened():
                cap.release()
            if out is not None:
                out.release()
            return None
    
    def create_result_video(self, video_result_dir, frames_info, fps, video_basename):
        """
        프레임들을 동영상으로 합치기
        
        Args:
            video_result_dir: 결과 디렉토리
            frames_info: 프레임 정보 리스트
            fps: 원본 비디오 FPS
            video_basename: 비디오 파일명 (확장자 제외)
            
        Returns:
            result_video_path: 생성된 동영상 경로 또는 None
        """
        if not frames_info:
            print("[WARNING] No frames to create video")
            return None
        
        try:
            # 프레임 이미지 가져오기 (메모리에서 직접)
            frame_images = []
            for frame_info in frames_info:
                frame_image = frame_info.get("frame_image")
                if frame_image is not None:
                    # numpy array인지 확인
                    if isinstance(frame_image, np.ndarray):
                        frame_images.append(frame_image)
                    else:
                        print(f"[WARNING] Invalid frame image type: {type(frame_image)}")
            
            if not frame_images:
                print("[WARNING] No valid frame images found")
                return None
            
            # 첫 번째 프레임으로부터 크기 확인
            first_frame = frame_images[0]
            height, width, _ = first_frame.shape
            
            # 동영상 파일 경로
            result_video_path = os.path.join(video_result_dir, f"{video_basename}_result.mp4")
            
            # VideoWriter 설정 (MP4, H.264 코덱 - 웹 브라우저 호환성 향상)
            # 웹 호환성을 위해 여러 코덱 시도
            fourcc = None
            out = None
            
            # 코덱 우선순위: H264 > XVID > MJPG > mp4v
            codecs_to_try = [
                ('avc1', 'H.264 (avc1)'),
                ('H264', 'H.264 (H264)'),
                ('XVID', 'XVID'),
                ('MJPG', 'Motion JPEG'),
                ('mp4v', 'MPEG-4')
            ]
            
            # FPS 계산: 원본 FPS를 frame_interval로 조정
            # frame_interval=1이면 모든 프레임을 사용하므로 원본 FPS 사용
            # frame_interval>1이면 일부 프레임만 사용하므로 FPS를 조정해야 함
            # 하지만 현재는 frame_interval=1이므로 원본 FPS 사용
            output_fps = fps if fps > 0 else 30.0
            
            # 실제 프레임 수와 원본 프레임 수 확인
            total_original_frames = len(frames_info)  # 처리된 프레임 수
            print(f"[INFO] Total frames to add: {total_original_frames}, Output FPS: {output_fps}")
            
            for codec_name, codec_desc in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_name)
                    out = cv2.VideoWriter(result_video_path, fourcc, output_fps, (width, height))
                    if out.isOpened():
                        print(f"[INFO] 비디오 코덱 사용: {codec_desc}")
                        break
                    else:
                        out.release()
                        out = None
                except Exception as e:
                    print(f"[WARNING] 코덱 {codec_name} 실패: {str(e)}")
                    if out:
                        out.release()
                        out = None
                    continue
            
            # 모든 코덱 실패 시 기본값 사용
            if out is None or not out.isOpened():
                print("[WARNING] 모든 코덱 실패, 기본값(mp4v) 사용")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(result_video_path, fourcc, output_fps, (width, height))
            
            if not out.isOpened():
                print(f"[ERROR] Failed to create video writer for: {result_video_path}")
                return None
            
            # 프레임들을 동영상에 추가 (메모리에서 직접)
            print(f"[INFO] Starting to add {len(frame_images)} frames to video...")
            print(f"[INFO] Video output: {result_video_path}")
            print(f"[INFO] Video settings: {width}x{height} @ {output_fps} fps")
            
            frames_written = 0
            for i, frame in enumerate(frame_images):
                try:
                    # 크기가 다른 경우 리사이즈
                    if frame.shape[:2] != (height, width):
                        frame = cv2.resize(frame, (width, height))
                    
                    # 프레임을 비디오에 쓰기
                    success = out.write(frame)
                    if success:
                        frames_written += 1
                    else:
                        print(f"[WARNING] Failed to write frame {i+1}")
                    
                    # 진행 상황을 더 자주 출력 (100프레임마다 또는 마지막 프레임)
                    if (i + 1) % 100 == 0 or (i + 1) == len(frame_images):
                        print(f"[INFO] Added {i + 1}/{len(frame_images)} frames to video ({((i+1)/len(frame_images)*100):.1f}%)")
                except Exception as e:
                    print(f"[ERROR] Error processing frame {i+1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            out.release()
            
            # 생성된 비디오 정보 확인
            if os.path.exists(result_video_path):
                file_size = os.path.getsize(result_video_path)
                estimated_duration = frames_written / output_fps if output_fps > 0 else 0
                print(f"[INFO] Video created successfully: {result_video_path}")
                print(f"[INFO] Video file size: {file_size / (1024*1024):.2f} MB")
                print(f"[INFO] Frames written: {frames_written}/{len(frame_images)}")
                print(f"[INFO] Estimated duration: {estimated_duration:.2f} seconds")
            else:
                print(f"[ERROR] Video file was not created: {result_video_path}")
                return None
            
            return result_video_path
            
        except Exception as e:
            print(f"[ERROR] Failed to create result video: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_random_korea_location(self):
        """
        대한민국 전국 각지의 다양한 장소 중 랜덤으로 GPS 좌표 선택
        
        Returns:
            (latitude, longitude, location_name): GPS 좌표와 장소 이름
        """
        try:
            locations_file = "/app/korea_locations.json"
            if os.path.exists(locations_file):
                with open(locations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    locations = data.get("locations", [])
                    if locations:
                        import random
                        selected = random.choice(locations)
                        lat = selected.get("latitude")
                        lon = selected.get("longitude")
                        name = selected.get("name", "Unknown")
                        location_type = selected.get("type", "unknown")
                        print(f"[INFO] Selected random location: {name} ({location_type}) - {lat}, {lon}")
                        return lat, lon, name
        except Exception as e:
            print(f"[WARNING] Failed to load Korea locations: {str(e)}")
        
        # Fallback: 서울 좌표
        print("[INFO] Using default Seoul coordinates as fallback")
        return 37.5665, 126.9780, "서울시청 (기본값)"
    
    def process_video(self, video_path, latitude=None, longitude=None, frame_interval=1):
        """
        Process video file frame by frame
        
        Args:
            video_path: Path to video file
            latitude: GPS latitude (optional, if None, random Korea location will be used)
            longitude: GPS longitude (optional, if None, random Korea location will be used)
            frame_interval: Process every N frames (default: 1, 모든 프레임 처리)
        """
        print(f"\n[INFO] Starting video processing: {video_path}")
        
        # GPS 좌표가 제공되지 않으면 랜덤으로 대한민국 장소 선택
        if latitude is None or longitude is None:
            lat, lon, location_name = self.get_random_korea_location()
            latitude = lat
            longitude = lon
            print(f"[INFO] Using random Korea location: {location_name} ({latitude}, {longitude})")
        
        if not os.path.exists(video_path):
            print(f"[ERROR] Video file not found: {video_path}")
            return
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[ERROR] Failed to open video: {video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"[INFO] Video info: {total_frames} frames, {fps:.2f} fps")
        
        frame_count = 0
        processed_count = 0
        
        # 비디오 처리 결과 저장을 위한 디렉토리
        video_output_dir = "/app/shared_images/video_results"
        os.makedirs(video_output_dir, exist_ok=True)
        
        # 비디오 파일명 기반 디렉토리 생성
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        video_result_dir = os.path.join(video_output_dir, f"{video_basename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(video_result_dir, exist_ok=True)
        
        # 비디오 처리 정보 저장
        video_info = {
            "video_path": video_path,
            "video_name": os.path.basename(video_path),
            "total_frames": total_frames,
            "fps": fps,
            "frame_interval": frame_interval,
            "start_time": datetime.now().isoformat(),
            "frames": [],
            "processed_frames": 0,
            "total_detections": 0,
            "status": "processing"  # processing, completed
        }
        
        # 처리 시작 시 즉시 video_info.json 저장 (페이지에서 처리 중 상태 확인 가능)
        info_file = os.path.join(video_result_dir, "video_info.json")
        video_info_for_save = video_info.copy()
        video_info_for_save["frames"] = []  # 프레임 데이터는 저장하지 않음
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(video_info_for_save, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Created video_info.json: {info_file}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every N frames
            if frame_count % frame_interval == 0:
                # 추론 시작 시간 측정
                inference_start_time = time.time()
                
                # Save frame as temporary image (최적화: 낮은 품질로 저장)
                temp_dir = "/app/temp"
                os.makedirs(temp_dir, exist_ok=True)
                temp_image_path = os.path.join(temp_dir, f"frame_{frame_count}.jpg")
                cv2.imwrite(temp_image_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                # 원본 프레임 복사 (시각화용)
                frame_copy = frame.copy()
                
                # YOLO 추론 실행 (최적화: 작은 이미지 크기, half precision)
                detections = self.yolo_model.predict(
                    temp_image_path,
                    device=self.device,
                    conf=0.25,
                    imgsz=416,  # 640 -> 416으로 축소하여 속도 향상
                    half=True if self.device != 'cpu' else False,  # GPU일 때 FP16 사용
                    verbose=False,
                    agnostic_nms=False,
                    max_det=300  # 최대 탐지 수 제한
                )
                
                # 추론 시간 계산
                inference_time = time.time() - inference_start_time
                actual_fps = 1.0 / inference_time if inference_time > 0 else 0
                
                # 추론 결과를 프레임에 그리기
                frame_with_detections = frame_copy.copy()
                detected_potholes = []
                
                if len(detections) > 0 and detections[0].boxes is not None:
                    boxes = detections[0].boxes
                    for box in boxes:
                        # 바운딩 박스 좌표
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # 바운딩 박스 그리기
                        cv2.rectangle(frame_with_detections, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # 신뢰도 텍스트
                        label = f"Pothole {confidence:.2f}"
                        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(frame_with_detections, (x1, y1 - label_size[1] - 10), 
                                     (x1 + label_size[0], y1), (0, 255, 0), -1)
                        cv2.putText(frame_with_detections, label, (x1, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                        
                        detected_potholes.append({
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "confidence": float(confidence)
                        })
                
                # 실제 추론 FPS 및 정보 표시 (왼쪽 상단)
                info_text = f"FPS: {actual_fps:.1f} | Detections: {len(detected_potholes)}"
                cv2.putText(frame_with_detections, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame_with_detections, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
                
                # 처리된 프레임 이미지를 디스크에 저장 (동영상 생성 시 사용)
                frame_image_path = os.path.join(video_result_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_image_path, frame_with_detections, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                # 프레임 정보 저장
                frame_info = {
                    "frame_number": frame_count,
                    "timestamp": frame_count / fps if fps > 0 else 0,
                    "detections": detected_potholes,
                    "frame_image_path": frame_image_path  # 디스크 경로 저장
                }
                video_info["frames"].append(frame_info)
                
                # Process frame (GPS will be extracted from frame if available, or use provided/default)
                self.process_image(temp_image_path, latitude, longitude)
                processed_count += 1
                
                # 주기적으로 video_info.json 업데이트 (처리 중 상태 표시를 위해)
                if processed_count % 10 == 0:  # 10프레임마다 업데이트
                    video_info["processed_frames"] = processed_count
                    video_info["total_detections"] = sum(len(f.get("detections", [])) for f in video_info["frames"])
                    video_info_for_save = video_info.copy()
                    # frame_image_path는 이미 경로 문자열이므로 그대로 저장 가능
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump(video_info_for_save, f, indent=2, ensure_ascii=False)
                
                # Clean up temp file
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            
            frame_count += 1
            
            if frame_count % 100 == 0:
                print(f"[INFO] Processed {frame_count}/{total_frames} frames ({processed_count} processed)")
        
        cap.release()
        print(f"[INFO] Video reading completed. Total frames: {frame_count}, Processed: {processed_count}")
        print(f"[INFO] Frames stored in memory: {len(video_info['frames'])}")
        
        # 프레임 수 확인 및 검증
        if len(video_info["frames"]) != processed_count:
            print(f"[WARNING] Frame count mismatch: stored={len(video_info['frames'])}, processed={processed_count}")
        
        # 비디오 처리 정보 저장 (동영상 생성 전에 먼저 저장)
        video_info["end_time"] = datetime.now().isoformat()
        video_info["processed_frames"] = processed_count
        video_info["total_detections"] = sum(len(f["detections"]) for f in video_info["frames"])
        video_info["result_directory"] = video_result_dir  # 실제 경로 저장
        video_info["status"] = "completed"
        video_info["video_creating"] = True  # 동영상 생성 중 플래그
        
        print(f"[INFO] Video processing completed: {processed_count} frames processed")
        print(f"[INFO] Video results saved to: {video_result_dir}")
        print(f"[INFO] Total detections: {video_info['total_detections']}")
        print(f"[INFO] Original video: {total_frames} frames @ {fps:.2f} fps")
        if fps > 0:
            print(f"[INFO] Expected duration: {total_frames / fps:.2f} seconds")
        
        # 처리된 프레임을 딕셔너리로 변환 (빠른 조회를 위해)
        processed_frames_dict = {}
        for frame_info in video_info["frames"]:
            frame_num = frame_info["frame_number"]
            processed_frames_dict[frame_num] = frame_info
        
        # 프레임들을 동영상으로 합치기 (원본 비디오의 모든 프레임 포함)
        print(f"[INFO] Creating result video from {total_frames} frames (processed: {processed_count})...")
        print(f"[INFO] This may take a while depending on the number of frames...")
        try:
            result_video_path = self.create_result_video_from_original(
                video_path, video_result_dir, processed_frames_dict, fps, video_basename, total_frames
            )
            if result_video_path:
                video_info["result_video_path"] = result_video_path
                print(f"[INFO] Result video created: {result_video_path}")
            else:
                print(f"[WARNING] Result video creation failed or was skipped")
        except Exception as e:
            print(f"[ERROR] Failed to create result video: {str(e)}")
            import traceback
            traceback.print_exc()
            result_video_path = None
        
        # 동영상 생성 결과를 포함하여 최종 정보 저장
        info_file = os.path.join(video_result_dir, "video_info.json")
        # frame_image_path는 이미 경로 문자열이므로 그대로 저장 가능
        video_info_for_save = video_info.copy()
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(video_info_for_save, f, indent=2, ensure_ascii=False)
    
    def load_processed_videos(self, state_file="/app/processed_videos.json"):
        """
        처리된 동영상 목록을 파일에서 로드
        
        Args:
            state_file: 상태 파일 경로
            
        Returns:
            dict: {filepath: {'processed_at': timestamp, 'file_size': size, 'file_mtime': mtime}}
        """
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[INFO] Loaded {len(data)} processed video records from {state_file}")
                    return data
            except Exception as e:
                print(f"[WARNING] Failed to load processed videos state: {str(e)}")
                return {}
        return {}
    
    def save_processed_video(self, filepath, state_file="/app/processed_videos.json"):
        """
        처리된 동영상을 상태 파일에 저장
        
        Args:
            filepath: 처리된 동영상 파일 경로
            state_file: 상태 파일 경로
        """
        try:
            # 기존 상태 로드
            processed = self.load_processed_videos(state_file)
            
            # 파일 정보 수집
            if os.path.exists(filepath):
                file_stat = os.stat(filepath)
                processed[filepath] = {
                    'processed_at': datetime.now().isoformat(),
                    'file_size': file_stat.st_size,
                    'file_mtime': file_stat.st_mtime
                }
                
                # 상태 파일 저장
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(processed, f, indent=2, ensure_ascii=False)
                
                print(f"[INFO] Saved processed video record: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[WARNING] Failed to save processed video state: {str(e)}")
    
    def is_video_processed(self, filepath, processed_state):
        """
        동영상이 이미 처리되었는지 확인
        파일 크기나 수정 시간이 변경되었으면 다시 처리
        
        Args:
            filepath: 동영상 파일 경로
            processed_state: 처리된 파일 상태 딕셔너리
            
        Returns:
            bool: 이미 처리되었으면 True
        """
        if filepath not in processed_state:
            return False
        
        # 파일이 존재하는지 확인
        if not os.path.exists(filepath):
            return True  # 파일이 삭제되었으면 처리된 것으로 간주
        
        # 파일 정보 확인
        try:
            file_stat = os.stat(filepath)
            stored_info = processed_state[filepath]
            
            # 파일 크기나 수정 시간이 변경되었으면 다시 처리
            if (file_stat.st_size != stored_info.get('file_size') or 
                file_stat.st_mtime != stored_info.get('file_mtime')):
                print(f"[INFO] Video file changed, will reprocess: {os.path.basename(filepath)}")
                return False
            
            return True
        except Exception as e:
            print(f"[WARNING] Failed to check video file state: {str(e)}")
            return False
    
    def is_video_processing(self, video_results_dir="/app/shared_images/video_results"):
        """
        현재 처리 중인 비디오가 있는지 확인
        
        Args:
            video_results_dir: 비디오 결과 디렉토리
            
        Returns:
            bool: 처리 중인 비디오가 있으면 True
        """
        if not os.path.exists(video_results_dir):
            return False
        
        try:
            for item in os.listdir(video_results_dir):
                item_path = os.path.join(video_results_dir, item)
                if os.path.isdir(item_path):
                    info_file = os.path.join(item_path, "video_info.json")
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                # 파일이 큰 경우를 대비해 첫 부분만 읽기
                                content = f.read(5000)  # 처음 5KB만 읽기
                                if '"status": "processing"' in content:
                                    return True
                        except:
                            continue
        except:
            pass
        
        return False
    
    def watch_video_directory(self, video_dir="/app/videos", latitude=None, longitude=None, frame_interval=1):
        """
        Watch video directory and process new video files
        한 번에 하나의 비디오만 처리하여 리소스 효율성 향상
        
        Args:
            video_dir: Directory to watch for video files
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            frame_interval: Process every N frames (default: 1, 모든 프레임 처리)
        """
        if not os.path.exists(video_dir):
            os.makedirs(video_dir, exist_ok=True)
            print(f"[INFO] Created video directory: {video_dir}")
        
        print(f"[INFO] Watching video directory: {video_dir}")
        print(f"[INFO] Place video files (.mp4, .avi, .mov, .mkv) in this directory to process them")
        print(f"[INFO] Frame interval: {frame_interval} (모든 프레임 처리)")
        print(f"[INFO] 한 번에 하나의 비디오만 처리합니다.")
        
        # 처리된 동영상 상태 파일 경로
        state_file = "/app/processed_videos.json"
        
        # 처리된 동영상 목록 로드
        processed_state = self.load_processed_videos(state_file)
        print(f"[INFO] Found {len(processed_state)} previously processed videos")
        
        while True:
            # 현재 처리 중인 비디오가 있으면 대기
            if self.is_video_processing():
                time.sleep(10)  # 처리 중이면 10초 대기
                continue
            
            # Check for new video files
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI', '.MOV', '.MKV']
            new_video_found = False
            
            for filename in os.listdir(video_dir):
                filepath = os.path.join(video_dir, filename)
                
                # 디렉토리는 건너뛰기
                if not os.path.isfile(filepath):
                    continue
                
                # 이미 처리된 파일인지 확인
                if self.is_video_processed(filepath, processed_state):
                    continue
                
                # Check if it's a video file
                if any(filename.lower().endswith(ext.lower()) for ext in video_extensions):
                    print(f"\n[INFO] Found new video file: {filename}")
                    print(f"[INFO] Starting processing (frame_interval={frame_interval})...")
                    try:
                        # frame_interval을 사용하여 프레임 샘플링 (속도 향상)
                        self.process_video(filepath, latitude, longitude, frame_interval=frame_interval)
                        # 처리 완료 후 상태 저장
                        self.save_processed_video(filepath, state_file)
                        # 메모리 상태도 업데이트
                        processed_state = self.load_processed_videos(state_file)
                        print(f"[INFO] Video processing completed: {filename}")
                    except Exception as e:
                        print(f"[ERROR] Failed to process video {filename}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    
                    new_video_found = True
                    break  # 한 번에 하나만 처리
            
            if not new_video_found:
                time.sleep(5)  # 새 비디오가 없으면 5초 대기
    
    def get_new_detected_images_count(self, days=1):
        """
        최근 N일 동안 새로 감지된 포트홀 이미지 개수 확인
        
        Args:
            days: 확인할 일수 (기본값: 1일, 즉 어제부터 오늘까지)
            
        Returns:
            int: 새로 감지된 이미지 개수
        """
        try:
            # 어제 00시부터 오늘 00시까지의 데이터 확인
            end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=days)
            
            count = Pothole.objects.filter(
                detected_at__gte=start_date,
                detected_at__lt=end_date,
                image_path__isnull=False
            ).exclude(
                image_path=''
            ).values('image_path').distinct().count()
            
            print(f"[INFO] New detected images in last {days} day(s): {count}")
            return count
            
        except Exception as e:
            print(f"[ERROR] Failed to get new detected images count: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def prepare_finetune_dataset(self):
        """
        파인튜닝을 위한 데이터셋 준비
        데이터베이스에서 검증된 포트홀 이미지와 바운딩 박스 정보를 추출
        
        Returns:
            str: YOLO 형식의 데이터셋 디렉토리 경로 또는 None
        """
        try:
            # 데이터셋 디렉토리 생성
            dataset_dir = "/app/models/finetune_dataset"
            images_dir = os.path.join(dataset_dir, "images", "train")
            labels_dir = os.path.join(dataset_dir, "labels", "train")
            
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(labels_dir, exist_ok=True)
            
            # 1. 관리자가 승인한 검증된 포트홀 이미지와 바운딩 박스 정보 조회 (포지티브 샘플)
            positive_potholes = Pothole.objects.filter(
                validation_result=True,
                approved_for_training=True,
                image_path__isnull=False
            ).exclude(
                image_path=''
            ).exclude(
                bbox_x1__isnull=True,
                bbox_y1__isnull=True,
                bbox_x2__isnull=True,
                bbox_y2__isnull=True
            ).values(
                'image_path', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2'
            ).distinct().order_by('-detected_at')[:1000]
            
            positive_results = [
                (item['image_path'], item['bbox_x1'], item['bbox_y1'], item['bbox_x2'], item['bbox_y2'])
                for item in positive_potholes
            ]
            
            # 2. 관리자가 거부한 이미지 또는 검토되지 않은 이미지 조회 (배경 이미지/네거티브 샘플)
            # 이 이미지들은 합성 포트홀을 추가할 후보가 됨
            background_potholes = Pothole.objects.filter(
                Q(approved_for_training=False) | Q(approved_for_training__isnull=True),
                image_path__isnull=False
            ).exclude(
                image_path=''
            ).values('image_path').distinct().order_by('-detected_at')[:500]
            
            background_results = [(item['image_path'],) for item in background_potholes]
            
            # 3. 합성 포트홀 생성 (선택사항 - 배경 이미지에 합성)
            use_synthetic = os.getenv('USE_SYNTHETIC_POTHOLES', 'false').lower() == 'true'
            if use_synthetic and len(background_results) > 0:
                print("[INFO] 합성 포트홀 생성 활성화됨")
                try:
                    generator = SyntheticPotholeGenerator()
                    synthetic_dir = os.path.join(dataset_dir, "synthetic_temp")
                    os.makedirs(synthetic_dir, exist_ok=True)
                    
                    # 배경 이미지 디렉토리에 복사 (임시)
                    temp_road_dir = os.path.join(synthetic_dir, "road_images")
                    os.makedirs(temp_road_dir, exist_ok=True)
                    temp_images_dir = os.path.join(synthetic_dir, "images")
                    temp_labels_dir = os.path.join(synthetic_dir, "labels")
                    
                    # 배경 이미지 일부를 합성용으로 사용
                    synthetic_count = min(100, len(background_results))  # 최대 100개
                    for i, (img_path,) in enumerate(background_results[:synthetic_count]):
                        if os.path.exists(img_path):
                            filename = os.path.basename(img_path)
                            dest_path = os.path.join(temp_road_dir, filename)
                            if os.path.exists(img_path):
                                shutil.copy2(img_path, dest_path)
                    
                    # 합성 데이터 생성
                    synth_stats = generator.generate_synthetic_dataset(
                        road_images_dir=temp_road_dir,
                        output_images_dir=temp_images_dir,
                        output_labels_dir=temp_labels_dir,
                        num_potholes_per_image=1,
                        min_scale=0.5,
                        max_scale=1.5,
                        class_id=0
                    )
                    
                    # 합성 이미지를 학습 데이터셋에 추가
                    if synth_stats['processed_images'] > 0:
                        for img_file in os.listdir(temp_images_dir):
                            if img_file.endswith(('.jpg', '.jpeg', '.png')):
                                src_img = os.path.join(temp_images_dir, img_file)
                                dest_img = os.path.join(images_dir, f"synthetic_{img_file}")
                                shutil.copy2(src_img, dest_img)
                                
                                # 라벨도 복사
                                label_file = os.path.splitext(img_file)[0] + '.txt'
                                src_label = os.path.join(temp_labels_dir, label_file)
                                if os.path.exists(src_label):
                                    dest_label = os.path.join(labels_dir, f"synthetic_{label_file}")
                                    shutil.copy2(src_label, dest_label)
                        
                        print(f"[OK] 합성 포트홀 {synth_stats['processed_images']}개 추가됨")
                    
                    # 임시 디렉토리 정리
                    shutil.rmtree(synthetic_dir, ignore_errors=True)
                except Exception as e:
                    print(f"[WARNING] 합성 포트홀 생성 실패 (계속 진행): {str(e)}")
            
            if len(positive_results) == 0:
                print("[WARNING] No validated pothole images found for fine-tuning")
                return None
            
            print(f"[INFO] Preparing dataset with {len(positive_results)} positive images and {len(background_results)} background images")
            
            # 이미지 복사 및 라벨 파일 생성
            image_count = 0
            
            # 1. 포지티브 샘플 (승인된 포트홀 이미지) 처리
            for db_image_path, bbox_x1, bbox_y1, bbox_x2, bbox_y2 in positive_results:
                try:
                    # 원본 이미지 경로 확인
                    image_path = db_image_path
                    
                    # 절대 경로가 아니면 shared_images에서 찾기
                    if not os.path.isabs(image_path):
                        filename = os.path.basename(image_path)
                        image_path = f"/app/shared_images/{filename}"
                    
                    # 경로가 존재하지 않으면 shared_images에서 파일명으로 찾기
                    if not os.path.exists(image_path):
                        filename = os.path.basename(db_image_path)
                        alt_paths = [
                            f"/app/shared_images/{filename}",
                            f"/app/shared_images/{os.path.basename(image_path)}",
                            db_image_path
                        ]
                        found = False
                        for alt_path in alt_paths:
                            if os.path.exists(alt_path):
                                image_path = alt_path
                                found = True
                                break
                        if not found:
                            continue
                    
                    # 이미지 로드하여 크기 확인
                    img = cv2.imread(image_path)
                    if img is None:
                        continue
                    
                    img_height, img_width = img.shape[:2]
                    
                    # YOLO 형식으로 바운딩 박스 변환 (normalized center x, center y, width, height)
                    # 클래스는 0 (포트홀)
                    center_x = ((bbox_x1 + bbox_x2) / 2.0) / img_width
                    center_y = ((bbox_y1 + bbox_y2) / 2.0) / img_height
                    width = (bbox_x2 - bbox_x1) / img_width
                    height = (bbox_y2 - bbox_y1) / img_height
                    
                    # 값 검증 (0~1 범위)
                    center_x = max(0, min(1, center_x))
                    center_y = max(0, min(1, center_y))
                    width = max(0, min(1, width))
                    height = max(0, min(1, height))
                    
                    # 이미지 복사
                    image_filename = f"pothole_{image_count:06d}.jpg"
                    dest_image_path = os.path.join(images_dir, image_filename)
                    shutil.copy2(image_path, dest_image_path)
                    
                    # 라벨 파일 생성
                    label_filename = f"pothole_{image_count:06d}.txt"
                    label_path = os.path.join(labels_dir, label_filename)
                    with open(label_path, 'w') as f:
                        f.write(f"0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
                    
                    image_count += 1
                    
                except Exception as e:
                    print(f"[WARNING] Failed to process positive image {image_path}: {str(e)}")
                    continue
            
            positive_count = image_count
            
            # 2. 배경 이미지 (승인되지 않은 이미지) 처리 - 라벨 파일 없이 추가
            background_count = 0
            for (db_image_path,) in background_results:
                try:
                    # 원본 이미지 경로 확인
                    image_path = db_image_path
                    
                    # 절대 경로가 아니면 shared_images에서 찾기
                    if not os.path.isabs(image_path):
                        filename = os.path.basename(image_path)
                        image_path = f"/app/shared_images/{filename}"
                    
                    # 경로가 존재하지 않으면 shared_images에서 파일명으로 찾기
                    if not os.path.exists(image_path):
                        filename = os.path.basename(db_image_path)
                        alt_paths = [
                            f"/app/shared_images/{filename}",
                            f"/app/shared_images/{os.path.basename(image_path)}",
                            db_image_path
                        ]
                        found = False
                        for alt_path in alt_paths:
                            if os.path.exists(alt_path):
                                image_path = alt_path
                                found = True
                                break
                        if not found:
                            continue
                    
                    # 이미지 로드하여 크기 확인
                    img = cv2.imread(image_path)
                    if img is None:
                        continue
                    
                    # 배경 이미지 복사 (라벨 파일 없음)
                    image_filename = f"background_{background_count:06d}.jpg"
                    dest_image_path = os.path.join(images_dir, image_filename)
                    shutil.copy2(image_path, dest_image_path)
                    
                    # 빈 라벨 파일 생성 (YOLO 형식에서 배경 이미지는 라벨 파일이 비어있음)
                    label_filename = f"background_{background_count:06d}.txt"
                    label_path = os.path.join(labels_dir, label_filename)
                    with open(label_path, 'w') as f:
                        # 빈 파일 (배경 이미지는 객체가 없음)
                        pass
                    
                    background_count += 1
                    image_count += 1
                    
                except Exception as e:
                    print(f"[WARNING] Failed to process background image {image_path}: {str(e)}")
                    continue
            
            # 3. 합성 포트홀 생성 (선택사항 - 배경 이미지에 합성)
            use_synthetic = os.getenv('USE_SYNTHETIC_POTHOLES', 'false').lower() == 'true'
            synthetic_count = 0
            if use_synthetic and len(background_results) > 0:
                print("[INFO] 합성 포트홀 생성 활성화됨")
                try:
                    generator = SyntheticPotholeGenerator()
                    
                    # 배경 이미지 일부를 합성용으로 사용 (최대 100개)
                    synthetic_candidates = min(100, len(background_results))
                    print(f"[INFO] {synthetic_candidates}개의 배경 이미지에 합성 포트홀 생성 중...")
                    
                    for i, (img_path,) in enumerate(background_results[:synthetic_candidates]):
                        try:
                            # 원본 이미지 경로 확인
                            image_path = img_path
                            if not os.path.isabs(image_path):
                                filename = os.path.basename(image_path)
                                image_path = f"/app/shared_images/{filename}"
                            
                            if not os.path.exists(image_path):
                                filename = os.path.basename(img_path)
                                alt_path = f"/app/shared_images/{filename}"
                                if os.path.exists(alt_path):
                                    image_path = alt_path
                                else:
                                    continue
                            
                            # 도로 이미지 로드
                            road_image = cv2.imread(image_path)
                            if road_image is None:
                                continue
                            
                            # 포트홀 생성 및 합성
                            pothole_size = (random.randint(100, 300), random.randint(100, 300))
                            pothole_image = generator._generate_pothole_texture(pothole_size, "asphalt")
                            
                            # 랜덤 파라미터
                            scale = random.uniform(0.5, 1.5)
                            rotation = random.uniform(-30, 30)
                            blend_mode = random.choice(["normal", "multiply", "overlay"])
                            
                            # 합성
                            result_image, bbox = generator.composite_pothole_on_road(
                                road_image, pothole_image,
                                position=None,  # 랜덤 위치
                                scale=scale,
                                rotation=rotation,
                                blend_mode=blend_mode
                            )
                            
                            # YOLO 형식으로 변환
                            road_h, road_w = road_image.shape[:2]
                            yolo_bbox = generator.convert_bbox_to_yolo(bbox, road_w, road_h)
                            
                            # 결과 저장
                            image_filename = f"synthetic_{synthetic_count:06d}.jpg"
                            dest_image_path = os.path.join(images_dir, image_filename)
                            cv2.imwrite(dest_image_path, result_image)
                            
                            # 라벨 저장
                            label_filename = f"synthetic_{synthetic_count:06d}.txt"
                            label_path = os.path.join(labels_dir, label_filename)
                            generator.save_yolo_label(label_path, 0, yolo_bbox)
                            
                            synthetic_count += 1
                            image_count += 1
                            
                        except Exception as e:
                            print(f"[WARNING] 합성 포트홀 생성 실패 ({img_path}): {str(e)}")
                            continue
                    
                    if synthetic_count > 0:
                        print(f"[OK] 합성 포트홀 {synthetic_count}개 추가됨")
                    
                except Exception as e:
                    print(f"[WARNING] 합성 포트홀 생성 프로세스 실패 (계속 진행): {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            if positive_count < 10:
                print(f"[WARNING] Not enough positive images for fine-tuning: {positive_count} < 10")
                return None
            
            # Train/Validation 분리를 위한 디렉토리 생성
            train_images_dir = os.path.join(dataset_dir, "images", "train")
            train_labels_dir = os.path.join(dataset_dir, "labels", "train")
            val_images_dir = os.path.join(dataset_dir, "images", "val")
            val_labels_dir = os.path.join(dataset_dir, "labels", "val")
            
            os.makedirs(val_images_dir, exist_ok=True)
            os.makedirs(val_labels_dir, exist_ok=True)
            
            # 데이터를 Train/Validation으로 분리 (80:20)
            # 포지티브 샘플과 배경 샘플을 각각 분리
            import random
            random.seed(42)  # 재현성을 위한 시드 설정
            
            # 포지티브 샘플 파일 목록
            positive_files = [f for f in os.listdir(train_images_dir) if f.startswith("pothole_")]
            background_files = [f for f in os.listdir(train_images_dir) if f.startswith("background_")]
            
            # 포지티브 샘플 분리 (80% train, 20% val)
            random.shuffle(positive_files)
            positive_val_count = max(1, int(len(positive_files) * 0.2))
            positive_val_files = positive_files[:positive_val_count]
            positive_train_files = positive_files[positive_val_count:]
            
            # 배경 샘플 분리 (80% train, 20% val)
            random.shuffle(background_files)
            background_val_count = max(1, int(len(background_files) * 0.2))
            background_val_files = background_files[:background_val_count]
            background_train_files = background_files[background_val_count:]
            
            # Validation 세트로 이동
            for filename in positive_val_files + background_val_files:
                # 이미지 이동
                src_img = os.path.join(train_images_dir, filename)
                dst_img = os.path.join(val_images_dir, filename)
                if os.path.exists(src_img):
                    shutil.move(src_img, dst_img)
                
                # 라벨 이동
                label_filename = filename.replace(".jpg", ".txt")
                src_label = os.path.join(train_labels_dir, label_filename)
                dst_label = os.path.join(val_labels_dir, label_filename)
                if os.path.exists(src_label):
                    shutil.move(src_label, dst_label)
            
            print(f"[INFO] Dataset split: Train={len(positive_train_files)+len(background_train_files)} images, Val={len(positive_val_files)+len(background_val_files)} images")
            
            # 데이터셋 설정 파일 생성 (data.yaml)
            data_yaml_path = os.path.join(dataset_dir, "data.yaml")
            with open(data_yaml_path, 'w') as f:
                f.write(f"""path: {dataset_dir}
train: images/train
val: images/val

nc: 1
names: ['pothole']
""")
            
            print(f"[OK] Dataset prepared: {positive_count} positive images, {background_count} background images, {synthetic_count} synthetic images (total: {image_count})")
            return dataset_dir
            
        except Exception as e:
            print(f"[ERROR] Failed to prepare fine-tuning dataset: {str(e)}")
            return None
    
    def finetune_model(self):
        """
        YOLO 모델 파인튜닝 실행
        """
        try:
            print("[INFO] Starting model fine-tuning...")
            
            # 데이터셋 준비
            dataset_dir = self.prepare_finetune_dataset()
            if dataset_dir is None:
                print("[ERROR] Failed to prepare dataset for fine-tuning")
                return False
            
            # 현재 모델 백업
            if self.current_model_path and os.path.exists(self.current_model_path):
                backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
                backup_path = os.path.join(self.backup_model_dir, backup_filename)
                shutil.copy2(self.current_model_path, backup_path)
                print(f"[OK] Model backed up to: {backup_path}")
            
            # 파인튜닝 실행
            print("[INFO] Training model...")
            
            # 현재 모델을 기반으로 파인튜닝
            base_model = self.yolo_model if self.yolo_model else YOLO("yolov8n.pt")
            
            # 파인튜닝 설정 (과적합 방지 포함)
            results = base_model.train(
                data=os.path.join(dataset_dir, "data.yaml"),
                epochs=100,  # 더 많은 에포크 (Early stopping으로 조기 종료)
                imgsz=640,
                batch=16,
                device=self.device,
                project="/app/models",
                name="finetune",
                exist_ok=True,
                patience=15,  # Early stopping patience 증가
                save=True,
                plots=True,
                # 과적합 방지 설정
                lr0=0.001,  # 초기 학습률 (낮게 설정)
                lrf=0.01,  # 최종 학습률 비율
                momentum=0.937,  # 모멘텀
                weight_decay=0.0005,  # 가중치 감쇠 (L2 정규화)
                warmup_epochs=3,  # 워밍업 에포크
                warmup_momentum=0.8,  # 워밍업 모멘텀
                warmup_bias_lr=0.1,  # 워밍업 바이어스 학습률
                # 데이터 증강 설정 (과적합 방지)
                hsv_h=0.015,  # HSV-Hue 증강 (색상 변화)
                hsv_s=0.7,  # HSV-Saturation 증강 (채도 변화)
                hsv_v=0.4,  # HSV-Value 증강 (밝기 변화)
                degrees=10,  # 회전 각도 (±10도)
                translate=0.1,  # 이동 (10%)
                scale=0.5,  # 크기 조정 (50% 범위)
                shear=2,  # 전단 변환 (±2도)
                perspective=0.0,  # 원근 변환 (비활성화)
                flipud=0.0,  # 상하 뒤집기 (비활성화 - 포트홀은 위아래 의미 있음)
                fliplr=0.5,  # 좌우 뒤집기 (50% 확률)
                mosaic=0.5,  # 모자이크 증강 (50% 확률)
                mixup=0.1,  # MixUp 증강 (10% 확률)
                copy_paste=0.0,  # Copy-Paste 증강 (비활성화)
                # 정규화
                dropout=0.0,  # Dropout (YOLOv8에서는 기본적으로 사용 안 함)
                val=True,  # 검증 세트 사용
                split=0.2,  # Train/Validation 분리 (20%를 검증용으로)
            )
            
            # 최적 모델 경로 찾기
            finetune_model_path = os.path.join("/app/models/finetune", "weights", "best.pt")
            if not os.path.exists(finetune_model_path):
                finetune_model_path = os.path.join("/app/models/finetune", "weights", "last.pt")
            
            if os.path.exists(finetune_model_path):
                # 새 모델을 기본 모델 위치로 복사
                new_model_path = "/app/models/best2.pt"
                shutil.copy2(finetune_model_path, new_model_path)
                print(f"[OK] Fine-tuned model saved to: {new_model_path}")
                
                # 새 모델 로드
                self.load_yolo_model(new_model_path)
                print("[OK] New fine-tuned model loaded")
                
                self.last_finetune_date = datetime.now()
                return True
            else:
                print("[ERROR] Fine-tuned model not found")
                return False
                
        except Exception as e:
            print(f"[ERROR] Fine-tuning failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_and_finetune(self):
        """
        새로 감지된 이미지 개수를 확인하고, 조건에 맞으면 파인튜닝 실행
        """
        try:
            print("[INFO] Checking for new detected images...")
            
            # 어제부터 오늘까지 새로 감지된 이미지 개수 확인
            new_count = self.get_new_detected_images_count(days=1)
            
            if new_count >= self.finetune_threshold:
                print(f"[INFO] Found {new_count} new images (threshold: {self.finetune_threshold})")
                print("[INFO] Starting fine-tuning...")
                
                success = self.finetune_model()
                
                if success:
                    print("[OK] Fine-tuning completed successfully")
                else:
                    print("[ERROR] Fine-tuning failed")
            else:
                print(f"[INFO] Not enough new images for fine-tuning: {new_count} < {self.finetune_threshold}")
                
        except Exception as e:
            print(f"[ERROR] Error in check_and_finetune: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def setup_scheduler(self):
        """스케줄러 설정 - 매일 00시에 파인튜닝 체크"""
        try:
            # 매일 00시에 실행
            self.scheduler.add_job(
                func=self.check_and_finetune,
                trigger=CronTrigger(hour=0, minute=0),
                id='daily_finetune_check',
                name='Daily Fine-tuning Check',
                replace_existing=True
            )
            print("[OK] Scheduler configured: Daily fine-tuning check at 00:00")
        except Exception as e:
            print(f"[ERROR] Failed to setup scheduler: {str(e)}")
    
    def run(self):
        """Main loop - watch video directory and process videos"""
        print("[INFO] AI Core starting...")
        print(f"[INFO] NPU Worker URL: {self.npu_worker_url}")
        
        # Watch video directory for new files
        video_dir = os.getenv("VIDEO_DIR", "/app/videos")
        latitude = os.getenv("DEFAULT_LATITUDE", None)
        longitude = os.getenv("DEFAULT_LONGITUDE", None)
        
        # Frame interval 설정 (환경 변수 또는 기본값)
        # 기본값: 1 (모든 프레임 처리)
        frame_interval = int(os.getenv("FRAME_INTERVAL", "1"))
        
        if latitude:
            latitude = float(latitude)
        if longitude:
            longitude = float(longitude)
        
        self.watch_video_directory(video_dir, latitude, longitude, frame_interval=frame_interval)

if __name__ == "__main__":
    ai_core = AICore()
    ai_core.run()

