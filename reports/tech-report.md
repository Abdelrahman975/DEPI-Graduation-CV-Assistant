**Technical Report: CV Assistant RAG**

**1. فكرة المشروع**
المشروع هو Web Application محلي يساعد المستخدم في تحليل وتحسين الـ CV. المستخدم يرفع السيرة الذاتية، والنظام يقرأها، يحللها، ويقدم اقتراحات.

المشروع مبني كـ RAG system بسيط: يعني قبل ما الموديل يرد، النظام يبحث في داتا محلية مثل الوظائف وأسئلة الانترفيو، ثم يعطي الموديل السياق فيساعده يرد بشكل أدق.

**2. الفئة المستهدفة**
الفئة الأساسية:
- الطلاب والخريجين الجدد.
- الباحثين عن عمل.
- أشخاص يريدون تحسين CV قبل التقديم.
- المتقدمون لمجالات Data, AI, Software, Cybersecurity.
- Career coaches أو HR teams صغيرة تحتاج أداة مساعدة للتقييم الأولي.

**3. المشاكل التي يحلها**
المشروع يحل مشاكل عملية مثل:
- المستخدم لا يعرف هل CV مناسب للوظائف أم لا.
- المستخدم لا يعرف هل CV مكتوب بطريقة ATS-friendly.
- المستخدم لا يعرف المهارات الناقصة مقارنة بسوق العمل.
- المستخدم يحتاج وظائف مناسبة بدل البحث اليدوي.
- المستخدم يحتاج أسئلة Interview مبنية على خبرته ومجاله.
- المستخدم يحتاج شات يتابع معه نفس المحادثة ويفهم الـ CV المرفوع.

**4. بنية المشروع**
البنية الأساسية:

```text
g_project_cv_g
├── main.py
├── config/
├── core/
├── core/chat_service/
├── dto/
├── routes/
├── prompts/
├── scripts/
├── static/
├── data/
└── storage/
```

أهم الملفات:
- [main.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/main.py): نقطة تشغيل FastAPI وربط الـ routes.
- [config/settings.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/config/settings.py): إعدادات المشروع، مسارات الداتا، Gemini, Chroma, storage.
- [dto/schemas.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/dto/schemas.py): تعريف شكل الـ request والـ response.
- [static/index.html](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/static/index.html): واجهة المستخدم.
- [scripts/build_index.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/scripts/build_index.py): بناء فهرس Chroma من الداتا المحلية.

**5. الداتا المستخدمة**

النسخة الحالية تستخدم ملفين أساسيين:
- `data/clean_jobs.csv`: داتا الوظائف، وتشمل title, company, location, link, source, date, description.
- `data/new/coding_interview_question_bank.csv`: بنك أسئلة interview، ويشمل question, difficulty, category, date.

الوظائف تستخدم في:
- ترشيح الوظائف المناسبة.
- حساب job alignment.
- استخراج matched skills و missing skills.

أسئلة الانترفيو تستخدم في:
- استرجاع أسئلة مناسبة لمجال المستخدم.
- تزويد Gemini بسياق يساعده يولد أسئلة Interview مخصصة.

**6. طبقة الإعدادات**
في [config/settings.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/config/settings.py) يتم تعريف:
- `GOOGLE_API_KEY`: مفتاح Gemini.
- `GEMINI_MODEL`: الموديل، حاليًا `gemini-2.5-flash-lite`.
- `EMBEDDING_MODEL`: موديل embeddings.
- `CONN_STR`: اتصال PostgreSQL اختياري.
- `SESSION_BACKEND`: إما PostgreSQL أو files.
- `DATA_DIR`: مسار الداتا داخل المشروع.
- `CHROMA_DIR`: مكان Chroma index.
- `UPLOAD_DIR`: مكان الملفات المرفوعة.
- `SESSION_DIR`: مكان حفظ المحادثات لو PostgreSQL غير متاح.

**7. نقطة تشغيل التطبيق**
في [main.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/main.py):
- يتم إنشاء FastAPI app.
- يتم تفعيل CORS.
- يتم ربط routes:
  - `routes/cv.py`
  - `routes/conversations.py`
  - `routes/chat.py`
- يتم تقديم الواجهة من `/app`.
- يوجد endpoint للصحة `/health`.
- يوجد endpoint إعدادات عامة `/config`.

**8. الواجهة Frontend**
الواجهة في [static/index.html](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/static/index.html).

وظيفتها:
- إنشاء أو اختيار محادثة.
- رفع CV.
- إرسال رسالة للمساعد.
- استقبال الرد streaming من السيرفر.
- عرض الردود بشكل chat UI.
- عرض نتائج التحليل مثل ATS score والاقتراحات والوظائف.

