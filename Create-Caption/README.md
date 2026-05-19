# Create-Caption

## 🚀 프로젝트 개요 (Overview)

이 프로젝트는 다양한 최신 Vision-Language 모델(VLM)들을 활용하여 이미지에 대한 상세하고 정확한 캡션을 생성하는 과정을 탐구합니다. 특히 YOLOv8 객체 탐지 결과를 다른 VLM 모델의 프롬프트로 활용하여 캡션의 정확도와 풍부함을 향상시키는 방법을 실험했습니다. 여러 캡션 생성 모델의 성능을 비교하고 최적의 조합을 찾는 데 초점을 맞추고 있습니다.

## ✨ 주요 기능 (Features)

-   **멀티모달 이미지 캡션 생성**: YOLOv8 객체 탐지 결과를 GPT-4o, Kosmos-2와 같은 VLM 모델에 통합하여 상세하고 문맥에 맞는 캡션 생성.
-   **다양한 VLM 모델 비교**: BLIP, InstructBLIP, CLIP Interrogator 등 여러 모델들의 캡션 생성 성능을 비교 분석하여 각 모델의 특성과 강점 파악.
-   **캡션 후처리**: 생성된 캡션의 품질을 향상시키기 위한 후처리 및 정리 과정 포함.

## 🤖 사용된 모델 및 기술 스택 (Models & Tech Stack)

이 프로젝트에서는 이미지 분석 및 캡션 생성을 위해 다음과 같은 최신 인공지능 모델과 기술을 사용했습니다.

### 모델 아키텍처

-   **YOLOv8**: 이미지 내 객체를 탐지하고 바운딩 박스와 클래스 확률을 제공하여, 이를 다른 캡션 모델의 입력으로 활용합니다. 예를 들어 '나무전체', '수관', '꽃', '열매', '기둥' 등을 정확하게 식별합니다. [【1】](about:blank)
-   **GPT-4o (OpenAI)**: YOLO 탐지 정보를 포함한 프롬프트를 사용하여 이미지를 자세하고 간결하게 설명하는 데 활용됩니다. 이를 통해 보다 문맥적이고 정확한 캡션을 생성합니다. [【1】](about:blank)[【3】](about:blank)
-   **Kosmos-2**: 이미지 캡션 생성에 사용된 또 다른 Vision-Language 모델입니다. 생성된 캡션의 추가적인 정리 과정을 통해 품질을 높입니다. [【2】](about:blank)[【5】](about:blank)
-   **BLIP (Bootstrapping Language-Image Pre-training)**: 이미지 캡션의 기본 성능을 제공하는 모델 중 하나로, 다른 모델들과의 비교를 위해 사용됩니다. [【4】](about:blank)
-   **InstructBLIP**: BLIP의 지시 추론 능력을 강화한 모델로, 상세한 캡션을 생성하며 비교 대상 모델로 활용됩니다. [【4】](about:blank)
-   **CLIP Interrogator**: 이미지의 시각적 특징을 기반으로 다양한 키워드와 스타일을 조합하여 프롬프트를 생성하거나 캡션을 제공하는 데 사용됩니다. [【4】](about:blank)

### 주요 기술 및 라이브러리

-   **Python**: 프로젝트의 주요 개발 언어.
-   **OpenAI API**: GPT-4o 모델과의 연동 및 활용.
-   **Hugging Face Transformers**: BLIP, InstructBLIP, Kosmos-2 등 다양한 VLM 모델의 불러오기 및 사용.
-   **Pillow (PIL)**: 이미지 처리 및 관리를 위한 라이브러리.
-   **google-colab / userdata**: Colab 환경에서 API 키를 안전하게 관리하고 개발을 진행합니다.
