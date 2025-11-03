import streamlit as st
import os
import random
import re
from PIL import Image

# --- Functions ---

@st.cache_data
def load_image_pairs(data_folder="/Users/thanongphoneanothay/X_KOSEN/YEAR4/MATH/Math_Test/Applied_math_middle/Data"):
    """
    Loads and pairs front (problem) and back (solution) images from a directory 
    by matching the extracted numerical ID (e.g., f1.png matches b1.png).
    Missing files in either directory will be safely skipped.
    """
    front_dir = os.path.join(data_folder, "front")
    back_dir = os.path.join(data_folder, "back")

    if not os.path.isdir(front_dir) or not os.path.isdir(back_dir):
        st.error(f"エラー: '{front_dir}' または '{back_dir}' フォルダが見つかりません。")
        st.stop()

    def get_file_id(filename):
        # Extracts the numerical ID from the filename
        numbers = re.findall(r'\d+', filename)
        return int(numbers[0]) if numbers else None

    image_extensions = ('png', 'jpg', 'jpeg')
    
    # 1. Map IDs to file paths for front images
    front_map = {}
    for f in os.listdir(front_dir):
        if f.lower().endswith(image_extensions):
            file_id = get_file_id(f)
            if file_id is not None:
                front_map[file_id] = os.path.join(front_dir, f)
    
    # 2. Map IDs to file paths for back images
    back_map = {}
    for f in os.listdir(back_dir):
        if f.lower().endswith(image_extensions):
            file_id = get_file_id(f)
            if file_id is not None:
                back_map[file_id] = os.path.join(back_dir, f)

    # 3. Find IDs present in BOTH directories (the intersection)
    matching_ids = sorted(list(front_map.keys() & back_map.keys()))
    
    # 4. Create the final list of paired file paths, sorted by ID
    paired_images = []
    for id in matching_ids:
        paired_images.append((front_map[id], back_map[id]))
        
    if not paired_images:
        st.warning("問題と解答のペア画像が見つかりません。ファイル名とフォルダ構成を確認してください。")
        return []

    return paired_images


def initialize_session_state():
    """Initializes the session state."""
    # データをロードし、セッションステートを初期化
    if 'image_pairs' not in st.session_state:
        st.session_state.image_pairs = load_image_pairs()
    
    total_loaded_pairs = len(st.session_state.image_pairs)

    if 'card_indices_master' not in st.session_state:
        # ロードされた全カードのインデックスを初期マスターリストとする
        st.session_state.card_indices_master = list(range(total_loaded_pairs))

    if 'card_indices_active' not in st.session_state or len(st.session_state.card_indices_active) == 0:
        st.session_state.card_indices_active = st.session_state.card_indices_master
    
    if 'total_cards' not in st.session_state:
        st.session_state.total_cards = len(st.session_state.card_indices_active)
    
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    
    if 'is_flipped' not in st.session_state:
        st.session_state.is_flipped = False
    
    if 'card_status' not in st.session_state:
        # Status is tracked by the original index (0 to total_loaded_pairs - 1)
        st.session_state.card_status = {i: "未確認" for i in range(total_loaded_pairs)}
    
    if 'shuffle_on' not in st.session_state:
        st.session_state.shuffle_on = False
    
    # カード範囲入力の初期値を設定
    if 'range_start' not in st.session_state:
        st.session_state.range_start = 1
    if 'range_end' not in st.session_state:
        st.session_state.range_end = min(10, total_loaded_pairs) if total_loaded_pairs > 0 else 1


def apply_range(start_num, end_num):
    """Applies the selected range of cards and sets it as the master list."""
    start_idx = start_num - 1
    end_idx = end_num
    
    all_indices = list(range(len(st.session_state.image_pairs)))
    
    if 0 <= start_idx < end_idx <= len(all_indices):
        master_list = all_indices[start_idx:end_idx]
        if st.session_state.shuffle_on:
            random.shuffle(master_list)
        
        st.session_state.card_indices_master = master_list
        st.session_state.card_indices_active = master_list # The active deck is the new master deck
        
        st.session_state.total_cards = len(st.session_state.card_indices_active)
        st.session_state.current_index = 0
        st.session_state.is_flipped = False
    else:
        st.sidebar.error("範囲が正しくありません。")

