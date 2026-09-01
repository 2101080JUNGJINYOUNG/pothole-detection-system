# import cv2
# import numpy as np
# import matplotlib.pyplot as plt

# # === 설정 영역 ===
# path = 'test.png'  # <-- 이미지 경로 확인
# # =================

# img = cv2.imread(path)

# if img is None:
#     print(f"❌ 에러: '{path}' 경로에서 이미지를 찾을 수 없습니다.")
# else:
#     print("✅ 이미지 로드 성공! 전처리 비교를 시작합니다.")

#     # 1. 기본 흑백 변환 (Sobel, Canny, Laplacian용)
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     # -------------------------------------------------------
#     # A. Sobel (소벨)
#     # -------------------------------------------------------
#     sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
#     sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
#     sobel = cv2.magnitude(sobel_x, sobel_y)
#     sobel = cv2.convertScaleAbs(sobel)

#     # -------------------------------------------------------
#     # B. Canny (캐니)
#     # -------------------------------------------------------
#     canny = cv2.Canny(gray, 100, 200)

#     # -------------------------------------------------------
#     # C. Laplacian (라플라시안)
#     # -------------------------------------------------------
#     laplacian = cv2.Laplacian(gray, cv2.CV_64F)
#     laplacian = cv2.convertScaleAbs(laplacian)

#     # -------------------------------------------------------
#     # D. Color CLAHE (컬러 CLAHE) - 요청사항 반영
#     # -------------------------------------------------------
#     lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
#     l, a, b = cv2.split(lab)
    
#     # L 채널(밝기)에만 CLAHE 적용
#     clahe_obj = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
#     l_new = clahe_obj.apply(l)
    
#     merged = cv2.merge((l_new, a, b))
#     clahe_color = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

#     # -------------------------------------------------------
#     # 시각화 (Matplotlib)
#     # -------------------------------------------------------
#     # Matplotlib는 BGR이 아닌 RGB 순서를 사용하므로 변환
#     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     clahe_rgb = cv2.cvtColor(clahe_color, cv2.COLOR_BGR2RGB)

#     plt.figure(figsize=(16, 10)) # 전체 창 크기 조절

#     # 1. 원본
#     plt.subplot(2, 3, 1)
#     plt.imshow(img_rgb)
#     plt.title('1. Original')
#     plt.axis('off')

#     # 2. Sobel
#     plt.subplot(2, 3, 2)
#     plt.imshow(sobel, cmap='gray')
#     plt.title('2. Sobel (Edge Direction)')
#     plt.axis('off')

#     # 3. Canny
#     plt.subplot(2, 3, 3)
#     plt.imshow(canny, cmap='gray')
#     plt.title('3. Canny (Clean Edge)')
#     plt.axis('off')

#     # 4. Laplacian
#     plt.subplot(2, 3, 4)
#     plt.imshow(laplacian, cmap='gray')
#     plt.title('4. Laplacian (Detail/Noise)')
#     plt.axis('off')

#     # 5. Color CLAHE
#     plt.subplot(2, 3, 5)
#     plt.imshow(clahe_rgb)
#     plt.title('5. Color CLAHE (Contrast Up)')
#     plt.axis('off')

#     plt.tight_layout()
#     plt.show()



import cv2
import numpy as np
import matplotlib.pyplot as plt

