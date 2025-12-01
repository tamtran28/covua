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
    url = "https://lichess.org/api/cloud-eval"
    r = requests.get(url, params={"fen": fen, "depth": depth})
    if r.status_code != 200:
        return None
    return r.json()


# ======================
# RANDOM POSITION
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
# AUTO PUZZLE GENERATOR
# ======================

def generate_puzzle(depth=14, min_gap=150):
    while True:
        board = random_position(random.randint(6, 24))
        fen = board.fen()

        info = get_engine_eval(fen, depth=depth)
        if info is None or "pvs" not in info:
            continue

        pvs = info["pvs"]
        if len(pvs) < 1:
            continue

        best = pvs[0]
        best_move = best["moves"].split()[0]

        # Mate
        if "mate" in best:
            return {
                "fen": fen,
                "solution": best_move,
                "type": f"Mate in {abs(best['mate'])}"
            }

        # Tactic
        if len(pvs) >= 2:
            best_cp = best.get("cp", 0)
            second_cp = pvs[1].get("cp", 0)
            if (best_cp - second_cp) >= min_gap:
                return {
                    "fen": fen,
                    "solution": best_move,
                    "type": "Tactic"
                }


# ======================
# RENDER BOARD
# ======================

def render_board(fen):
    board = chess.Board(fen)
    svg = chess.svg.board(board=board, size=480)
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}"/>'


# ======================
# BUILD BOARD FROM SQUARE LIST
# ======================

def build_board_from_squares(text):
    """
    Nhập dạng: Ke1, Qd4, pa2, pb2, pg7
    - Viết hoa = quân trắng
    - Viết thường = quân đen
    """
    board = chess.Board(None)
    items = text.split(",")

    piece_map = {
        "K": chess.KING,
        "Q": chess.QUEEN,
        "R": chess.ROOK,
        "B": chess.BISHOP,
        "N": chess.KNIGHT,
        "P": chess.PAWN
    }

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


# ======================
# ALGEBRAIC NOTATION PARSER
# ======================

def algebraic_to_uci(board, move_str):
    """
    Chuyển nước từ SAN/Algebraic (Như Nf3, Qh5, Bxe6+)
    thành UCI để so sánh với lời giải.
    """
    move_str = move_str.strip()

    # rocastle
    if move_str in ["O-O", "0-0", "o-o"]:
        move_str = "O-O"
    if move_str in ["O-O-O", "0-0-0", "o-o-o"]:
        move_str = "O-O-O"

    try:
        move = board.parse_san(move_str)
        return move.uci()
    except:
        return None


# ======================
# STREAMLIT UI
# ======================

st.set_page_config(page_title="Chess Trainer Plus", page_icon="♟")
st.title("♟ Trình tạo bài tập cờ vua – bản hoàn chỉnh")

tab1, tab2, tab3 = st.tabs([
    "🎲 Tạo bài tự động",
    "📥 Nhập FEN",
    "⌨ Tạo bàn từ ký hiệu ô"
])


# ======================
# TAB 1 – AUTO PUZZLE
# ======================

with tab1:
    difficulty = st.select_slider("Độ khó", ["Dễ", "Vừa", "Khó"])
    depth_map = {"Dễ": 12, "Vừa": 14, "Khó": 18}
    gap_map = {"Dễ": 120, "Vừa": 150, "Khó": 200}

    if st.button("🎲 Tạo bài mới"):
        st.session_state["puzzle"] = generate_puzzle(
            depth=depth_map[difficulty],
            min_gap=gap_map[difficulty]
        )

    if "puzzle" in st.session_state:
        p = st.session_state["puzzle"]

        st.subheader(f"Loại bài: **{p['type']}**")
        st.write(f"FEN: `{p['fen']}`")

        st.markdown(render_board(p["fen"]), unsafe_allow_html=True)

        # --- UCI input ---
        st.write("### 📝 Nhập nước đi dạng UCI (e2e4)")
        uci_move = st.text_input("Nước đi UCI:", key="uci1")

        if st.button("Kiểm tra UCI"):
            if uci_move == p["solution"]:
                st.success("✔ Chính xác!")
            else:
                st.error("❌ Sai rồi!")

        # --- Algebraic input ---
        st.write("### 💬 Nhập nước đi dạng Algebraic (Nf3, Qh5, Bxe6+)")
        algebraic_move = st.text_input("Nước đi SAN/AN:", key="alg1")

        if st.button("Kiểm tra Algebraic"):
            board = chess.Board(p["fen"])
            uci = algebraic_to_uci(board, algebraic_move)

            if uci is None:
                st.error("⚠ Không hiểu nước AN bạn nhập.")
            elif uci == p["solution"]:
                st.success("🎉 Chính xác (AN → UCI)!")
            else:
                st.error(f"❌ Sai rồi. Nước bạn nhập là: **{uci}**")

        if st.button("Xem lời giải"):
            st.info(f"Đáp án đúng: **{p['solution']}**")


# ======================
# TAB 2 – FEN INPUT
# ======================

with tab2:
    st.subheader("✔ Nhập FEN để hiển thị bàn cờ")
    fen_input = st.text_input("Nhập mã FEN:", key="feninput")

    if st.button("Vẽ FEN"):
        try:
            st.markdown(render_board(fen_input), unsafe_allow_html=True)
        except:
            st.error("❌ FEN không hợp lệ.")


# ======================
# TAB 3 – SQUARE INPUT
# ======================

with tab3:
    st.subheader("✔ Tạo bàn cờ từ ký hiệu ô")

    st.write("""
    Ví dụ nhập:

    **Ke1, Qh5, pa7, pb7, ph7, ra8**
    
    - Viết hoa = quân trắng  
    - Viết thường = quân đen  
    - Ký hiệu ô theo chuẩn (a1 đến h8)
    """)

    sq_input = st.text_area("Danh sách quân:")
    if st.button("Tạo bàn từ ký hiệu"):
        try:
            board = build_board_from_squares(sq_input)
            st.markdown(render_board(board.fen()), unsafe_allow_html=True)
        except:
            st.error("❌ Lỗi khi dựng bàn. Hãy kiểm tra ký hiệu.")
