"""Portable CSV, JSON, SVG and offline HTML output (Python standard library)."""
import csv
import html
import json
from pathlib import Path
from .model import DAYS


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames=None):
    rows = list(rows)
    with Path(path).open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def schedule_rows(instance, schedule):
    rows = []
    for day, events in enumerate(schedule):
        for sid, slot, room in events:
            sec = instance.sections[sid - 1]
            rows.append({"day": day + 1, "day_name": DAYS[day], "timeslot": slot,
                         "period": "AM" if slot <= 3 else "PM", "room": room,
                         "room_size": instance.room_sizes[room - 1], "course": sec.course,
                         "section": sid, "section_in_course": (sid - 1) % 8 + 1,
                         "section_size": sec.size, "professor": sec.professor})
    return sorted(rows, key=lambda row: (row["day"], row["timeslot"], row["room"]))


def plot_svg(path, history, rooms):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="710" viewBox="0 0 1120 710">',
             '<rect width="1120" height="710" fill="#f4f7fb"/>',
             '<g font-family="Arial,sans-serif" fill="#152b45">',
             f'<text x="70" y="42" font-size="24" font-weight="bold">HW3 | {rooms} rooms | Genetic algorithm</text>',
             '<text x="70" y="66" font-size="14">Actual recorded generations, including the initial population (generation 0)</text>']
    for y0, keys, title in ((100, ("best_soft_cost", "mean_soft_cost"), "Soft cost (lower is better)"),
                            (395, ("best_fitness",), "Hard-aware fitness = 1 / (1 + 100000 * (missing sessions + conflicts) + soft cost)")):
        x0, width, height = 130, 920, 210
        values = [row[key] for row in history for key in keys]
        low, high = min(values), max(values)
        pad = (high - low) * 0.08 or max(abs(high) * 0.05, 0.000001)
        low, high = low - pad, high + pad
        parts.append(f'<text x="70" y="{y0}" font-size="17" font-weight="bold">{title}</text>')
        top = y0 + 22
        for i in range(5):
            y = top + height * i / 4
            value = high - (high - low) * i / 4
            label = (f"{value:.0f}" if keys[0] == "best_soft_cost" else
                     f"{value:.8e}" if rooms == 20 else f"{value:.6f}")
            parts.append(f'<path d="M {x0} {y} H {x0 + width}" stroke="#dce4ed"/>')
            parts.append(f'<text x="{x0 - 12}" y="{y + 4}" font-size="12" text-anchor="end">{label}</text>')
        last = max(1, history[-1]["generation"])
        for i in range(6):
            x = x0 + width * i / 5
            parts.append(f'<text x="{x}" y="{top + height + 20}" font-size="12" text-anchor="middle">{round(last * i / 5)}</text>')
        parts.append(f'<text x="{x0 + width / 2}" y="{top + height + 42}" font-size="13" text-anchor="middle">Generation</text>')
        for key, color in zip(keys, ("#087f8c", "#e18b35")):
            points = " ".join(f'{x0 + width * row["generation"] / last:.2f},{top + height * (high - row[key]) / (high - low):.2f}' for row in history)
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        if len(keys) == 2:
            parts.append(f'<text x="790" y="{y0}" fill="#087f8c" font-size="13">Best</text>')
            parts.append(f'<text x="870" y="{y0}" fill="#e18b35" font-size="13">Population mean</text>')
    parts.append('<text x="70" y="688" font-size="12">Missing sessions are hard violations. Fitness axis is zoomed; compare coverage before comparing soft costs.</text>')
    parts.append('</g></svg>')
    Path(path).write_text("\n".join(parts), encoding="utf-8")


