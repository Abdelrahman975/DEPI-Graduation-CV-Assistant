# CV Assistant RAG - Code Walkthrough

هذا التقرير يشرح كود مشروع `CV Assistant RAG` من وجهة نظر تقنية، لكن بلغة بسيطة تصلح لطالب جامعي. الهدف أن تفهم:

- بنية المشروع.
- وظيفة كل ملف.
- وظيفة أهم class و function.
- ماذا يحدث بالضبط عندما المستخدم يرسل رسالة.
- ماذا يحدث عندما المستخدم يرفع CV.
- أين يتم التخزين، الفهرسة، البحث، واستدعاء Gemini.

---

## 1. الصورة الكبيرة للمشروع

المشروع عبارة عن تطبيق Web محلي مبني بـ FastAPI. المستخدم يفتح واجهة شات، ينشئ محادثة، يرفع CV، ثم يبدأ يسأل المساعد عن:

- تقييم الـ CV.
- تحسينات للـ CV.
- الوظائف المناسبة.
- أسئلة الانترفيو.
- المهارات الناقصة.

المشروع يستخدم فكرة RAG:

1. المستخدم يرسل سؤال.
2. النظام يبحث في الداتا المحلية، مثل الوظائف وأسئلة الانترفيو.
3. النظام يرسل السؤال + الـ CV + نتائج البحث إلى Gemini.
4. Gemini يرد بناءً على السياق الموجود.

المسار العام:

```text
User UI
  -> FastAPI route
  -> SessionStore
  -> CV parser / VectorStore / ATS / Gemini
  -> Streaming response
  -> UI displays answer
```

---

## 2. هيكل المشروع

```text
g_project_cv_g
├── main.py
├── logging_config.py
├── README.md
├── requirements.txt
├── config/
│   └── settings.py
├── core/
│   ├── ats_service.py
│   ├── cv_analysis_service.py
│   ├── cv_parser.py
│   ├── job_filters.py
│   ├── job_service.py
│   ├── safety.py
│   ├── session_store.py
│   ├── text_utils.py
│   ├── vector_store.py
│   └── chat_service/
│       ├── gemini_service.py
│       └── streaming_chat_service.py
├── dto/
│   └── schemas.py
├── routes/
│   ├── chat.py
│   ├── conversations.py
│   └── cv.py
├── prompts/
│   └── cv_assistant.py
├── scripts/
│   ├── build_index.py
│   └── smoke_check.py
├── static/
│   └── index.html
├── data/
└── storage/
```

أهم فكرة في التنظيم:

- `routes`: يستقبل HTTP requests فقط.
- `core`: يحتوي منطق المشروع الحقيقي.
- `dto`: يحدد شكل البيانات الداخلة والخارجة.
- `config`: الإعدادات.
- `static`: واجهة المستخدم.
- `scripts`: أوامر مساعدة مثل بناء الفهرس.
- `storage`: بيانات مولدة أثناء التشغيل.

---

## 3. نقطة البداية: `main.py`

الملف: `main.py`

هذا هو entry point للتطبيق.

### ماذا يفعل؟

1. يستدعي `configure_logging`.
2. ينشئ FastAPI app.
3. يضبط CORS.
4. يربط routes.
5. يقدم ملفات static.
6. يعرف endpoints عامة مثل `/health` و `/app`.

### الكود المهم

```python
app = FastAPI(...)
```

ينشئ تطبيق FastAPI.

```python
app.include_router(cv.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
```

يربط ملفات routes بالمشروع. بما أن `API_V1_STR = "/api/v1"`، أي endpoint داخل هذه الملفات سيبدأ بـ `/api/v1`.

### Functions داخل `main.py`

#### `root()`

المسار:

```text
GET /
```

يرجع رسالة ترحيب وروابط مهمة:

- docs
- ui
- health

#### `health()`

المسار:

```text
GET /health
```

يرجع حالة النظام:

- هل التطبيق healthy.
- نوع session backend.
- هل Chroma متاح.
- هل Gemini متاح.
- اسم الموديل المستخدم.

مفيد جدًا في debugging.

#### `public_config()`

المسار:

```text
GET /config
```

يرجع إعدادات عامة للواجهة، مثل:

- حجم الرفع المسموح.
- endpoints المهمة.
- هل Chroma متاح.

#### `app_ui()`

المسار:

```text
GET /app
```

يرجع ملف الواجهة:

```text
static/index.html
```

---

## 4. الإعدادات: `config/settings.py`

الملف: `config/settings.py`

يحتوي class اسمها:

