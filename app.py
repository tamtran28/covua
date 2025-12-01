import streamlit as st
import chess
import chess.svg
import random
import requests
import base64


# ============================================
#  LICHESS CLOUD ENGINE FIX (CHẠY ĐƯỢC TRÊN STREAMLIT CLOUD)
# ============================================

def get_engine_eval(fen, depth=14):
    url = "https://lichess.org/api/cloud-eval"
    headers = {
        "User-Agent": "ChessTrainerStreamlit/1.0 (contact: your-email@example.com)"
    }
    try:
        r = requests.get(
            url,
            params={"fen": fen, "depth": depth},
            headers=headers,
            timeout=10
        )
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


# ============================================
#  RANDOM POSITION
# ============================================

def random_position(plies=12):
    board = chess.Board()
    for _ in range(plies):
        if board.is_game_over():
            break
        move = random.choice(list(board.legal_moves))
        board.push(move)
    return board


# ============================================
#  TẠO BÀI TẬP (MATE + TACTIC)
# ============================================

def generate_puzzle(depth=14, min_gap=150):
    for _ in range(50):  # thử tối đa 50 lần
        board = random_position(random.randint(6, 24))
        fen = board.fen()

        info = get_engine_eval(fen, depth)
        if info is None or "pvs" not in info:
            continue

        pvs = info["pvs"]
        if len(pvs) == 0:
            continue

        best = pvs[0]
        best_move = best["moves"].split()[0]

        # Nếu có Mate → bài chiếu bí
        if "mate" in best:
            return {
                "fen": fen,
                "solution": best_move,
                "type": f"Mate in {abs(best['mate'])}"
            }

        # Nếu có tactic (best hơn second nhiều)
        if len(pvs) >= 2:
            best_cp = best.get("cp", 0)
            second_cp = pvs[1].get("cp", 0)

            if (best_cp - second_cp) >= min_gap:
                return {
                    "fen": fen,
                    "solution": best_move,
                    "type": "Tactic"
                }

    return None  # không tìm được bài


# ============================================
#  VẼ BÀN CỜ SVG
# ============================================

def render_board(fen):
    board = chess.Board(fen)
    svg = chess.svg.board(board=board, size=480)
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'


# ============================================
#  BUILD BOARD FROM SQUARE LIST
# ============================================

def build_board_from_squares(text):
    board = chess.Board(None)
    items = text.split(",")

    piece_map = {"K": chess.KING, "Q": chess.QUEEN, "R": chess.ROOK,
                 "B": chess.BISHOP, "N": chess.KNIGHT, "P": chess.PAWN}

    for item in items:
        item = item.strip()
        if len(item) < 3:
            continue

        piece_symbol = item[0]
        square_symbol = item[1:]

        if square_symbol not in chess.SQUARE_NAMES:
            continue

        square = chess.parse_square(square_symbol)
        color = piece_symbol.isupper()
        ptype = piece_map[piece_symbol.upper()]

        board.set_piece_at(square, chess.Piece(ptype, color))

    return board


# ============================================
#  CHUYỂN SAN → UCI
# ============================================

def algebraic_to_uci(board, move_str):
    move_str = move_str.strip()

    if move_str in ["O-O", "0-0", "o-o"]:
        move_str = "O-O"
    if move_str in ["O-O-O", "0-0-0", "o-o-o"]:
        move_str = "O-O-O"

    try:
        move = board.parse_san(move_str)
        return move.uci()
    except:
        return None


# ============================================
#  STREAMLIT UI
# ============================================

st.set_page_config(page_title="Chess Trainer Plus", page_icon="♟")
st.title("♟ Trình tạo bài tập cờ vua – FULL VERSION")


tab1, tab2, tab3 = st.tabs([
    "🎲 Tạo bài tự động",
    "📥 Nhập nhiều FEN",
    "⌨ Nhập nhiều ký hiệu quân"
])


# ============================================
#  TAB 1 – AUTO PUZZLE
# ============================================

with tab1:
    st.subheader("🎲 Tự sinh bài tập từ engine")

    difficulty = st.select_slider("Độ khó", ["Dễ", "Vừa", "Khó"])
    depth_map = {"Dễ": 12, "Vừa": 14, "Khó": 18}
    gap_map = {"Dễ": 120, "Vừa": 150, "Khó": 200}

    if st.button("Tạo bài mới 🎯"):
        puzzle = generate_puzzle(
            depth=depth_map[difficulty],
            min_gap=gap_map[difficulty]
        )
        st.session_state["puzzle"] = puzzle

    if "puzzle" in st.session_state and st.session_state["puzzle"]:
        p = st.session_state["puzzle"]

        st.write(f"### Loại bài: **{p['type']}**")
        st.write(f"FEN: `{p['fen']}`")

        st.markdown(render_board(p["fen"]), unsafe_allow_html=True)

        # UCI INPUT
        st.write("#### 📝 Kiểm tra nước UCI")
        uci = st.text_input("Nhập UCI:", key="uci1")
        if st.button("Kiểm tra UCI"):
            st.success("✔ Đúng!") if uci == p["solution"] else st.error("❌ Sai!")

        # SAN INPUT
        st.write("#### 💬 Kiểm tra nước SAN (vd: Nf3, Qh5)")
        san = st.text_input("Nhập SAN:", key="san1")

        if st.button("Kiểm tra SAN"):
            board = chess.Board(p["fen"])
            uci_move = algebraic_to_uci(board, san)

            if uci_move is None:
                st.error("⚠ Không hiểu nước SAN.")
            elif uci_move == p["solution"]:
                st.success("🎉 Chính xác!")
            else:
                st.error(f"❌ Sai rồi. Bạn nhập (UCI): **{uci_move}**")

        if st.button("Xem đáp án"):
            st.info(f"Đáp án: **{p['solution']}**")


# ============================================
#  TAB 2 – MULTI FEN INPUT
# ============================================

with tab2:
    st.subheader("📥 Nhập nhiều FEN (ngăn cách bằng ;)")
    fen_multi = st.text_area("Ví dụ: FEN1 ; FEN2 ; FEN3")

    if st.button("Vẽ tất cả FEN"):
        fen_list = [f.strip() for f in fen_multi.split(";") if f.strip()]

        for i, fen in enumerate(fen_list, 1):
            st.write(f"### ♟ Bàn cờ {i}")
            try:
                st.markdown(render_board(fen), unsafe_allow_html=True)
            except:
                st.error(f"❌ Lỗi FEN: {fen}")


# ============================================
#  TAB 3 – MULTI SQUARE INPUT
# ============================================

with tab3:
    st.subheader("⌨ Nhập nhiều cấu hình quân (ngăn cách bằng ;)")

    st.write("""
    Ví dụ:
    **Ke1,Qh5,pa7 ; Kh8, Qa1, pg7, pf6**
    """)

    sq_multi = st.text_area("Danh sách quân:")

    if st.button("Tạo tất cả bàn cờ"):
        groups = [g.strip() for g in sq_multi.split(";") if g.strip()]

        for i, group in enumerate(groups, 1):
            st.write(f"### ♟ Bàn cờ {i}")
            try:
                board = build_board_from_squares(group)
                st.markdown(render_board(board.fen()), unsafe_allow_html=True)
            except:
                st.error(f"❌ Lỗi nhóm thứ {i}: {group}")