def export_html(path, instance, rows, validation):
    payload = json.dumps(rows, ensure_ascii=True)
    status = ("Đủ 480 lớp / 960 buổi; không vi phạm ràng buộc cứng." if validation["fully_feasible"]
              else "Lịch một phần: 300 lớp / 600 buổi; còn 180 lớp / 360 buổi chưa xếp do thiếu sức chứa.")
    document = '''<!doctype html><html lang="vi"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HW3 - Thời khóa biểu</title><style>
body{font:15px system-ui,sans-serif;background:#f3f6fa;color:#17314c;margin:0;padding:28px}
main{max-width:1400px;margin:auto}h1{margin-bottom:8px}.status{padding:16px;background:#e4eff6;border-left:5px solid #087f8c}
.controls{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}select{padding:8px;font:inherit;border:1px solid #aabccc;border-radius:5px}
table{border-collapse:collapse;width:100%;background:white;table-layout:fixed}th,td{border:1px solid #d3deea;padding:10px;vertical-align:top}
th{background:#17314c;color:white}.event{background:#edf6f7;border-left:3px solid #087f8c;padding:8px;margin:3px 0;border-radius:3px}
.muted{color:#526a80;font-size:13px}.wrap{overflow:auto}table{min-width:780px}th:first-child{width:65px}
img{max-width:100%;margin-top:24px}a{color:#087f8c}button{padding:9px;cursor:pointer}
@media print{body{padding:0}.controls,button{display:none}.event{break-inside:avoid}}
</style><main><h1>HW3 · Thời khóa biểu __ROOMS__ phòng</h1>
<p class="status">__STATUS__</p>
<p>Tiết 1–3: sáng; tiết 4–6: chiều. Mã lớp L001–L480 là mã duy nhất; mỗi môn có 8 lớp.</p>
<div class="controls"><label>Xem theo <select id="kind"><option value="room">Phòng</option><option value="professor">Giảng viên</option><option value="course">Môn học</option></select></label>
<label>Mã số <select id="id"></select></label><button onclick="window.print()">In lịch đang xem</button></div>
<p id="count"></p><div class="wrap"><table><thead><tr><th>Tiết</th><th>Thứ Hai</th><th>Thứ Ba</th><th>Thứ Tư</th><th>Thứ Năm</th><th>Thứ Sáu</th></tr></thead><tbody id="grid"></tbody></table></div>
<p><a href="schedule.csv">Toàn bộ lịch CSV</a> · <a href="unscheduled.csv">Các lớp chưa xếp</a> · <a href="summary.json">Kết quả kiểm tra</a></p>
<img src="fitness.svg" alt="Đồ thị chi phí mềm và fitness qua các thế hệ">
<p class="muted">Lịch 20 phòng đạt giới hạn sức chứa, không phải lời giải đầy đủ. GA tối ưu ràng buộc mềm trong miền ngày học và phân công giảng viên đã cố định.</p>
</main><script>
const data=__DATA__, roomCount=__ROOMS__;
const kind=document.getElementById('kind'), selector=document.getElementById('id');
function render(){const rows=data.filter(r=>r[kind.value]===Number(selector.value));
document.getElementById('count').textContent=rows.length+' buổi trong lịch đang xem.';
document.getElementById('grid').innerHTML=Array.from({length:6},(_,t)=>'<tr><th>'+(t+1)+'<br><small>'+(t<3?'Sáng':'Chiều')+'</small></th>'+Array.from({length:5},(_,d)=>'<td>'+rows.filter(r=>r.day===d+1&&r.timeslot===t+1).map(r=>'<div class="event"><b>M'+r.course+' · L'+String(r.section).padStart(3,'0')+'</b><br>GV '+r.professor+' · Phòng '+r.room+'<br><span class="muted">Cỡ lớp '+r.section_size+' / phòng '+r.room_size+'</span></div>').join('')+'</td>').join('')+'</tr>').join('');}
function populate(){const n=kind.value==='room'?roomCount:60;selector.innerHTML=Array.from({length:n},(_,i)=>'<option>'+(i+1)+'</option>').join('');render();}
kind.onchange=populate;selector.onchange=render;populate();
</script></html>'''
    document = document.replace("__ROOMS__", str(len(instance.room_sizes)))
    document = document.replace("__STATUS__", html.escape(status)).replace("__DATA__", payload)
    Path(path).write_text(document, encoding="utf-8")


def export_run(folder, instance, best, initial, history, summary):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / "instance.json", instance.to_dict())
    write_json(folder / "schedule.json", {"days": best})
    write_json(folder / "summary.json", summary)
    rows = schedule_rows(instance, best)
    write_csv(folder / "schedule.csv", rows)
    write_csv(folder / "initial_schedule.csv", schedule_rows(instance, initial))
    write_csv(folder / "fitness.csv", history)
    selected = {r["section"] for r in rows}
    unscheduled = [{"section": s.id, "course": s.course, "professor": s.professor,
                    "section_size": s.size, "missing_sessions": 2,
                    "reason": "Insufficient room-timeslot capacity"}
                   for s in instance.sections if s.id not in selected]
    write_csv(folder / "unscheduled.csv", unscheduled,
              ["section", "course", "professor", "section_size", "missing_sessions", "reason"])
    plot_svg(folder / "fitness.svg", history, len(instance.room_sizes))
    export_html(folder / "schedule.html", instance, rows, summary["validation"])