```python
class Settings(BaseSettings)
```

هذه class تقرأ الإعدادات من:

- القيم الافتراضية في الكود.
- ملف `.env`.
- environment variables.

### أهم الإعدادات

#### إعدادات التطبيق

```python
APP_NAME = "CV Assistant RAG"
HOST = "0.0.0.0"
PORT = 8000
API_V1_STR = "/api/v1"
```

#### إعدادات Gemini

```python
GOOGLE_API_KEY
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

لو `GOOGLE_API_KEY` موجود، Gemini يشتغل. لو غير موجود، المشروع لا يتوقف، لكن يستخدم fallback responses.

#### إعدادات Embeddings

```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

يستخدم في تحويل النصوص إلى vectors للبحث داخل Chroma.

#### إعدادات التخزين

```python
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = STORAGE_DIR / "chroma"
UPLOAD_DIR = STORAGE_DIR / "uploads"
SESSION_DIR = STORAGE_DIR / "sessions"
LOG_DIR = STORAGE_DIR / "logs"
```

#### PostgreSQL اختياري

```python
CONN_STR
SESSION_BACKEND = "auto"
```

لو PostgreSQL متاح، يحفظ sessions فيه. لو غير متاح، يرجع إلى JSON files.

### Validators

#### `parse_debug`

تحول قيم مثل:

- `"release"`
- `"prod"`
- `"debug"`

إلى boolean مناسب.

#### `normalize_log_level`

يتأكد أن `LOG_LEVEL` قيمة صحيحة مثل:

- INFO
- DEBUG
- ERROR

---

## 5. DTO Schemas: `dto/schemas.py`

هذا الملف يحدد شكل البيانات في API. يعني بدل ما نرجع dictionaries عشوائية، نستخدم Pydantic models.

### `MessageResponse`

Response بسيط:

```python
message: str
```

يستخدم مثلًا عند حذف chat.

### `CVSummary`

يمثل ملخص CV:

- name
- email
- phone
- skills
- likely_roles
- years_experience_hint
- text_length

### `JobRecommendation`

يمثل وظيفة مرشحة:

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

### `ATSResult`

يمثل نتيجة ATS:

- score
- label
- explanation
- score_breakdown
- matched_skills
- missing_skills
- top_jobs

### `CVAnalyzeResponse`

response بعد تحليل CV:

- session_id
- user_id
- filename
- summary
- ats
- improvement_suggestions

### `ChatMessage`

يمثل رسالة داخل chat history:

- role: user / assistant / system
- content

### User and Chat schemas

تستخدم مع `routes/conversations.py`:

- `UserCreateRequest`
- `UserResponse`
- `ChatCreateRequest`
- `ChatSummary`
- `ChatSessionResponse`

---

## 6. مسار المستخدمين والمحادثات: `routes/conversations.py`

هذا الملف مسؤول عن:

- إنشاء user.
- إنشاء chat.
- عرض محادثات user.
- جلب محادثة.
- حذف محادثة.

### `_chat_summary(payload)`

دالة داخلية تحول session payload إلى `ChatSummary`.

تقرأ:

- session_id
- user_id
- title
- created_at
- updated_at
- has_cv
- filename
- messages_count

### `create_or_get_user(request)`

المسار:

```text
POST /api/v1/users
```

يستدعي:

```python
session_store.create_user(...)
```

لو user موجود يرجعه. لو غير موجود ينشئه.

### `create_chat(request)`

المسار:

```text
POST /api/v1/chats
```

ينشئ chat session جديدة للمستخدم.

### `list_user_chats(user_id)`

المسار:

```text
GET /api/v1/users/{user_id}/chats
```

يرجع كل المحادثات الخاصة بالمستخدم.

### `get_chat(session_id)`

المسار:

```text
GET /api/v1/chats/{session_id}
```

يرجع تفاصيل محادثة كاملة:

- messages
- summary
- ats
- suggestions

### `delete_chat(session_id)`

المسار:

```text
DELETE /api/v1/chats/{session_id}
```

يحذف المحادثة وملف CV المرتبط بها إن وجد.

---

## 7. تخزين المحادثات: `core/session_store.py`

هذا الملف يحتوي class مهمة جدًا:

```python
class SessionStore
```

هي المسؤولة عن حفظ واسترجاع users و chats و messages.

### فكرة التخزين

عند التشغيل:

1. يبدأ backend باسم `files`.
2. لو `CONN_STR` موجود و PostgreSQL متاح، يتحول إلى `postgres`.
3. لو PostgreSQL فشل، يظل يستخدم JSON files.

