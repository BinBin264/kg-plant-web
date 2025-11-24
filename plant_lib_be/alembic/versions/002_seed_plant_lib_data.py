# versions/002_seed_plant_lib_data.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import unicodedata
import re

# ---- Alembic identifiers ----
revision = "002_seed_plant_lib_data"
down_revision = "001_init_plant_lib_lite"
branch_labels = None
depends_on = None


# --------- Helpers ----------
def _slugify(s: str) -> str:
    """Bỏ dấu tiếng Việt, chuyển thường, thay non a-z0-9 thành '-', trim '-'."""
    if s is None:
        return ""
    s = s.replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _get_or_create_crop(conn, name: str):
    row = conn.execute(sa.text("SELECT id FROM kb.crops WHERE name = :name"), {"name": name}).fetchone()
    if row:
        return row[0]
    res = conn.execute(
        sa.text("INSERT INTO kb.crops (name) VALUES (:name) RETURNING id"),
        {"name": name},
    )
    return res.scalar()


def _insert_disease(conn, name, pathogen_type, symptoms, prevention_steps):
    image_url = f"/assets/images/diseases/{_slugify(name)}.jpg"
    stmt = (
        sa.text(
            """
            INSERT INTO kb.diseases (name, pathogen_type, symptoms, prevention_steps, image_url)
            VALUES (:name, :ptype, :symptoms, :steps, :image_url)
            RETURNING id
            """
        ).bindparams(
            sa.bindparam("steps", value=prevention_steps, type_=pg.ARRAY(sa.Text()))
        )
    )
    return conn.execute(
        stmt,
        {"name": name, "ptype": pathogen_type, "symptoms": symptoms, "image_url": image_url},
    ).scalar()


