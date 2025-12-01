import streamlit as st
import chess
import chess.svg
import random
import requests
import base64


# ======================
# LICHESS CLOUD ENGINE API
# ======================

def get_engine_eval(fen, depth=14):
    """Dùng Stockfish 16 miễn phí từ Lichess."""
    url = "https://lichess.org/api/cloud-eval"
    r = requests.get(url, params={"fen": fen, "depth": depth})
    if r.status_code != 200:
        return None
    return r.json()


# ======================
#  TẠO VỊ TRÍ NGẪU NHIÊN
# ======================

def random_position(plies=12):
    board = chess.Board()
    for _ in range(plies):
        if board.is_game_over():
            break
        move = random.choice(list(board.legal_moves))
        board.push(move)
    return board


# ======================
#  TẠO BÀI TẬP TỰ ĐỘNG
# ======================

def generate_puzzle(depth=14, min_gap=150):
    """Trả về puzzle dạng: {fen, solution, type}."""

    while True:
        board = random_position(random.randint(8, 24))
        fen = board.fen()

        info = get_engine_eval(fen, depth=depth)
        if info is None or "pvs" not in info:
            continue

        pvs = info["pvs"]
        if len(pvs) < 1:
            continue

        best = pvs[0]
        best_move = best["moves"].split()[0]

        # Nếu có mate → Mate puzzle
        if "mate" in best:
            return {
                "fen": fen,
                "solution": best_move,
                "type": f"Mate in {best['mate'] if best['mate']>0 else -best['mate']}"
            }

        # Nếu không mate → tactic
        if len(pvs) >= 2:
            second = pvs[1]
            best_score = best.get("cp", 0)
            second_score = second.get("cp", 0)

            if (best_score - second_score) >= min_gap:
                return {
                    "fen": fen,
                    "solution": best_move,
                    "type": "Tactic (winning move)"
                }


# ======================
# HIỂN THỊ BÀN CỜ SVG
# ======================

def render_board(fen):
    board = chess.Board(fen)
    svg = chess.svg.board(board=board, size=480)
    b64 = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'


# ======================
# STREAMLIT UI
# ======================

st.set_page_config(page_title="Chess Trainer", page_icon="♟")
st.title("♟ Trình tạo bài tập cờ vua – TỰ ĐỘNG & KHÔNG GIỚI HẠN")

difficulty = st.select_slider("Độ khó", ["Dễ", "Vừa", "Khó"])
depth_map = {"Dễ": 12, "Vừa": 14, "Khó": 18}
gap_map = {"Dễ": 120, "Vừa": 150, "Khó": 200}

if st.button("🎲 Tạo bài mới"):
    st.session_state["puzzle"] = generate_puzzle(
        depth=depth_map[difficulty],
        min_gap=gap_map[difficulty],
    )

if "puzzle" in st.session_state:

    p = st.session_state["puzzle"]

    st.subheader(f"Loại bài: **{p['type']}**")
    st.write(f"FEN: `{p['fen']}`")

    st.markdown(render_board(p["fen"]), unsafe_allow_html=True)

    move = st.text_input("Nhập nước đi theo UCI (vd: e2e4):")

    if st.button("Kiểm tra"):
        if move == p["solution"]:
            st.success("✔ Chính xác!")
        else:
            st.error("❌ Sai rồi, thử lại nhé.")

    if st.button("Xem đáp án"):
        st.info(f"Đáp án đúng: **{p['solution']}**")