### `__init__`

ينشئ مجلد sessions، ويقرر backend.

### `save(session_id, payload)`

يحفظ session.

لو backend هو PostgreSQL:

```python
self._pg_save(...)
```

لو backend هو files:

يحفظ JSON داخل:

```text
storage/sessions/{session_id}.json
```

### `load(session_id)`

يجلب session من PostgreSQL أو JSON file.

### `require(session_id)`

مثل `load`، لكن لو session غير موجودة يرمي `KeyError`.

تستخدم في routes للتأكد أن المحادثة موجودة.

### `create_user(user_id, display_name)`

ينشئ user أو يرجعه.

في file mode يحفظ كل users في:

```text
storage/sessions/users.json
```

### `create_chat(user_id, title)`

ينشئ payload جديد للمحادثة:

```python
{
  "session_id": ...,
  "user_id": ...,
  "title": ...,
  "cv_text": "",
  "summary": None,
  "ats": None,
  "chat_history": []
}
```

### `list_chats(user_id)`

يرجع محادثات user مرتبة من الأحدث للأقدم.

### `delete_chat(session_id)`

يحذف:

- session.
- ملف CV المرتبط من `storage/uploads` لو موجود.

### `append_message(session_id, role, content)`

يضيف message إلى `chat_history` ويحفظ session مرة أخرى.

### PostgreSQL functions

#### `_connect_postgres`

يحاول الاتصال بـ PostgreSQL.

#### `_ensure_postgres_schema`

ينشئ الجداول:

- `cv_assistant_users`
- `cv_assistant_sessions`

#### `_pg_save`

يحفظ session في PostgreSQL كـ JSONB.

#### `_pg_load`

يقرأ session من PostgreSQL.

#### `_pg_create_user`

ينشئ user في PostgreSQL.

#### `_pg_list_chats`

يرجع sessions من PostgreSQL.

---

## 8. أمان أسماء الملفات والمعرفات: `core/safety.py`

### `safe_identifier(value, fallback_prefix="id")`

ينظف user_id أو session_id بحيث يسمح فقط بـ:

- letters
- numbers
- `-`
- `_`

لو القيمة فارغة، ينشئ id جديد.

### `safe_filename(filename, default="cv.txt")`

ينظف اسم الملف ويمنع path traversal.

مثال:

```text
../../evil.pdf
```

يتحول إلى اسم آمن فقط.

---

## 9. رفع وتحليل CV: `routes/cv.py`

الملف يحتوي endpoint:

```text
POST /api/v1/cv/analyze
```

### `analyze_cv(file, user_id, session_id)`

الخطوات:

1. يقرأ extension من اسم الملف.
2. يتأكد أنه PDF أو DOCX أو TXT.
3. يستدعي:

```python
cv_analysis_service.analyze_and_save(...)
```

4. يرجع `CVAnalyzeResponse`.

هذا route بسيط؛ لا ينفذ التحليل بنفسه. هو فقط يستقبل request ويمرر العمل إلى service.

---

## 10. خدمة تحليل CV: `core/cv_analysis_service.py`

تحتوي:

```python
class CVAnalysisService
```

### `analyze_and_save(file_content, filename, user_id, session_id)`

هذه هي الدالة الرئيسية لتحليل CV.

الخطوات بالتفصيل:

1. تنظيف اسم الملف:

```python
safe_name = safe_filename(filename)
```

2. التأكد من extension.

3. التأكد من الحجم:

```python
MAX_UPLOAD_MB
```

4. تجهيز session_id و user_id.

5. حفظ الملف في:

```text
storage/uploads
```

6. قراءة النص:

```python
cv_text = cv_parser.parse(upload_path)
```

7. استخراج summary:

```python
summary_data = cv_parser.summarize(cv_text)
```

8. حساب ATS:

```python
ats = ats_service.evaluate(cv_text)
```

9. توليد اقتراحات:

```python
suggestions = gemini_service.suggest_cv_improvements(...)
```

10. تحميل session قديمة لو موجودة.

11. إضافة رسالتين للـ chat history:

- المستخدم رفع CV.
- المساعد يقول تم التحليل.

12. حفظ كل شيء في session:

- cv_text
- summary
- ats
- suggestions
- chat_history

13. يرجع result للـ route.

---

## 11. قراءة CV: `core/cv_parser.py`

تحتوي:

```python
class CVParser
```

### `SUPPORTED_EXTENSIONS`

```python
{".pdf", ".docx", ".txt"}
```

### `parse(file_path)`

