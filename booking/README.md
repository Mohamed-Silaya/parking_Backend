
# 🚗 مشروع إدارة حجز الجراجات (Parking Management System)

## ✅ المهمة المنفذة
تم تطوير ميزة حجز مكان في الجراج وربطها بنظام Celery للتحقق من وصول السائق خلال فترة السماح. في حالة عدم وصوله، يتم تنبيهه بأن الحجز سيلغى أو يمكنه دفع تكلفة لتأكيد الحجز.

---

## 🧠 كيف تعمل الميزة؟

1. **عند الحجز**:
   - يتم تحديد الجراج والمكان ووقت الوصول المتوقع.
   - يتم حساب وقت انتهاء صلاحية الحجز (باستخدام فترة السماح).
   - يتم تغيير حالة المكان إلى "محجوز".
   - يتم إنشاء كائن حجز في قاعدة البيانات بحالة "pending".
   - يتم جدولة مهمة باستخدام Celery للتحقق بعد فترة السماح.

2. **مهمة Celery**:
   - عند انتهاء الوقت، يتم التحقق هل السائق وصل أم لا.
   - إذا لم يصل:
     - يتم تحديث حالة الحجز إلى `awaiting_response`.
     - يتم إعادة المكان لحالته الأصلية `available`.
     - يتم طباعة تنبيه على الـ Worker.

---

## 🔧 الإعداد لتشغيل المهمة

### 1. تشغيل Redis (من مجلد Redis):
```bash
.
edis-server.exe
```

### 2. تشغيل Celery:
```bash
celery -A project worker --loglevel=info --pool=solo
```

> **ملاحظة**: استخدم `--pool=solo` في Windows.

### 3. إرسال طلب الحجز من Postman:
```http
POST /api/bookings/initiate/
Headers: Authorization: Bearer <access_token>

{
  "garage_id": 1,
  "parking_spot_id": 2,
  "estimated_arrival_time": "2025-07-04T17:30:00"
}
```

---

## 🔁 مثال حالة ناجحة:
```json
{
  "booking_id": 3,
  "estimated_cost": 20.0,
  "reservation_expiry_time": "2025-07-04T15:27:17.464621+00:00",
  "status": "success"
}
```

## ⏰ بعد انتهاء فترة السماح (من Celery):
```
🚨 التنبيه: لم يصل السائق في الوقت المحدد.
```

---

## 📁 الملفات التي تم تعديلها:

- `booking/views.py` → إضافة الحجز وجدولة المهمة.
- `booking/tasks.py` → تنفيذ المهمة بعد انتهاء فترة السماح.
- `garage/models.py` → التأكد من حالة المكان.
- `settings.py` → إعداد Celery والـ broker (Redis).

---


booking/models.py → إضافة qr_code_image للحجز.

booking/utils.py → كود توليد QR.

booking/views.py → ربط QR بالحجز.

booking/serializers.py → تعديل التفاصيل المرسلة للفرونت.





/api/bookings/initiate/ → لإنشاء حجز + QR

/api/bookings/<id>/ → عرض تفاصيل الحجز (بما في ذلك QR)

