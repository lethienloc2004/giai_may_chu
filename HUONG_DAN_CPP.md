# Bộ giải C++ (ít RAM)

Cùng luật với `giai_dung.py` nhưng mỗi trạng thái chỉ 32 byte (Python tốn ~900 byte nên dễ hết RAM).

```
g++ -O2 -o giai_cpp giai_cpp.cpp
python3 chuanbi_cpp.py ai15_lan8.json ten_mau.txt > vao.txt
./giai_cpp vao.txt 150000000
```

Kết quả: `WIN_CERTAIN`, `PROB` (xác suất thắng tối đa), `PATH` (các nước tới lần lộ ô kế tiếp, lọ đánh số từ 1).
Ghi chú: chưa đối chiếu chéo với bản Python trên ván nhỏ.