تحدد نوع الملف:

- TXT -> قراءة مباشرة.
- PDF -> `_parse_pdf`.
- DOCX -> `_parse_docx`.

بعد القراءة:

```python
text = normalize_text(text)
```

لو النص أقل من 80 حرف، يرجع خطأ لأن الملف غالبًا scanned أو غير قابل للقراءة.

### `summarize(text)`

يرجع dictionary فيها:

- الاسم المتوقع.
- الإيميل.
- الهاتف.
- المهارات.
- الأدوار المحتملة.
- عدد الحروف.

يستخدم دوال من `text_utils`.

### `_parse_pdf(file_path)`

يحاول قراءة PDF بثلاث مراحل:

1. PyMuPDF.
2. pypdf.
3. Windows OCR fallback.

لو كلهم فشلوا، يرجع خطأ واضح.

### `_parse_pdf_with_windows_ocr(file_path)`

يفتح صفحات PDF، يحول كل صفحة إلى صورة PNG مؤقتة، ثم يرسلها إلى Windows OCR.

### `_ocr_image_with_windows(image_path)`

ينشئ PowerShell script مؤقت يستخدم Windows Runtime OCR.

لو نجح، يرجع النص المستخرج من الصورة.

### `_parse_docx(file_path)`

يقرأ:

- paragraphs
- table cells

باستخدام `python-docx`.

### `_guess_name(text)`

يحاول تخمين الاسم من أول أسطر في CV.

### `_infer_roles(text, keywords)`

يحاول توقع المجال:

- Data Analyst
- Data Scientist
- Machine Learning Engineer
- Data Engineer
- Software Engineer
- Cybersecurity Analyst

### `_experience_hint(text)`

يبحث عن شكل مثل:

```text
3 years experience
5+ years of experience
```

---

## 12. أدوات النص: `core/text_utils.py`

هذا الملف helper مهم لتحليل النصوص.

### `COMMON_SKILLS`

قائمة مهارات معروفة مثل:

- Python
- SQL
- Machine Learning
- FastAPI
- Docker
- Business Analysis
- UAT

### `STOP_WORDS`

كلمات يتم تجاهلها عند استخراج keywords.

### `GENERIC_MISSING_TERMS`

كلمات عامة لا نريد عرضها كمهارات ناقصة، مثل:

- Developer
- Required
- Responsibilities
- Team

### `normalize_text(text)`

ينظف النص:

- يزيل null characters.
- يحول المسافات الكثيرة إلى مسافة واحدة.

### `extract_email(text)`

يستخدم regex لاستخراج email.

### `extract_phone(text)`

يستخدم regex لاستخراج phone.

### `extract_known_skills(text)`

يبحث داخل النص عن المهارات الموجودة في `COMMON_SKILLS`.

### `top_keywords(text, limit)`

يستخرج أكثر الكلمات المهمة تكرارًا بعد حذف stop words.

### `lexical_score(query, document)`

يحسب تطابق بسيط بين query و document بناءً على الكلمات المشتركة.

يستخدم كـ fallback لو Chroma أو embeddings غير متاحة.

### `matched_terms(left, right)`

يرجع الكلمات أو المهارات الموجودة في النصين.

مثال:

CV فيه Python و SQL، والوظيفة فيها Python و SQL، إذًا يظهروا في matched terms.

### `missing_terms(cv_text, job_text)`

يرجع مهارات موجودة في الوظيفة وغير موجودة في CV.

### `dedupe_keep_order(items)`

يزيل التكرار مع الحفاظ على نفس الترتيب.

### `score_label(score)`

يحول الرقم إلى label:

- `Good Fit`
- `Potential Fit`
- `No Fit`

---

## 13. فهرسة وبحث Chroma: `core/vector_store.py`

تحتوي:

```python
class VectorStore
```

### Collections

```python
JOBS = "jobs"
INTERVIEW = "interview_questions"
```

### `__init__`

يحاول إنشاء Chroma client:

```python
chromadb.PersistentClient(path=settings.CHROMA_DIR)
```

ثم ينشئ embedding function.

لو فشل، يجعل:

```python
chroma_available = False
```

والنظام يستخدم lexical fallback.

### `build_all(reset=True)`

يبني كل collections:

- jobs
- interview questions

### `search_jobs(query, top_k)`

يبحث عن وظائف مناسبة.

لو Chroma متاح:

- يبحث داخل collection.
- يرجع نتائج بعد فلترة masked jobs.

لو Chroma غير متاح:

- يستخدم `_fallback_jobs`.