def paper_preprocessing(image_path):
    # 1. 이미지 로드
    img = cv2.imread('test.png')
    if img is None:
        print("이미지를 찾을 수 없습니다.")
        return

    # ==========================================
    # 1단계: 기본 단계 (Intensity Transformation)
    # ==========================================
    
    # 1-1. Log Transformation (그림자 속 디테일 개선)
    # s = c * log(1 + r)
    img_float = img.astype(np.float32)
    c = 255 / np.log(1 + np.max(img_float))
    log_img = c * (np.log(img_float + 1))
    log_img = np.array(log_img, dtype=np.uint8)

    # 1-2. Gamma Transformation (전체적으로 어둡게, 논문 감마값 3.5)
    # s = c * r^gamma
    gamma = 3.5
    lookUpTable = np.empty((1, 256), np.uint8)
    for i in range(256):
        lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
    gamma_img = cv2.LUT(log_img, lookUpTable)

    # 1-3. Piecewise-Linear Transformation (명암 경계 명확화)
    # 논문에 구체적 파라미터가 없어 Min-Max Contrast Stretching으로 구현
    min_val = np.min(gamma_img)
    max_val = np.max(gamma_img)
    piecewise_img = ((gamma_img - min_val) / (max_val - min_val) * 255).astype(np.uint8)

    # 1-4. Grayscale 변환 (다음 단계 준비)
    gray_base = cv2.cvtColor(piecewise_img, cv2.COLOR_BGR2GRAY)

    # ==========================================
    # 2단계: 특성 추출 단계 (Feature Extraction)
    # ==========================================

    # 2-A. Superpixel (형태 강화 - 색/밝기 정보 이용)
    # 논문 조건: 기본 단계에서 grayscale 변환 전 이미지(piecewise_img) 사용
    # Segment 수: 500
    try:
        # SLIC 알고리즘 사용
        slic = cv2.ximgproc.createSuperpixelSLIC(piecewise_img, algorithm=cv2.ximgproc.SLICO, region_size=20, ruler=10.0)
        slic.iterate(10)
        mask_slic = slic.getLabelContourMask()
        
        # 슈퍼픽셀 경계가 아닌, 슈퍼픽셀로 뭉개진 이미지를 얻기 위한 평균색 적용
        labels = slic.getLabels()
        num_slic = slic.getNumberOfSuperpixels()
        superpixel_img = np.zeros_like(piecewise_img)
        
        for i in range(num_slic):
            mask = (labels == i)
            # 해당 슈퍼픽셀 영역의 평균 색상 계산
            mean_color = cv2.mean(piecewise_img, mask=mask.astype(np.uint8))[:3]
            superpixel_img[mask] = mean_color
            
        # 논문의 합성 단계를 위해 Grayscale로 변환하여 채널로 사용
        superpixel_result = cv2.cvtColor(superpixel_img, cv2.COLOR_BGR2GRAY)
        
    except AttributeError:
        print("opencv-contrib-python이 설치되지 않아 Superpixel을 건너뜁니다.")
        superpixel_result = gray_base

    # 2-B. Sobel Edge Detection (형태 강화 - 밝기 변화량 이용)
    # 논문 조건: Grayscale 이미지에 Median Filter(k=7) 후 Sobel(k=3)
    median = cv2.medianBlur(gray_base, 7)
    
    sobel_x = cv2.Sobel(median, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(median, cv2.CV_64F, 0, 1, ksize=3)
    sobel_combined = cv2.magnitude(sobel_x, sobel_y)
    sobel_result = cv2.convertScaleAbs(sobel_combined)

    # ==========================================
    # 3단계: 합성 단계 (Synthesis)
    # ==========================================
    
    # 논문 조건: 
    # R 채널: Sobel
    # G 채널: Superpixel
    # B 채널: Grayscale (기본 단계 결과)
    
    # OpenCV는 BGR 순서이므로 (Gray, Superpixel, Sobel) 순서로 합침
    final_merged = cv2.merge([gray_base, superpixel_result, sobel_result])

    # ==========================================
    # 시각화
    # ==========================================
    plt.figure(figsize=(15, 10))

    # 1. 원본
    plt.subplot(2, 3, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title("Original")
    plt.axis('off')

    # 2. Intensity Transform 결과 (Gamma 등 적용 후)
    plt.subplot(2, 3, 2)
    plt.imshow(cv2.cvtColor(piecewise_img, cv2.COLOR_BGR2RGB))
    plt.title("Step 1: Intensity Transformed")
    plt.axis('off')

    # 3. Superpixel 결과
    plt.subplot(2, 3, 3)
    plt.imshow(superpixel_result, cmap='gray')
    plt.title("Step 2-A: Superpixel (G Channel)")
    plt.axis('off')

    # 4. Sobel 결과
    plt.subplot(2, 3, 4)
    plt.imshow(sobel_result, cmap='gray')
    plt.title("Step 2-B: Sobel (R Channel)")
    plt.axis('off')

    # 5. 최종 합성 결과 (Proposed)
    # R: Sobel, G: Superpixel, B: Gray
    # 화면 표시를 위해 RGB로 변환 (Sobel이 Red로 가도록)
    final_view = cv2.merge([sobel_result, superpixel_result, gray_base])
    plt.subplot(2, 3, 5)
    plt.imshow(final_view) 
    plt.title("Step 3: Proposed Method (R:Sobel, G:Super, B:Gray)")
    plt.axis('off')

    plt.tight_layout()
    plt.show()

# 실행 예시 (경로를 수정해서 사용하세요)
paper_preprocessing('test_pothole.jpg')