def filter_deck_for_review():
    """Filters the active deck to only show unmastered cards from the master list."""
    review_indices = [
        idx for idx in st.session_state.card_indices_master 
        if st.session_state.card_status.get(idx) != "✅ 理解済み"
    ]

    if not review_indices:
        st.sidebar.success("素晴らしい！この範囲に復習するカードはありません。🎉")
        return

    st.session_state.card_indices_active = review_indices
    st.session_state.total_cards = len(review_indices)
    st.session_state.current_index = 0
    st.session_state.is_flipped = False

def reset_to_master_deck():
    """Resets the active deck to the master list selected by the user."""
    st.session_state.card_indices_active = st.session_state.card_indices_master
    st.session_state.total_cards = len(st.session_state.card_indices_master)
    st.session_state.current_index = 0
    st.session_state.is_flipped = False

def next_card():
    if st.session_state.current_index < st.session_state.total_cards - 1:
        st.session_state.current_index += 1
        st.session_state.is_flipped = False


def prev_card():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.is_flipped = False


def mark_status(status):
    original_card_index = st.session_state.card_indices_active[st.session_state.current_index]
    st.session_state.card_status[original_card_index] = status


# --- UI Layout ---
st.set_page_config(page_title="数学画像フラッシュカード", layout="wide", page_icon="🧮")