الواجهة تستخدم Server-Sent Events مع endpoint:

```text
POST /api/v1/chat/stream
```

عشان الرد يظهر تدريجيًا بدل ما ينتظر المستخدم الرد كامل.

**9. إدارة المستخدمين والمحادثات**
الملف المسؤول:

[routes/conversations.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/routes/conversations.py)

Endpoints:
- `POST /api/v1/users`: إنشاء أو جلب user.
- `POST /api/v1/chats`: إنشاء chat session.
- `GET /api/v1/users/{user_id}/chats`: عرض محادثات المستخدم.
- `GET /api/v1/chats/{session_id}`: جلب محادثة كاملة.
- `DELETE /api/v1/chats/{session_id}`: حذف محادثة.

التخزين يتم عن طريق:

[core/session_store.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/session_store.py)

لو PostgreSQL متاح:
- يحفظ users و sessions في جداول PostgreSQL.

لو PostgreSQL غير متاح:
- يرجع تلقائيًا إلى JSON files داخل `storage/sessions`.

**10. رفع وتحليل CV**
الـ endpoint موجود في:

[routes/cv.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/routes/cv.py)

Endpoint:

```text
POST /api/v1/cv/analyze
```

يقبل:
- `file`: ملف CV.
- `user_id`: اختياري.
- `session_id`: اختياري.

بعدها يستدعي:

[core/cv_analysis_service.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/cv_analysis_service.py)

الخطوات:
- التأكد من امتداد الملف.
- التأكد من حجم الملف.
- حفظ الملف في `storage/uploads`.
- قراءة النص من الملف.
- استخراج summary.
- حساب ATS.
- توليد suggestions.
- حفظ كل النتائج داخل session.

**11. قراءة ملفات CV**
المسؤول:

[core/cv_parser.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/cv_parser.py)

يدعم:
- `.pdf`
- `.docx`
- `.txt`

طريقة القراءة:
- TXT يقرأ مباشرة كنص.
- DOCX باستخدام `python-docx`.
- PDF باستخدام PyMuPDF أولًا، ثم pypdf.
- لو PDF عبارة عن صور، يحاول OCR باستخدام Windows OCR لو متاح.

بعد استخراج النص:
- لو النص أقل من 80 حرف، يرجع خطأ واضح للمستخدم.
- يعمل summary بسيط:
  - name
  - email
  - phone
  - skills
  - likely_roles
  - years_experience_hint
  - text_length

**12. استخراج المهارات والكلمات المهمة**
المسؤول:

[core/text_utils.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/text_utils.py)

يحتوي على:
- قائمة `COMMON_SKILLS`.
- دوال استخراج email و phone.
- دالة `extract_known_skills`.
- دالة `top_keywords`.
- دالة `lexical_score`.
- دوال matched terms و missing terms.
- تحويل score إلى label:
  - أقل من 40: `No Fit`
  - من 40 إلى أقل من 70: `Potential Fit`
  - 70 أو أكثر: `Good Fit`

**13. تقييم ATS**
المسؤول:

[core/ats_service.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/ats_service.py)

التقييم لا يعتمد على رقم واحد فقط، بل على breakdown:
- `job_alignment`: مدى تطابق الـ CV مع الوظائف المحلية.
- `skills_coverage`: عدد وتنوع المهارات الموجودة في CV.
- `cv_structure`: هل الـ CV منظم وفيه email, phone, summary, experience, education, skills.
- `impact_evidence`: هل فيه أرقام وإنجازات و action verbs.

الأوزان:
- job alignment: 40%
- skills coverage: 30%
- CV structure: 20%
- impact evidence: 10%

الناتج:
- score من 100.
- label.
- explanation.
- matched skills.
- missing skills.
- top jobs.

**14. ترشيح الوظائف**
المسؤول:

[core/job_service.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/job_service.py)

الخطوات:
- يستدعي `vector_store.search_jobs`.
- يستبعد الوظائف غير الواضحة أو masked.
- يحسب matched terms.
- يحسب missing terms.
- يرجع قائمة `JobRecommendation`.

شكل الوظيفة الراجعة:
- id
- title
- company
- location
- link
- source
- date_posted
- match_score
- matched_terms
- missing_terms
- description_preview

**15. فلترة الوظائف غير الصالحة**
المسؤول:

[core/job_filters.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/job_filters.py)

هذا الملف يمنع ظهور وظائف بياناتها غير واضحة، مثل:
- title بدون حروف.
- company بدون حروف.
- قيم كثيرة مخفية بنجوم `****`.