### `search_interview_questions(query, top_k, difficulty)`

يبحث في أسئلة الانترفيو.

يمكن فلترة difficulty:

- Easy
- Medium
- Hard

### `search_context(query, top_k)`

يجمع context من:

- jobs
- interview questions

ويستخدم في الشات مع Gemini.

### `_build_jobs(reset)`

يقرأ:

```text
data/clean_jobs.csv
```

ثم:

- يستبعد masked jobs.
- يبني document من title, company, location, description.
- يحفظه في Chroma.

### `_build_interview_questions(reset)`

يقرأ:

```text
data/new/coding_interview_question_bank.csv
```

ويحفظ الأسئلة في Chroma.

### `_query_collection(name, query, top_k, where)`

تنفذ query على Chroma collection وترجع:

- document
- metadata
- distance
- `_distance_score`

### `_fallback_jobs(query, top_k)`

لو Chroma غير متاح، يقرأ CSV مباشرة ويحسب lexical score.

### `_get_collection(name, reset)`

يحضر collection من Chroma أو ينشئها.

لو `reset=True` يحذف collection القديمة.

### `_collection_exists(name)`

يتأكد إذا collection موجودة.

### `_add_in_batches`

يضيف documents إلى Chroma على batches حجمها 100.

### `_read_csv(path)`

يقرأ CSV ويرجع list of dicts.

### `_create_embedding_function`

يحاول إنشاء:

```python
LocalSentenceTransformerEmbeddingFunction
```

لو فشل يستخدم:

```python
HashEmbeddingFunction
```

### `LocalSentenceTransformerEmbeddingFunction`

يستخدم `SentenceTransformer` محليًا:

```python
SentenceTransformer(model_name, local_files_only=True)
```

ثم يحول النصوص إلى embeddings.

### `HashEmbeddingFunction`

fallback بسيط يحول الكلمات إلى vector باستخدام hashing.

ليس بجودة sentence-transformers، لكنه يمنع توقف المشروع.

---

## 14. فلترة الوظائف: `core/job_filters.py`

هذا الملف يمنع ظهور وظائف غير مفهومة.

### `is_masked_job(row)`

يرجع `True` لو الوظيفة غير صالحة.

يعتبر الوظيفة غير صالحة لو:

- title لا يحتوي حروف.
- company لا يحتوي حروف.
- title/company/location فيها نجوم كثيرة مثل `*****`.

### `_looks_masked(value)`

يتأكد هل النص شكله masked.

### `_has_letters(value)`

يتأكد أن النص فيه حروف عربية أو إنجليزية.

### `_to_text(value)`

يحول أي value إلى string نظيف.

---

## 15. ترشيح الوظائف: `core/job_service.py`

تحتوي:

```python
class JobService
```

### `recommend(cv_text, top_k)`

الخطوات:

1. يبحث عن وظائف باستخدام:

```python
vector_store.search_jobs(cv_text)
```

2. يستبعد masked jobs.

3. يحسب:

- matched_terms
- missing_terms

4. يبني objects من نوع `JobRecommendation`.

5. يرجع أفضل الوظائف.

---

## 16. تقييم ATS: `core/ats_service.py`

تحتوي:

```python
class ATSService
```

### `evaluate(cv_text, top_jobs=8)`

هذه الدالة الأساسية.

الخطوات:

1. تجلب الوظائف المناسبة:

```python
jobs = job_service.recommend(...)
```

2. تحسب breakdown:

```python
breakdown = self._score_breakdown(cv_text, jobs)
```

3. تحسب score النهائي.

4. تحول score إلى label.

5. تجمع matched و missing skills.

6. تبني explanation.

7. ترجع `ATSResult`.

### `_score_breakdown(cv_text, jobs)`

يرجع:

- job_alignment
- skills_coverage
- cv_structure
- impact_evidence

### `_final_score(breakdown)`

يستخدم الأوزان:

```text
job_alignment: 40%
skills_coverage: 30%
cv_structure: 20%
impact_evidence: 10%
```

### `_job_alignment_score(jobs)`

يعتمد على نتائج job matching.

### `_skills_coverage_score(cv_text)`

يقيم عدد وتنوع المهارات في CV.

### `_structure_score(cv_text)`

يقيم تنظيم CV:

- email
- phone
- summary
- experience
- education
- skills
- projects
- certifications

### `_impact_score(cv_text)`

يبحث عن:

- أرقام.
- نسب.
- action verbs مثل built, developed, improved.

### `_collect_terms(jobs, attr)`

يجمع matched أو missing terms من أفضل الوظائف.