# --- Custom Dark Theme CSS ---
st.markdown("""
    <style>
        body, .stApp { background-color: #121212; color: #E0E0E0; }
        .stMarkdown, .stText, .stSubheader, .stHeader, .stTitle { color: #E0E0E0 !important; }
        div.stButton > button { 
            background-color: #2E2E2E; 
            color: #E0E0E0; 
            border: 1px solid #444; 
            border-radius: 10px; 
            padding: 0.6em 1.2em; 
            font-size: 16px; 
            font-weight: 500; 
            transition: all 0.2s ease-in-out; 
        }
        div.stButton > button:hover { 
            background-color: #444; 
            border: 1px solid #666; 
            color: #FFFFFF; 
        }
        section[data-testid="stSidebar"] { 
            background-color: #1A1A1A; 
            border-right: 1px solid #333; 
        }
        .stImage > img { 
            background-color: white; 
            border-radius: 10px; 
            object-fit: contain;
            max-width: 100%;
            height: auto;
        }
        .main .block-container { 
            max-width: 90%; 
            padding-left: 2rem; 
            padding-right: 2rem; 
        }
        [data-testid="stProgressText"] {
            font-size: 1.1em;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

initialize_session_state()

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ 設定")
    st.subheader("カード範囲")
    
    total_cards_overall = len(st.session_state.image_pairs)
    
    if total_cards_overall == 0:
        st.warning("画像が読み込まれていません。フォルダパスを確認してください。")
        start_num = 1
        end_num = 1
    else:
        # セッションステートの値を使用して入力フィールドを制御
        start_num = st.number_input("開始", min_value=1, max_value=total_cards_overall, 
                                    value=st.session_state.range_start, step=1, key='input_start')
        end_num = st.number_input("終了", min_value=1, max_value=total_cards_overall, 
                                  value=st.session_state.range_end, step=1, key='input_end')


    st.toggle("シャッフル", key="shuffle_on", help="選択範囲をシャッフルします。")
    if st.button("範囲を適用", use_container_width=True):
        # 範囲をセッションステートに保存
        st.session_state.range_start = start_num
        st.session_state.range_end = end_num
        apply_range(start_num, end_num)
        st.rerun()

    st.header("📊 進捗 (現在の範囲)")
    
    # 進捗の分母を、選択された範囲内のカード数に変更
    total_cards_in_range = len(st.session_state.card_indices_master)
    
    # 進捗の分子を、選択された範囲内のカードステータスのみから計算
    status_in_range = [
        st.session_state.card_status.get(i, "未確認") 
        for i in st.session_state.card_indices_master # masterリストに含まれるインデックスのみをチェック
    ]
    
    remembered_count = status_in_range.count("✅ 理解済み")
    repeat_count = status_in_range.count("🔄 復習が必要")
    
    # 表示も範囲内のカード数を使用
    st.metric(label="✅ 理解済み", value=f"{remembered_count} / {total_cards_in_range}")
    st.metric(label="🔄 復習が必要", value=f"{repeat_count} / {total_cards_in_range}")
    
    if st.button("進捗をリセット", use_container_width=True):
        # 進捗のリセットは、ロードされている全カードに対して行われます
        st.session_state.card_status = {i: "未確認" for i in range(len(st.session_state.image_pairs))}
        st.rerun()
    
    st.divider()
    
    st.header("🔄 復習モード")
    st.button("未学習・要復習カードのみ表示", on_click=filter_deck_for_review, use_container_width=True, help="「理解済み」以外のカードを抽出して表示します。")
    st.button("すべてのカードを表示", on_click=reset_to_master_deck, use_container_width=True, help="設定した範囲のすべてのカードに戻ります。")


# --- Main Flashcard Area ---
st.title("🧮 数学画像フラッシュカード")

if not st.session_state.card_indices_active or st.session_state.total_cards == 0:
    st.warning("表示するカードがありません。範囲を設定するか、すべてのカードを表示してください。")
else:
    # Safety check for current index
    if st.session_state.current_index >= st.session_state.total_cards:
        st.session_state.current_index = max(0, st.session_state.total_cards - 1)

    original_card_index = st.session_state.card_indices_active[st.session_state.current_index]
    front_image_path, back_image_path = st.session_state.image_pairs[original_card_index]
    current_status = st.session_state.card_status.get(original_card_index, "未確認")

    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        progress_value = (st.session_state.current_index + 1) / st.session_state.total_cards
        st.progress(progress_value, text=f"カード {st.session_state.current_index + 1} / {st.session_state.total_cards}")

        card_placeholder = st.empty()

        # Show a message when the last card is reached
        if st.session_state.current_index == st.session_state.total_cards - 1:
             st.info("最後のカードです。お疲れ様でした！復習モードで苦手なカードを再挑戦できます。")

        # Determine which image to show
        current_image_path = back_image_path if st.session_state.is_flipped else front_image_path
        card_title = "解答:" if st.session_state.is_flipped else "問題:"
        
        with card_placeholder.container(border=True):
            st.markdown(f"**状態:** {current_status}")
            st.subheader(card_title)
            
            try:
                # Use PIL to open the image
                image = Image.open(current_image_path)
                st.image(image, use_container_width=True) 
            except Exception as e:
                st.error(f"画像を開けませんでした: {current_image_path}\nエラー: {e}")

            # Flip Button
            flip_label = "問題に戻る ↪️" if st.session_state.is_flipped else "答えを見る ↩️"
            if st.button(flip_label, use_container_width=True):
                st.session_state.is_flipped = not st.session_state.is_flipped
                st.rerun()
        
        st.divider()

        # Navigation and Status Buttons
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            st.button("⬅️ 前へ", on_click=prev_card, use_container_width=True, disabled=(st.session_state.current_index == 0))
        with nav_col2:
            st.button("次へ ➡️", on_click=next_card, use_container_width=True, disabled=(st.session_state.current_index == st.session_state.total_cards - 1))

        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.button("✅ 理解済み", on_click=mark_status, args=("✅ 理解済み",), use_container_width=True)
        with status_col2:
            st.button("🔄 復習が必要", on_click=mark_status, args=("🔄 復習が必要",), use_container_width=True)