الدالة الرئيسية:
```python
is_masked_job(row)
```

لو الوظيفة masked أو غير مفهومة، يتم استبعادها من الترشيحات والفهرسة.

**16. Vector Store و RAG**
المسؤول:

[core/vector_store.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/vector_store.py)

يستخدم Chroma محليًا.

Collections الحالية:
- `jobs`
- `interview_questions`

عند build index:
- يقرأ `clean_jobs.csv`.
- يفلتر الوظائف masked.
- يحفظ الوظائف في Chroma.
- يقرأ بنك أسئلة الانترفيو.
- يحفظ الأسئلة في Chroma.

لو Chroma أو embeddings غير متاحة:
- يستخدم fallback search بالـ lexical score.

الـ embedding:
- يحاول استخدام `sentence-transformers/all-MiniLM-L6-v2` من الملفات المحلية.
- لو غير متاح، يستخدم `HashEmbeddingFunction` كـ fallback بسيط.

**17. بناء الفهرس**
المسؤول:

[scripts/build_index.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/scripts/build_index.py)

عند تشغيل:

```powershell
python .\scripts\build_index.py
```

يحدث الآتي:
- يمسح `storage/chroma` القديم بأمان.
- ينشئه من جديد.
- يستدعي `vector_store.build_all`.
- يبني collections للوظائف وأسئلة الانترفيو.
- يطبع عدد العناصر التي تم فهرستها.

**18. Gemini Service**
المسؤول:

[core/chat_service/gemini_service.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/chat_service/gemini_service.py)

وظائفه:
- الاتصال بـ Google Gemini.
- توليد اقتراحات تحسين CV.
- بناء prompt للمحادثة.
- إرسال CV + history + retrieved context للموديل.
- دعم streaming response.
- استخدام fallback لو Gemini غير مضبوط.


لو `GOOGLE_API_KEY` غير موجود:
- لا يتوقف التطبيق.
- يعطي رد fallback يقول إن Gemini غير configured.
- يظل retrieval المحلي يعمل.

**19. Prompt الأساسي**
المسؤول:

[prompts/cv_assistant.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/prompts/cv_assistant.py)

يحدد شخصية وتعليمات المساعد:
- يرد بشكل عملي.
- لا يخترع job links.
- يستخدم CV كمرجع أساسي.
- يستخدم الداتا المسترجعة من النظام.
- يجيب بنفس لغة المستخدم إن أمكن.

**20. Chat Streaming**
المسؤول:

[routes/chat.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/routes/chat.py)

Endpoint:

```text
POST /api/v1/chat/stream
```

يقبل:
- `session_id`
- `message`
- `user_id`
- `file` اختياري

يرجع:
- `StreamingResponse`
- media type: `text/event-stream`

الخدمة التي تنفذ المنطق:

[core/chat_service/streaming_chat_service.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/chat_service/streaming_chat_service.py)

**21. ماذا يحدث عندما المستخدم يرسل رسالة؟**
التتبع خطوة بخطوة:

1. المستخدم يكتب رسالة في الواجهة.
2. الواجهة ترسل request إلى:
   ```text
   POST /api/v1/chat/stream
   ```
3. الطلب يصل إلى [routes/chat.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/routes/chat.py).
4. route يتحقق أن `session_id` موجود عن طريق `session_store.require`.
5. لو المستخدم أرفق CV مع الرسالة، يتم قراءة الملف.
6. route يرجع `StreamingResponse` من `streaming_chat_service.stream_chat`.
7. `StreamingChatService` يرسل event نوعه `start`.
8. لو فيه CV مرفق، يستدعي `cv_analysis_service.analyze_and_save`.
9. يتم تحليل الـ CV وحفظ نتائجه في session.
10. يتم إرسال event نوعه `analysis` يحتوي summary و ATS و suggestions.
11. يتم تحميل session مرة أخرى للحصول على:
    - chat history
    - cv_text
    - ats
    - user data
12. يتم بناء query من رسالة المستخدم ومحتوى الـ CV.
13. يتم البحث في Chroma عن context مناسب:
    - وظائف مشابهة.
    - أسئلة Interview مشابهة.
14. يتم إرسال event نوعه `context` للواجهة بالمصادر.
15. يتم حفظ رسالة المستخدم في history.
16. يتم إرسال CV + السؤال + history + context إلى Gemini.
17. Gemini يبدأ يرجع الرد على أجزاء.
18. كل جزء يخرج للواجهة كـ event نوعه `delta`.
19. الواجهة تعرض الرد تدريجيًا.
20. بعد انتهاء الرد، يتم حفظ رد المساعد في session.
21. يتم إرسال event نوعه `done`.
22. يتم إرسال:
    ```text
    data: [DONE]
    ```