### `_explain(score, label, jobs, breakdown)`

ينشئ شرح مفهوم للمستخدم.

---

## 17. Prompt: `prompts/cv_assistant.py`

يحتوي تعليمات Gemini.

### `CV_ASSISTANT_SYSTEM_PROMPT`

يقول للموديل:

- أنت مساعد CV و interview.
- كن عمليًا ومحددًا.
- لا تخترع job links.
- لو معلومة ناقصة، وضح ذلك.
- استخدم bullets عند الحاجة.

### `CV_IMPROVEMENT_PROMPT`

يطلب من Gemini مراجعة CV وإرجاع اقتراحات عملية.

---

## 18. Gemini Service: `core/chat_service/gemini_service.py`

تحتوي:

```python
class GeminiService
```

### `__init__`

يحاول تجهيز Gemini:

1. يتأكد من `GOOGLE_API_KEY`.
2. يستورد `google.generativeai`.
3. يضبط API key.
4. يجهز model.

لو فشل، يحفظ الخطأ في `init_error`.

### `available`

property ترجع هل Gemini جاهز.

### `suggest_cv_improvements(cv_text, ats_payload)`

تستخدم بعد تحليل CV.

لو Gemini متاح:

- تبني prompt من CV و ATS.
- تطلب bullet list.

لو غير متاح:

- ترجع `_fallback_suggestions`.

### `stream_chat(cv_text, user_message, retrieved_context, history)`

هذه الدالة تستخدم أثناء الشات.

لو Gemini غير متاح:

- ترجع fallback text على chunks.

لو Gemini متاح:

1. تبني prompt.
2. تجرب أكثر من model candidate.
3. تستدعي:

```python
model.generate_content(prompt, stream=True)
```

4. ترجع chunks تدريجيًا.

### `_generate(prompt)`

استدعاء غير streaming، يستخدم في suggestions.

### `_build_chat_prompt(...)`

يبني prompt النهائي الذي يصل إلى Gemini.

يحتوي:

- system prompt
- conversation memory
- CV text
- retrieved local context
- current user message
- instructions

### `_chunk_text(text, size=48)`

يقسم fallback text إلى أجزاء صغيرة كأنه streaming.

### `_get_model(model_name)`

ينشئ أو يرجع model من cache.

### `_model_candidates(configured_model)`

يجهز قائمة موديلات بديلة:

- configured model
- gemini-2.5-flash-lite
- gemini-2.5-flash
- gemini-flash-latest

### `_lines_to_list(text)`

يحول رد Gemini إلى list of suggestions.

### `_is_non_action_line(line)`

يحذف الجمل العامة غير المفيدة مثل:

- here are
- of course

### `_fallback_suggestions(ats_payload)`

اقتراحات جاهزة لو Gemini غير متاح.

### `_fallback_chat(user_message, retrieved_context)`

رد جاهز لو Gemini غير متاح.

---

## 19. Streaming Chat: `core/chat_service/streaming_chat_service.py`

تحتوي:

```python
class StreamingChatService
```

هذه class هي قلب المحادثة.

### `stream_chat(...)`

تستقبل:

- session_id
- message
- user_id
- uploaded_filename
- uploaded_content
- is_disconnected

وترجع async generator من SSE events.

#### الخطوات داخلها

1. تحميل session:

```python
session = session_store.require(session_id)
```

2. إرسال event بداية:

```json
{"type": "start"}
```

3. لو المستخدم رفع ملف مع الرسالة:

```python
cv_analysis_service.analyze_and_save(...)
```

ثم ترسل event:

```json
{"type": "analysis"}
```

4. لو الرسالة فارغة، ينشئ رسالة default.

5. تحميل session بعد التحليل.

6. قراءة:

- history
- cv_text

7. بناء query للبحث:

```python
query = message + CV snippet
```

8. البحث في Chroma:

```python
context = vector_store.search_context(query, top_k=6)
```

9. إرسال event فيه sources:

```json
{"type": "context"}
```

10. حفظ رسالة المستخدم:

```python
session_store.append_message(session_id, "user", current_message)
```

11. استدعاء Gemini streaming:

```python
gemini_service.stream_chat(...)
```

12. كل chunk يخرج كـ:

```json
{"type": "delta", "content": "..."}
```

13. بعد انتهاء الرد، يحفظ رد المساعد.

14. يرسل:

```json
{"type": "done"}
```

15. يرسل:

```text
data: [DONE]
```

### `_client_disconnected(is_disconnected)`

