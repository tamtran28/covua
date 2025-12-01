import streamlit as st
import chess
import chess.svg
import random
import base64

# ======================
#  HÀM TẠO BÀI TẬP ĐƠN GIẢN
# ======================

def random_mate_position():
    """Tạo bài chiếu bí 1–2 nước (dạng dễ)."""
    puzzles = [
        {
            "fen": "6k1/5ppp/8/8/8/2Q5/5PPP/6K1 w - - 0 1",
            "solution": "c3c8",
            "type": "Mate in 2"
        },
        {
            "fen": "8/8/5kp1/7p/8/6K1/7P/6Q1 w - - 0 1",
            "solution": "g1g6",
            "type": "Mate in 1"
        },
        {
            "fen": "6k1/5ppp/8/8/8/5Q2/5PPP/6K1 w - - 0 1",
            "solution": "f3a8",
            "type": "Mate in 2"
        }
    ]
    return random.choice(puzzles)

def random_tactic_position():
    """Tạo bài chiến thuật dễ – fork, mất quân."""
    puzzles = [
        {
            "fen": "rnbqkbnr/pppp1ppp/8/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 1 3",
            "solution": "f3e5",
            "type": "Winning a pawn"
        },
        {
            "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 2 4",
            "solution": "c3e4",
            "type": "Fork"
        }
    ]
    return random.choice(puzzles)


# ======================
#  HÀM HIỂN THỊ BÀN CỜ SVG
# ======================

def render_board(fen):
    board = chess.Board(fen)
    svg = chess.svg.board(board=board, size=480)
    b64 = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'


# ======================
#  GIAO DIỆN STREAMLIT
# ======================

st.set_page_config(page_title="Chess Trainer", page_icon="♟")

st.title("♟ Chương trình tạo bài tập cờ vua – Streamlit")

mode = st.selectbox(
    "Chọn loại bài tập:",
    ["Chiếu Bí", "Chiến Thuật"]
)

if st.button("🎲 Tạo bài tập mới"):
    if mode == "Chiếu Bí":
        puzzle = random_mate_position()
    else:
        puzzle = random_tactic_position()

    st.session_state["puzzle"] = puzzle
    st.session_state["answered"] = False

if "puzzle" in st.session_state:

    p = st.session_state["puzzle"]

    st.subheader(f"Loại bài tập: **{p['type']}**")
    st.write(f"**FEN:** `{p['fen']}`")

    st.markdown(render_board(p["fen"]), unsafe_allow_html=True)

    move = st.text_input("Nhập nước đi theo dạng UCI (ví dụ: e2e4, g1f3):")

    if st.button("Kiểm tra ☑️"):
        if move == p["solution"]:
            st.success("✔ Chính xác! Bạn đã tìm được nước đi đúng.")
        else:
            st.error("❌ Chưa đúng. Hãy thử lại.")

    if st.button("Xem đáp án 👀"):
        st.info(f"Đáp án đúng: **{p['solution']}**")

