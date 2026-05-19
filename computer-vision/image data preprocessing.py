import os
import json
import random
import shutil
from PIL import Image

# =========================
# 설정
# =========================
random.seed(42)

# 기존 데이터 경로
train_img_root = r"E:\b\pj1\image_data\T_V\Training\T_data"
train_label_root = r"E:\b\pj1\image_data\T_V\Training\Label"
val_img_root   = r"E:\b\pj1\image_data\T_V\Validation\V_data"
val_label_root = r"E:\b\pj1\image_data\T_V\Validation\Label"

# 새 저장 경로
new_root = r"E:\b\pj1\image_data\T_V_T"

# 클래스 매핑
class_mapping = {
    "TS_나무": "나무",
    "TS_남자사람": "남자사람",
    "TS_여자사람": "여자사람",
    "TS_집": "집",
    "VS_나무": "나무",
    "VS_남자사람": "남자사람",
    "VS_여자사람": "여자사람",
    "VS_집": "집"
}

# YOLO/Detectron2 클래스 ID
yolo_class_mapping = {
    # 집
    "집전체":0, "지붕":1, "집벽":2, "문":3, "창문":4, "굴뚝":5, "연기":6, "울타리":7, "길":8, "연못":9, "산":10,
    "나무":11, "꽃":12, "잔디":13, "태양":14,
    # 나무
    "나무전체":15, "기둥":16, "수관":17, "가지":18, "뿌리":19, "나뭇잎":20, "꽃":21, "열매":22, "그네":23,
    "새":24, "다람쥐":25, "구름":26, "달":27, "별":28,
    # 여자사람
    "사람전체":29, "머리":30, "얼굴":31, "눈":32, "코":33, "입":34, "귀":35, "머리카락":36, "목":37, "상체":38,
    "팔":39, "손":40, "다리":41, "발":42, "단추":43, "주머니":44, "운동화":45, "여자구두":46,
    # 남자사람
    "사람전체":47, "머리":48, "얼굴":49, "눈":50, "코":51, "입":52, "귀":53, "머리카락":54, "목":55, "상체":56,
    "팔":57, "손":58, "다리":59, "발":60, "단추":61, "주머니":62, "운동화":63, "남자구두":64
}

# Train/Val/Test 비율
train_ratio = 0.7
val_ratio   = 0.15
test_ratio  = 0.15

# =========================
# YOLO 변환 함수
# =========================
def convert_to_yolo(bboxes, img_width, img_height):
    yolo_lines = []
    for b in bboxes:
        label = b['label']
        if label not in yolo_class_mapping:
            continue
        class_id = yolo_class_mapping[label]
        x_center = b['x'] + b['w']/2
        y_center = b['y'] + b['h']/2
        x_center_norm = x_center / img_width
        y_center_norm = y_center / img_height
        w_norm = b['w'] / img_width
        h_norm = b['h'] / img_height
        yolo_lines.append(f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}")
    return yolo_lines

# =========================
# Detectron2 COCO 초기화
# =========================
def init_coco_json():
    categories = [{"id":v,"name":k} for k,v in yolo_class_mapping.items()]
    return {"images":[], "annotations":[], "categories":categories}