يتأكد هل المستخدم أغلق الاتصال. لو أغلقه، يوقف streaming.

### `_sse(payload)`

يحول dictionary إلى SSE format:

```text
data: {...}

```

### `_source_payload(item)`

ينظف بيانات source قبل إرسالها للواجهة.

---

## 20. Route الشات: `routes/chat.py`

يحتوي endpoint:

```text
POST /api/v1/chat/stream
```

### `chat_stream(...)`

الخطوات:

1. يستقبل form data:

- session_id
- message
- user_id
- file

2. يتأكد أن session موجودة.

3. يقرأ الملف لو موجود.

4. يرجع:

```python
StreamingResponse(...)
```

ويستخدم:

```python
streaming_chat_service.stream_chat(...)
```

---

## 21. ماذا يحدث عندما المستخدم يرسل رسالة؟

هذا أهم flow في المشروع.

### المرحلة 1: من الواجهة

في `static/index.html`، دالة:

```javascript
sendChatMessage(message)
```

تعمل:

1. تتأكد أن فيه chat session.
2. تضيف رسالة المستخدم في الواجهة.
3. تجهز `FormData`.
4. تضيف:

- session_id
- message
- user_id
- file لو موجود

5. ترسل request:

```javascript
fetch(`${API_BASE}/api/v1/chat/stream`, { method: "POST", body: form })
```

6. تبدأ قراءة stream.

### المرحلة 2: FastAPI route

الطلب يصل إلى:

```python
routes/chat.py -> chat_stream()
```

تتحقق من session، ثم ترجع StreamingResponse.

### المرحلة 3: Streaming service

ينتقل التنفيذ إلى:

```python
streaming_chat_service.stream_chat()
```

هنا يحدث كل المنطق الحقيقي:

1. إرسال start event.
2. تحليل CV لو مرفق.
3. بناء query.
4. البحث في Chroma.
5. إرسال context للواجهة.
6. حفظ رسالة المستخدم.
7. إرسال السؤال والسياق إلى Gemini.
8. بث الرد chunk by chunk.
9. حفظ رد المساعد.

### المرحلة 4: Gemini

الدالة:

```python
gemini_service.stream_chat()
```

تبني prompt يحتوي:

- تاريخ المحادثة.
- نص CV.
- نتائج البحث.
- سؤال المستخدم.

ثم تستدعي Gemini streaming.

### المرحلة 5: رجوع الرد للواجهة

الواجهة تستقبل events:

- `start`
- `analysis`
- `context`
- `delta`
- `done`
- `[DONE]`

كل `delta` يتم إضافته إلى bubble المساعد.

---

## 22. ماذا يحدث عندما المستخدم يرفع CV؟

هناك طريقتان:

1. رفع مباشر إلى `/api/v1/cv/analyze`.
2. رفع مع رسالة إلى `/api/v1/chat/stream`.

في الحالتين، الخدمة النهائية هي:

```python
cv_analysis_service.analyze_and_save()
```

الخطوات:

1. حفظ الملف.
2. قراءة النص.
3. استخراج summary.
4. تقييم ATS.
5. ترشيح jobs.
6. اقتراح تحسينات.
7. حفظ كل شيء في session.
8. إرجاع النتائج للواجهة.

---

## 23. ماذا يحدث عند بناء الفهرس؟

الأمر:

```powershell
python .\scripts\build_index.py
```

يشغل:

```python
scripts/build_index.py -> main()
```

الخطوات:

1. `clean_chroma_index()` يمسح `storage/chroma`.
2. يستورد `vector_store`.
3. يستدعي:

```python
vector_store.build_all(reset=True)
```

4. يبني collection الوظائف.
5. يبني collection أسئلة الانترفيو.
6. يطبع الأعداد.

---

## 24. Smoke Check

الملف:

```text
scripts/smoke_check.py
```

### `main()`

يفحص:

- هل FastAPI app يمكن import.
- هل parser يعمل على عينات CV لو موجودة.
- هل ATS score بين 0 و 100.
- هل breakdown يحتوي المفاتيح الصحيحة.

---

## 25. Logging

الملف:

```text
logging_config.py
```

### `configure_logging()`

يضبط:

- log file داخل `storage/logs/app.log`.
- console logging.
- يقلل noise من chromadb و sentence_transformers.

### `_has_named_handler(logger, name)`

يتأكد أن logger لا يضيف نفس handler مرتين.

---

## 26. الواجهة: `static/index.html`

الواجهة تحتوي HTML/CSS/JS في ملف واحد.

أهم JavaScript functions:

### `$`

