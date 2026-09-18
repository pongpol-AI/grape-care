# เกาลัดฟาร์ม — Smart Grape Garden

ระบบจัดการสวนองุ่นแบบ FastAPI + SQLite สำหรับบันทึกต้นองุ่น งานดูแล ประวัติ และเตรียมต่อ Sensor/ระบบน้ำในอนาคต

## สถานะ V1

- เพิ่ม/แก้ไข/ลบต้นองุ่นผ่าน API
- เพิ่มงานและกด “ทำแล้ว” เพื่อสร้างประวัติการดูแลอัตโนมัติ
- Dashboard แสดงสถานะสวน งาน และสถานะ Sensor
- Sensor ทุกชนิดเริ่มต้นเป็น `NOT_INSTALLED` และไม่แสดงค่าจำลอง
- ระบบน้ำแสดง `NOT_INSTALLED`; API Sensor ถูกเตรียมไว้แต่ยังไม่รับข้อมูลจนกว่าจะเชื่อม ESP32

## เปิดใช้งานบน Windows

ใช้ Python 3.12 หรือ 3.13 (FastAPI ยังไม่รองรับ Python 3.15 รุ่นทดสอบในบางเครื่อง)

```powershell
cd "D:\HOME Gaolud\Grape"
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

เปิด `http://127.0.0.1:8000` ในเบราว์เซอร์

## GitHub Pages

GitHub Pages ใช้ได้เฉพาะเว็บ static เดิมใน `dist/` แต่ไม่สามารถรัน FastAPI หรือ SQLite ได้ หากต้องการระบบเต็มที่บันทึกข้อมูลจริง ต้องนำ repository นี้ไป deploy บนผู้ให้บริการที่รัน Python ได้ เช่น Render, Railway หรือ VPS.