def upgrade():
    conn = op.get_bind()

    # ===================== Disease 100001 =====================
    d1_name = "Bệnh thối rễ và cổ rễ ở Táo"
    d1_pathogen = "nam"  # fungi
    d1_symptoms = (
        "Những triệu chứng đầu tiên trên táo và lê xuất hiện trên vòm lá với dấu hiệu điển hình là "
        "ngọn phát triển kém, lá nhỏ, úa vàng và héo rũ. Cây cũng có vẻ còi cọc. Vào thời điểm ấy, "
        "quá trình hư thối tại rễ và ngọn cây đã bước vào giai đoạn phát triển mạnh mẽ. Khi lột đi vỏ cây, "
        "những phần mô bên trong lộ ra các vùng nhuốm màu cam chuyển sang màu đỏ nâu rất dễ nhận thấy. "
        "Khi bệnh tiến triển, các vùng này to dần và chuyển sang màu nâu. Sự thối rữa hay hoại tử của các mô mạch "
        "làm hạn chế quá trình cung cấp các chất dinh dưỡng cho toàn bộ cây trồng. Các triệu chứng cho thấy cây "
        "đang chịu áp lực tổng thể, chẳng hạn như lá nhợt nhạt, héo rũ và rụng lá khiến cây phát triển còi cọc. "
        "Cây yếu dần suốt nhiều mùa rồi cuối cùng chết đi. Hiện tượng thối quả có thể diễn ra với biểu hiện là "
        "các vết tổn thương màu nâu sẫm có khả năng ảnh hưởng đến toàn bộ quả. Cây ăn quả thường mẫn cảm với "
        "tình trạng thối rữa ở các giai đoạn trưởng thành khác nhau."
    )
    d1_prevent = [
        "Chọn trồng các giống táo có sức chống chịu bệnh.",
        "Thoát nước tốt cho vườn táo.",
        "Cắt bỏ các cành nhánh đã nhiễm bệnh.",
        "Quả nhiễm bệnh cũng cần được thu gom lại và để dầm mềm đi dọc lối đi.",
        "Tránh để cỏ dại mọc quá nhiều cạnh thân cây.",
        "Bổ sung lớp phủ hữu cơ quanh thân cây để tránh tình trạng bị bắn bùn đất.",
        "Loại bỏ đất ở gốc cây để phơi sáng phần thân bị nhiễm bệnh và giữ cho khu vực nhiễm bệnh khô ráo, bồi đất mới vào mùa thu.",
        "Chỉ hái quả bên trên một độ cao nhất định để lưu kho.",
        "Phun dung dịch u-rê 5% để tăng tốc quá trình ngâm mềm lá trong vườn.",
        "Tránh để quả bị nhiễm bùn đất bắn từ xe kéo.",
    ]
    d1_id = _insert_disease(conn, d1_name, d1_pathogen, d1_symptoms, d1_prevent)
    for cname in ["Táo"]:
        cid = _get_or_create_crop(conn, cname)
        conn.execute(sa.text("INSERT INTO kb.disease_crops (disease_id, crop_id) VALUES (:did, :cid)"),
                     {"did": d1_id, "cid": cid})

    # ===================== Disease 100002 =====================
    d2_name = "Bệnh phấn trắng"
    d2_pathogen = "nam"  # fungi
    d2_symptoms = (
        "Ban đầu, những đốm vàng xuất hiện ở mặt trên của lá. Ở giai đoạn sau của bệnh, lớp phấn màu trắng, "
        "sau ngả xám lan rộng phủ lên lá, thân và quả. Nấm hút chất dinh dưỡng từ cây, để lại lớp phủ giống như tro "
        "trên lá cản trở quá trình quang hợp làm cây phát triển còi cọc. Khi bệnh tiến triển, các bộ phận bị nhiễm "
        "bệnh quăn lại, lá rụng và cây có thể chết. Trái ngược với bệnh sương mai, bệnh phấn trắng có thể được kiểm "
        "soát ở một mức độ nào đó."
    )
    d2_prevent = [
        "Sử dụng các giống kháng bệnh hoặc chịu bệnh.",
        "Trồng cây với khoảng cách vừa đủ cho phép thông gió tốt.",
        "Theo dõi vườn cây thường xuyên để đánh giá tình hình bệnh hoặc sâu bệnh.",
        "Loại bỏ lá bị nhiễm bệnh khi những đốm đầu tiên xuất hiện.",
        "Không chạm vào cây khỏe mạnh sau khi chạm vào cây bị nhiễm bệnh.",
        "Lớp phủ (bổi) dày có thể ngăn chặn sự phát tán của bào tử từ đất lên lá.",
        "Trong một số trường hợp, luân canh với cây trồng không dễ bị mắc bệnh.",
        "Bón phân cân đối.",
        "Tránh thay đổi nhiệt đột ngột.",
        "Cày xới đất kỹ sau khi thu hoạch để vùi phần còn lại của cây sâu vào đất.",
        "Loại bỏ tàn dư cây cối sau khi thu hoạch.",
    ]
    d2_id = _insert_disease(conn, d2_name, d2_pathogen, d2_symptoms, d2_prevent)
    d2_crops = [
        "Táo", "Mơ", "Đậu", "Mướp đắng", "Cải bắp", "Cải dầu", "Cà rốt", "Anh đào",
        "Đậu gà & Đậu xanh", "Chi cam chanh", "Cà phê", "Bông vải", "Dưa chuột", "Cà tím",
        "Đậu đen & xanh", "Đậu lăng", "Rau diếp", "Ngô/Bắp", "Sắn/Khoai mì", "Dưa",
        "Đậu bắp", "Hành", "Cây cảnh", "Đậu Hà Lan", "Đào", "Lạc/Đậu phộng", "Lê",
        "Đậu triều & Đậu đỏ", "Khoai tây", "Bí ngô", "Lúa miến", "Củ cải đường", "Mía",
        "Thuốc lá", "Cà chua", "Bí ngòi",
    ]
    for cname in d2_crops:
        cid = _get_or_create_crop(conn, cname)
        conn.execute(sa.text("INSERT INTO kb.disease_crops (disease_id, crop_id) VALUES (:did, :cid)"),
                     {"did": d2_id, "cid": cid})

    # ===================== Disease 100003 =====================
    d3_name = "Bệnh sương mai (mốc sương)"
    d3_pathogen = "nam"  # fungi
    d3_symptoms = (
        "Các đốm màu vàng loang lổ với kích thước khác nhau xuất hiện ở mặt trên của lá non đang phát triển. "
        "Khi bệnh tiến triển, những đốm này lan rộng ở các góc và được phân tách bởi các gân lá. Phần trung tâm bị "
        "hoại tử, với các sắc thái nâu khác nhau và có thể được bao quanh bởi một quầng sáng màu vàng. Thông thường "
        "sau nhiều đêm nồm ấm, một lớp bông dày, trắng ngả xám phát triển bên dưới những đốm này. Nấm hút chất dinh "
        "dưỡng từ cây làm cây phát triển chậm; quả và các bộ phận khác của cây cũng có thể bị ảnh hưởng. Rụng lá, thấp "
        "lùn hoặc chết chồi non/hoa/quả dẫn đến năng suất kém. Trái ngược với bệnh phấn trắng, lớp phủ này chỉ xuất "
        "hiện ở mặt dưới của lá, bị giới hạn bởi các gân chính và không dễ lau bỏ."
    )
    d3_prevent = [
        "Chọn giống kháng bệnh, nếu có.",
        "Giữ cho cây trồng khô ráo, ví dụ bằng phương pháp thông gió thích hợp.",
        "Đảm bảo đất được thoát nước tốt.",
        "Bón phân cân đối dinh dưỡng để đảm bảo sức sống cho cây.",
        "Tạo khoảng cách rộng rãi giữa các cây.",
        "Trồng ở những nơi tiếp xúc tốt với ánh nắng mặt trời và chọn đúng hướng.",
        "Kiểm soát cỏ dại trong và xung quanh ruộng vườn.",
        "Loại bỏ tàn dư cây lá có trên cánh đồng.",
        "Giữ dụng cụ và thiết bị sạch sẽ.",
        "Tránh phân tán đất và cành lá bị nhiễm bệnh.",
        "Có thể dùng thuốc trợ lực để tăng cường sức khỏe cho cây.",
    ]
    d3_id = _insert_disease(conn, d3_name, d3_pathogen, d3_symptoms, d3_prevent)
    d3_crops = [
        "Đậu", "Cải bắp", "Bông cải trắng", "Đậu gà & Đậu xanh", "Tỏi", "Rau diếp",
        "Hành", "Cây cảnh", "Đậu Hà Lan", "Đậu triều & Đậu đỏ", "Lúa miến",
    ]
    for cname in d3_crops:
        cid = _get_or_create_crop(conn, cname)
        conn.execute(sa.text("INSERT INTO kb.disease_crops (disease_id, crop_id) VALUES (:did, :cid)"),
                     {"did": d3_id, "cid": cid})

    # ===================== Disease 100004 =====================
    d4_name = "Bệnh sương mai trên kê"
    d4_pathogen = "nam"  # fungi
    d4_symptoms = (
        "Các triệu chứng của bệnh sương mai có thể rất khác nhau. Bệnh này còn được gọi là bệnh tai xanh, "
        "vì các phần hoa của cây bị chuyển thành các cấu trúc giống như lá."
    )
    d4_prevent = [
        "Loại bỏ cây bị nhiễm bệnh ngay lập tức.",
        "Xử lý hạt giống thường xuyên bằng thuốc diệt nấm.",
        "Trồng giống kháng bệnh."
    ]
    d4_id = _insert_disease(conn, d4_name, d4_pathogen, d4_symptoms, d4_prevent)
    for cname in ["Kê"]:
        cid = _get_or_create_crop(conn, cname)
        conn.execute(sa.text("INSERT INTO kb.disease_crops (disease_id, crop_id) VALUES (:did, :cid)"),
                     {"did": d4_id, "cid": cid})

    # ===================== Disease 100005 =====================
    d5_name = "Bệnh thối đen cây ăn quả"
    d5_pathogen = "nam"  # fungi
    d5_symptoms = (
        "Có thể quan sát thấy các mảng vỏ chết (thối mục) dạng lõm tròn hay bầu dục trên thân cây và các cành nhánh. "
        "Các trường hợp nhiễm bệnh này thường bắt đầu tại khu vực quanh những vết thương, các chồi búp trên cành hay "
        "nhánh non dưới dạng các vết thương tổn lõm hoe đỏ. Về sau, các thương tổn này phát triển thành khu vực thối "
        "mục, khiến cành nhánh bị tróc vỏ rồi chết đi chỉ trong một mùa vụ. Ở các cành to, các vết thương tổn xuất hiện "
        "dưới dạng các đốm lõm màu nâu đỏ, về sau vỡ ra và để lộ phần gỗ chết ở giữa. Vỏ cây chết đi vẫn lưu lại những "
        "vòng đồng tâm tích tụ nhiều năm và các mép nổi gờ điển hình. Các cành nhánh bên trên khu vực thối mục phát triển "
        "yếu ớt và chết dần đi. Đôi khi, các quả đang phát triển cũng bị tấn công và xuất hiện vết \"mắt thối loét khô\" "
        "(thối đuôi quả) quanh đài hoa."
    )
    d5_prevent = [
        "Đảm bảo chọn trồng giống kháng bệnh, nếu có.",
        "Tránh gây tổn thương cho cây khi làm việc vườn hay khi thu hoạch.",
        "Đảm bảo chế độ bón phân cân bằng và xén tỉa hợp lý.",
        "Chỉ xén tỉa cây trong thời tiết khô ráo và luôn vệ sinh sạch sẽ công cụ xén tỉa.",
        "Giám sát vườn thường xuyên và loại bỏ mọi cành nhánh đã nhiễm bệnh.",
        "Sơn các vết thương bằng một loại sơn bít có tính bảo vệ.",
        "Đảm bảo thoát nước tốt cho đất vườn.",
        "Nâng độ pH của đất vườn bằng cách bón vôi nếu cần.",
    ]
    d5_id = _insert_disease(conn, d5_name, d5_pathogen, d5_symptoms, d5_prevent)
    for cname in ["Táo", "Lê"]:
        cid = _get_or_create_crop(conn, cname)
        conn.execute(sa.text("INSERT INTO kb.disease_crops (disease_id, crop_id) VALUES (:did, :cid)"),
                     {"did": d5_id, "cid": cid})