اختصار لـ:

```javascript
document.getElementById
```

### `showStatus`

يعرض رسالة حالة أو خطأ.

### `addMessage`

يضيف message bubble في الواجهة.

### `addLoadingMessage`

يعرض رسالة انتظار.

### `updateAssistantMessage`

يحدث bubble المساعد أثناء streaming.

### `renderMarkdown`

يحول Markdown إلى HTML.

### `renderAnalysis`

يعرض نتيجة تحليل CV:

- score
- label
- suggestions
- jobs

### `requestJson`

ينفذ fetch لطلبات JSON العادية.

### `initUser`

ينشئ user عند فتح الصفحة.

### `createNewChat`

ينشئ chat session جديدة.

### `ensureChat`

يتأكد أن هناك chat قبل إرسال رسالة.

### `refreshChatList`

يجلب محادثات المستخدم ويعرضها في sidebar.

### `deleteChat`

يحذف chat.

### `loadChat`

يفتح chat قديم ويعرض رسائله ونتائجه.

### `sendChatMessage`

أهم دالة في الواجهة. ترسل message و file إلى:

```text
/api/v1/chat/stream
```

ثم تقرأ SSE stream وتحدث الواجهة.

---

## 27. ملخص Flow كامل

```text
User writes message
  -> static/index.html sendChatMessage
  -> POST /api/v1/chat/stream
  -> routes/chat.py chat_stream
  -> session_store.require
  -> streaming_chat_service.stream_chat
  -> optional cv_analysis_service.analyze_and_save
  -> vector_store.search_context
  -> session_store.append_message(user)
  -> gemini_service.stream_chat
  -> StreamingResponse delta events
  -> UI updates assistant bubble
  -> session_store.append_message(assistant)
```

---

## 28. ملخص Flow رفع CV

```text
User uploads CV
  -> routes/cv.py analyze_cv
  -> cv_analysis_service.analyze_and_save
  -> safety.safe_filename
  -> save file to storage/uploads
  -> cv_parser.parse
  -> cv_parser.summarize
  -> ats_service.evaluate
  -> job_service.recommend
  -> vector_store.search_jobs
  -> gemini_service.suggest_cv_improvements
  -> session_store.save
  -> return CVAnalyzeResponse
```

---

## 29. أهم Objects داخل session

كل session تحتوي غالبًا على:

```json
{
  "session_id": "...",
  "user_id": "...",
  "title": "...",
  "filename": "...",
  "upload_path": "...",
  "cv_text": "...",
  "summary": {...},
  "ats": {...},
  "improvement_suggestions": [...],
  "chat_history": [...]
}
```

---

## 30. كيف تشرح المشروع في المناقشة؟

يمكنك قول:

> المشروع معمول بأسلوب layered architecture. الواجهة ترسل الطلبات إلى FastAPI routes. الـ routes لا تحتوي منطق كبير، لكنها تستدعي services داخل core. عند رفع CV، يتم parsing ثم summarization ثم ATS scoring ثم job matching. عند إرسال رسالة، النظام يسترجع context من Chroma ثم يرسل السؤال والـ CV والـ context إلى Gemini، ويرجع الرد streaming للواجهة. التخزين مرن: PostgreSQL لو متاح، وإلا JSON files محلية.

---

## 31. أين أبدأ لو أريد تعديل شيء؟

- تغيير شكل الواجهة: `static/index.html`
- تغيير قواعد ATS: `core/ats_service.py`
- إضافة مهارات جديدة: `core/text_utils.py`
- تغيير طريقة ترشيح الوظائف: `core/job_service.py`
- تغيير البحث والفهرسة: `core/vector_store.py`
- تغيير prompt المساعد: `prompts/cv_assistant.py`
- تغيير Gemini logic: `core/chat_service/gemini_service.py`
- تغيير streaming flow: `core/chat_service/streaming_chat_service.py`
- تغيير التخزين: `core/session_store.py`
- تغيير endpoints: `routes/`

---

## 32. الخلاصة التقنية

المشروع يتكون من:

- FastAPI backend.
- HTML/JS frontend.
- Local Chroma vector store.
- Gemini LLM integration.
- CV parser.
- ATS scoring engine.
- Job recommendation engine.
- Conversation/session storage.
- Streaming chat over SSE.

أهم نقطة في الكود أن كل جزء منفصل:

- route يستقبل الطلب.
- service ينفذ المنطق.
- schema ينظم البيانات.
- storage يحفظ الحالة.
- vector store يسترجع السياق.
- Gemini يولد الرد.