# =========================
# 데이터 처리
# =========================
def process_folder(src_img_dir, src_label_dir, class_name, dst_train_img, dst_val_img, dst_test_img,
                   dst_train_label, dst_val_label, dst_test_label,
                   coco_train, coco_val, coco_test, start_anno_id):
    
    # 폴더 생성 (불필요한 Detectron2 폴더 제거)
    for folder in [
        dst_train_img, dst_val_img, dst_test_img,
        os.path.join(dst_train_label, "YOLO"),
        os.path.join(dst_val_label, "YOLO"),
        os.path.join(dst_test_label, "YOLO")
    ]:
        os.makedirs(folder, exist_ok=True)
    
    img_files = [f for f in os.listdir(src_img_dir) if f.lower().endswith(('.jpg','.png'))]
    random.shuffle(img_files)
    
    n_total = len(img_files)
    n_train = int(n_total*train_ratio)
    n_val = int(n_total*val_ratio)
    n_test = n_total - n_train - n_val
    
    train_imgs = img_files[:n_train]
    val_imgs = img_files[n_train:n_train+n_val]
    test_imgs = img_files[n_train+n_val:]
    
    def copy_and_convert(img_list, dst_img_dir, dst_label_dir, coco_json, anno_start):
        anno_id = anno_start
        for img_file in img_list:
            img_path = os.path.join(src_img_dir, img_file)
            label_file = img_file.rsplit('.',1)[0]+".json"
            label_path = os.path.join(src_label_dir, label_file)
            
            # 이미지 복사
            shutil.copy2(img_path, os.path.join(dst_img_dir, img_file))
            
            # JSON 읽기
            with open(label_path,'r',encoding='utf-8') as f:
                data = json.load(f)
            
            # PIL로 이미지 크기 확인
            with Image.open(img_path) as img:
                width, height = img.size
            
            bboxes = data['annotations']['bbox']
            
            # YOLO
            yolo_lines = convert_to_yolo(bboxes, width, height)
            yolo_path = os.path.join(dst_label_dir,"YOLO", img_file.rsplit('.',1)[0]+".txt")
            with open(yolo_path,'w',encoding='utf-8') as f:
                f.write("\n".join(yolo_lines))
            
            # Detectron2 JSON 추가
            coco_json['images'].append({"id":anno_id, "file_name":img_file, "width":width, "height":height})
            for b in bboxes:
                label = b['label']
                if label not in yolo_class_mapping:
                    continue
                coco_json['annotations'].append({
                    "id":anno_id,
                    "image_id":anno_id,
                    "category_id":yolo_class_mapping[label],
                    "bbox":[b['x'],b['y'],b['w'],b['h']],
                    "iscrowd":0
                })
                anno_id += 1
        return anno_id
    
    start_id = 0
    start_id = copy_and_convert(train_imgs, dst_train_img, dst_train_label, coco_train, start_id)
    start_id = copy_and_convert(val_imgs, dst_val_img, dst_val_label, coco_val, start_id)
    start_id = copy_and_convert(test_imgs, dst_test_img, dst_test_label, coco_test, start_id)

# =========================
# 메인 처리
# =========================
coco_train = init_coco_json()
coco_val = init_coco_json()
coco_test = init_coco_json()

for src_folder, class_name in class_mapping.items():
    if src_folder.startswith("TS_"):
        src_img_dir = os.path.join(train_img_root, src_folder)
        src_label_dir = os.path.join(train_label_root, "TL_" + src_folder[3:])
    else:
        src_img_dir = os.path.join(val_img_root, src_folder)
        src_label_dir = os.path.join(val_label_root, "VL_" + src_folder[3:])
    
    train_dst_img = os.path.join(new_root, "train/images", class_name)
    val_dst_img   = os.path.join(new_root, "val/images", class_name)
    test_dst_img  = os.path.join(new_root, "test/images", class_name)
    
    train_dst_label = os.path.join(new_root, "train/labels", class_name)
    val_dst_label   = os.path.join(new_root, "val/labels", class_name)
    test_dst_label  = os.path.join(new_root, "test/labels", class_name)
    
    process_folder(src_img_dir, src_label_dir, class_name,
                   train_dst_img, val_dst_img, test_dst_img,
                   train_dst_label, val_dst_label, test_dst_label,
                   coco_train, coco_val, coco_test, start_anno_id=0)

# =========================
# Detectron2 JSON 저장
# =========================
os.makedirs(os.path.join(new_root, "train/labels"), exist_ok=True)
os.makedirs(os.path.join(new_root, "val/labels"), exist_ok=True)
os.makedirs(os.path.join(new_root, "test/labels"), exist_ok=True)

with open(os.path.join(new_root, "train/labels/coco_train.json"), 'w', encoding='utf-8') as f:
    json.dump(coco_train, f, ensure_ascii=False, indent=4)
with open(os.path.join(new_root, "val/labels/coco_val.json"), 'w', encoding='utf-8') as f:
    json.dump(coco_val, f, ensure_ascii=False, indent=4)
with open(os.path.join(new_root, "test/labels/coco_test.json"), 'w', encoding='utf-8') as f:
    json.dump(coco_test, f, ensure_ascii=False, indent=4)

print("✅ 변환 완료! Train/Val/Test YOLO .txt + Detectron2 COCO JSON 생성됨.")