**22. ماذا يحدث لو المستخدم يرفع CV فقط؟**
المسار:
- UI يرسل الملف إلى `/api/v1/cv/analyze` أو يرسله مع `/api/v1/chat/stream`.
- `cv_analysis_service` يحفظ الملف.
- `cv_parser` يستخرج النص.
- `cv_parser.summarize` يستخرج البيانات الأساسية.
- `ats_service.evaluate` يحسب ATS.
- `job_service.recommend` يجيب top jobs.
- `gemini_service.suggest_cv_improvements` يولد اقتراحات.
- `session_store.save` يحفظ النتيجة.
- الواجهة تعرض التحليل.

**23. ماذا يحدث لو المستخدم يطلب وظائف؟**
النظام:
- يأخذ CV text من session.
- يبحث في collection `jobs`.
- يسترجع أقرب وظائف.
- يفلتر masked jobs.
- يحسب matched/missing terms.
- Gemini يستخدم النتائج في الرد.
- لا يخترع روابط، فقط يعرض links الموجودة في الداتا.

**24. ماذا يحدث لو المستخدم يطلب Interview Questions؟**
النظام:
- يأخذ السؤال + CV.
- يبحث في collection `interview_questions`.
- يسترجع أسئلة مشابهة حسب المجال.
- يعطي Gemini هذه الأسئلة كسياق.
- Gemini يولد رد مخصص بناءً على خبرة المستخدم ومحتوى CV.

**25. التخزين**
يوجد 3 أنواع تخزين:
- `storage/uploads`: ملفات CV المرفوعة.
- `storage/chroma`: فهرس Chroma المحلي.
- `storage/sessions`: JSON sessions لو PostgreSQL غير متاح.
- PostgreSQL اختياري عبر `CONN_STR`.

**26. الأمان والتنظيف**
المسؤول:

[core/safety.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/core/safety.py)

يحتوي على:
- `safe_identifier`: تنظيف user_id و session_id.
- `safe_filename`: تنظيف اسم الملف المرفوع.

الهدف:
- منع أسماء ملفات غريبة.
- منع path traversal.
- حفظ الملفات بأسماء آمنة.

**27. Logging**
المسؤول:

[logging_config.py](https://github.com/Abdelrahman975/DEPI-Graduation-CV-Assistant/blob/main/logging_config.py)

يقوم بـ:
- إنشاء log file داخل `storage/logs/app.log`.
- استخدام RotatingFileHandler.
- تقليل ضوضاء مكتبات مثل chromadb و sentence_transformers.
- طباعة logs مهمة في console.

**28. أهم Endpoints**
- `GET /`: معلومات عامة.
- `GET /health`: حالة التطبيق، Gemini، Chroma، session backend.
- `GET /config`: إعدادات عامة آمنة للواجهة.
- `GET /app`: فتح الواجهة.
- `POST /api/v1/users`: إنشاء user.
- `POST /api/v1/chats`: إنشاء chat.
- `GET /api/v1/users/{user_id}/chats`: عرض محادثات user.
- `GET /api/v1/chats/{session_id}`: تفاصيل session.
- `DELETE /api/v1/chats/{session_id}`: حذف session.
- `POST /api/v1/cv/analyze`: تحليل CV.
- `POST /api/v1/chat/stream`: شات streaming.

**29. نقاط القوة في التصميم**
- Local-first: لا يعتمد على S3 أو Pinecone.
- Chroma محلي مناسب للديمو والتطوير.
- fallback storage لو PostgreSQL غير متاح.
- fallback retrieval لو embeddings غير متاحة.
- fallback chat لو Gemini غير configured.
- فصل واضح بين routes و services و schemas.
- تجربة مستخدم أقرب لشات حقيقي بسبب SSE streaming.
- لا يتم اختراع links للوظائف.

**30. ملخص معماري سريع**
المستخدم يتعامل مع UI.  
UI يرسل requests إلى FastAPI routes.  
Routes لا تحتوي منطق كبير، بل تستدعي core services.  
Core services تقرأ CV، تحلل، تبحث في Chroma، تحسب ATS، وتبني prompt.  
Gemini يولد الرد النهائي.  
SessionStore يحفظ المحادثة والنتائج.  
الواجهة تستقبل الرد streaming وتعرضه للمستخدم.

ده هو خط المشروع من البداية للنهاية:  
**CV Upload → Parsing → Summary → ATS Scoring → Job Retrieval → RAG Context → Gemini Response → Streaming UI → Session Storage**.