def downgrade():
    conn = op.get_bind()

    disease_names = [
        "Bệnh thối rễ và cổ rễ ở Táo",
        "Bệnh phấn trắng",
        "Bệnh sương mai (mốc sương)",
        "Bệnh sương mai trên kê",
        "Bệnh thối đen cây ăn quả",
    ]

    # Tập crops đã tạo/đụng tới trong upgrade
    crop_names = set(
        ["Táo"] +
        [
            "Táo", "Mơ", "Đậu", "Mướp đắng", "Cải bắp", "Cải dầu", "Cà rốt", "Anh đào",
            "Đậu gà & Đậu xanh", "Chi cam chanh", "Cà phê", "Bông vải", "Dưa chuột", "Cà tím",
            "Đậu đen & xanh", "Đậu lăng", "Rau diếp", "Ngô/Bắp", "Sắn/Khoai mì", "Dưa",
            "Đậu bắp", "Hành", "Cây cảnh", "Đậu Hà Lan", "Đào", "Lạc/Đậu phộng", "Lê",
            "Đậu triều & Đậu đỏ", "Khoai tây", "Bí ngô", "Lúa miến", "Củ cải đường", "Mía",
            "Thuốc lá", "Cà chua", "Bí ngòi",
        ] +
        [
            "Đậu", "Cải bắp", "Bông cải trắng", "Đậu gà & Đậu xanh", "Tỏi", "Rau diếp",
            "Hành", "Cây cảnh", "Đậu Hà Lan", "Đậu triều & Đậu đỏ", "Lúa miến",
        ] +
        ["Kê", "Lê"]
    )

    # Xoá liên kết và bệnh
    for dname in disease_names:
        row = conn.execute(sa.text("SELECT id FROM kb.diseases WHERE name = :n"), {"n": dname}).fetchone()
        if row:
            did = row[0]
            conn.execute(sa.text("DELETE FROM kb.disease_crops WHERE disease_id = :did"), {"did": did})
            conn.execute(sa.text("DELETE FROM kb.diseases WHERE id = :did"), {"did": did})

    # Thử xoá crops nếu không còn được tham chiếu
    for cname in crop_names:
        conn.execute(
            sa.text(
                """
                DELETE FROM kb.crops c
                WHERE c.name = :name
                  AND NOT EXISTS (
                      SELECT 1 FROM kb.disease_crops dc
                      WHERE dc.crop_id = c.id
                  )
                """
            ),
            {"name": cname},
        )
