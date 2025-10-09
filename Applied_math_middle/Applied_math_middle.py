import streamlit as st
import os
import random
import re
from PIL import Image

# --- Functions ---

@st.cache_data
def load_image_pairs(data_folder="Data_Applied_math_middle"):
    """
    Loads and pairs front (problem) and back (solution) images from a directory.
    It sorts files numerically to ensure correct pairing (e.g., f1.png with b1.png).
    """
    front_dir = os.path.join(data_folder, "front")
    back_dir = os.path.join(data_folder, "back")

    if not os.path.isdir(front_dir) or not os.path.isdir(back_dir):
        st.error(f"エラー: '{front_dir}' または '{back_dir}' フォルダが見つかりません。")
        st.stop()

    def sort_key(filename):
        # Extracts numbers from the filename for correct sorting
        numbers = re.findall(r'\d+', filename)
        return int(numbers[0]) if numbers else 0

    front_images = sorted(
        [os.path.join(front_dir, f) for f in os.listdir(front_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))],
        key=sort_key
    )
    back_images = sorted(
        [os.path.join(back_dir, f) for f in os.listdir(back_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))],
        key=sort_key
    )

    if len(front_images) != len(back_images) or not front_images:
        st.warning("問題と解答の画像の数が一致しないか、画像がありません。")
        return []

    return list(zip(front_images, back_images))


def initialize_session_state():
    """Initializes the session state."""
    if 'image_pairs' not in st.session_state:
        st.session_state.image_pairs = load_image_pairs()
    
    if 'card_indices_master' not in st.session_state:
        # This will hold the user's selected range from the sidebar
        st.session_state.card_indices_master = list(range(len(st.session_state.image_pairs)))

    if 'card_indices_active' not in st.session_state:
        # This is the list of cards currently being viewed (can be filtered)
        st.session_state.card_indices_active = st.session_state.card_indices_master
    
    if 'total_cards' not in st.session_state:
        st.session_state.total_cards = len(st.session_state.card_indices_active)
    
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    
    if 'is_flipped' not in st.session_state:
        st.session_state.is_flipped = False
    
    if 'card_status' not in st.session_state:
        # Status is tracked by the original index of the image pair
        st.session_state.card_status = {i: "未確認" for i in range(len(st.session_state.image_pairs))}
    
    if 'shuffle_on' not in st.session_state:
        st.session_state.shuffle_on = False


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
        if st.session_state.card_status[idx] != "✅ 理解済み"
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
        div.stButton > button { background-color: #2E2E2E; color: #E0E0E0; border: 1px solid #444; border-radius: 10px; padding: 0.6em 1.2em; font-size: 16px; font-weight: 500; }
        div.stButton > button:hover { background-color: #444; border: 1px solid #666; color: #FFFFFF; }
        section[data-testid="stSidebar"] { background-color: #1A1A1A; border-right: 1px solid #333; }
        .stImage > img { background-color: white; border-radius: 10px; }
        .main .block-container { max-width: 90%; padding-left: 2rem; padding-right: 2rem; }
    </style>
""", unsafe_allow_html=True)

initialize_session_state()

# --- Sidebar Controls ---
with st.sidebar:
    st.header("⚙️ 設定")
    st.subheader("カード範囲")
    total_cards_overall = len(st.session_state.image_pairs)
    start_num = st.number_input("開始", min_value=1, max_value=total_cards_overall, value=1, step=1)
    end_num = st.number_input("終了", min_value=1, max_value=total_cards_overall, value=min(10, total_cards_overall), step=1)

    st.toggle("シャッフル", key="shuffle_on", help="選択範囲をシャッフルします。")
    if st.button("範囲を適用", use_container_width=True):
        apply_range(start_num, end_num)
        st.rerun()

    st.header("📊 進捗")
    remembered_count = list(st.session_state.card_status.values()).count("✅ 理解済み")
    repeat_count = list(st.session_state.card_status.values()).count("🔄 復習が必要")
    st.metric(label="✅ 理解済み", value=f"{remembered_count} / {total_cards_overall}")
    st.metric(label="🔄 復習が必要", value=f"{repeat_count} / {total_cards_overall}")
    if st.button("進捗をリセット", use_container_width=True):
        st.session_state.card_status = {i: "未確認" for i in range(len(st.session_state.image_pairs))}
        st.rerun()
    
    st.divider()
    
    st.header("🔄 復習モード")
    st.button("未学習・要復習カードのみ表示", on_click=filter_deck_for_review, use_container_width=True, help="「理解済み」以外のカードを抽出して表示します。")
    st.button("すべてのカードを表示", on_click=reset_to_master_deck, use_container_width=True, help="設定した範囲のすべてのカードに戻ります。")


# --- Main Flashcard Area ---
st.title("🧮 数学画像フラッシュカード")

if not st.session_state.card_indices_active:
    st.warning("表示するカードがありません。範囲を設定するか、すべてのカードを表示してください。")
else:
    original_card_index = st.session_state.card_indices_active[st.session_state.current_index]
    front_image_path, back_image_path = st.session_state.image_pairs[original_card_index]
    current_status = st.session_state.card_status[original_card_index]

    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        progress_value = (st.session_state.current_index + 1) / st.session_state.total_cards
        st.progress(progress_value, text=f"カード {st.session_state.current_index + 1} / {st.session_state.total_cards}")

        card_placeholder = st.empty()

        # Show a message when the last card is reached
        if st.session_state.current_index == st.session_state.total_cards - 1:
             st.info("最後のカードです。お疲れ様でした！復習モードで苦手なカードを再挑戦できます。")

        if not st.session_state.is_flipped:
            with card_placeholder.container(border=True):
                st.markdown(f"**状態:** {current_status}")
                st.subheader("問題:")
                try:
                    image = Image.open(front_image_path)
                    st.image(image, use_container_width=True) 
                except Exception as e:
                    st.error(f"画像を開けませんでした: {front_image_path}\nエラー: {e}")

                if st.button("答えを見る ↩️", use_container_width=True):
                    st.session_state.is_flipped = True
                    st.rerun()

        else:
            with card_placeholder.container(border=True):
                st.markdown(f"**状態:** {current_status}")
                st.subheader("解答:")
                try:
                    image = Image.open(back_image_path)
                    st.image(image, use_container_width=True)
                except Exception as e:
                    st.error(f"画像を開けませんでした: {back_image_path}\nエラー: {e}")

                if st.button("問題に戻る ↪️", use_container_width=True):
                    st.session_state.is_flipped = False
                    st.rerun()
        
        st.divider()

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