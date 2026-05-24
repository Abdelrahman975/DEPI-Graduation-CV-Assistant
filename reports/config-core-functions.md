# شرح كود `config` و `core`

هذا الملف مخصص لشرح الكود فقط داخل:

- `config`
- `core`

لا يحتوي هذا الملف على شرح فكرة المشروع أو العرض التقديمي. هو فقط شرح للملفات، الـ classes، والـ functions الموجودة في هذه المجلدات.

---

## `config/__init__.py`

ملف فارغ تقريبًا. وجوده يجعل مجلد `config` Python package يمكن استيراده.

مثال:

```python
from config.settings import settings
```

---

## `config/settings.py`

هذا الملف يحتوي إعدادات التطبيق كلها.

### `class Settings(BaseSettings)`

Class مبنية على `pydantic_settings.BaseSettings`.

وظيفتها:

- قراءة الإعدادات الافتراضية من الكود.
- قراءة القيم من ملف `.env`.
- قراءة environment variables من النظام.
- تحويل بعض القيم إلى أنواع صحيحة مثل `bool`, `Path`, `int`.

أهم attributes داخلها:

- `APP_NAME`: اسم التطبيق.
- `DEBUG`: حالة debug.
- `HOST`: عنوان تشغيل السيرفر.
- `PORT`: بورت التشغيل.
- `API_V1_STR`: prefix للـ API.
- `GOOGLE_API_KEY`: مفتاح Gemini.
- `GEMINI_MODEL`: اسم موديل Gemini.
- `EMBEDDING_MODEL`: اسم موديل embeddings.
- `CONN_STR`: connection string لـ PostgreSQL.
- `SESSION_BACKEND`: طريقة تخزين الجلسات.
- `LOG_LEVEL`: مستوى الـ logging.
- `CORS_ORIGINS`: origins المسموح بها.
- `PROJECT_ROOT`: مسار جذر المشروع.
- `DATA_DIR`: مسار مجلد الداتا.
- `CLEAN_JOBS_PATH`: مسار ملف الوظائف.
- `INTERVIEW_QUESTIONS_PATH`: مسار بنك أسئلة الانترفيو.
- `STORAGE_DIR`: مسار مجلد التخزين.
- `CHROMA_DIR`: مسار Chroma.
- `UPLOAD_DIR`: مسار الملفات المرفوعة.
- `SESSION_DIR`: مسار session files.
- `LOG_DIR`: مسار logs.
- `MAX_UPLOAD_MB`: أقصى حجم upload.
- `DEFAULT_TOP_JOBS`: عدد الوظائف الافتراضي.

### `cors_origins(self) -> list[str]`

Property ترجع قائمة CORS origins.

الكود يأخذ `CORS_ORIGINS` كـ string مثل:

```text
*
```

أو:

```text
http://localhost:3000,http://localhost:8000
```

ثم يحولها إلى list.

لو النتيجة فاضية، يرجع:

```python
["*"]
```

تستخدم في `main.py` عند إعداد `CORSMiddleware`.

### `parse_debug(cls, value)`

Validator لحقل `DEBUG`.

وظيفته تحويل قيم نصية إلى boolean.

أمثلة تتحول إلى `True`:

- `"1"`
- `"true"`
- `"yes"`
- `"debug"`
- `"dev"`
- `"development"`

أمثلة تتحول إلى `False`:

- `"0"`
- `"false"`
- `"no"`
- `"release"`
- `"prod"`
- `"production"`

لو القيمة ليست نصًا أو bool، ترجع كما هي ليحاول Pydantic التعامل معها.

### `normalize_log_level(cls, value)`

Validator لحقل `LOG_LEVEL`.

يحول القيمة إلى uppercase ويتأكد أنها واحدة من:

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

لو القيمة غير صحيحة، يرجع:

```python
"INFO"
```

### `class Config`

إعدادات Pydantic الداخلية.

```python
env_file = ".env"
env_file_encoding = "utf-8"
case_sensitive = True
extra = "ignore"
```

معناها:

- اقرأ القيم من `.env`.
- استخدم UTF-8.
- أسماء المتغيرات حساسة لحالة الحروف.
- تجاهل أي قيم إضافية غير معرفة في class.

### `settings = Settings()`

ينشئ object واحد من `Settings` يتم استيراده في باقي المشروع.

مثال:

```python
from config.settings import settings
```

---

## `core/__init__.py`

ملف فارغ تقريبًا. وجوده يجعل مجلد `core` Python package يمكن استيراده.

---

## `core/safety.py`

هذا الملف يحتوي دوال تنظيف identifiers وأسماء الملفات.

### `safe_identifier(value: str | None, fallback_prefix: str = "id") -> str`

تنظف قيمة مثل `user_id` أو `session_id`.

تسمح فقط بـ:

- الحروف.
- الأرقام.
- `-`
- `_`

أي رمز آخر يتم حذفه.

لو الناتج فارغ، تنشئ id جديد بهذا الشكل:

```python
f"{fallback_prefix}-{uuid.uuid4()}"
```

مثال:

```python
safe_identifier("../../abc!!")
```

يرجع تقريبًا:

```text
abc
```

### `safe_filename(filename: str | None, default: str = "cv.txt") -> str`

تنظف اسم الملف المرفوع.

تستخدم:

```python
Path(filename).name
```

لأخذ اسم الملف فقط بدون أي path.

تسمح فقط بـ:

- الحروف.
- الأرقام.
- `.`
- `_`
- `-`
- space

أي رمز آخر يتحول إلى `_`.

لو الاسم فارغ، ترجع:

```python
"cv.txt"
```

الغرض منها حماية التخزين من أسماء ملفات خطيرة أو paths خارج مجلد المشروع.

---

## `core/text_utils.py`

هذا الملف يحتوي دوال مساعدة لمعالجة النصوص واستخراج المهارات والتقييمات البسيطة.

### Constants

#### `COMMON_SKILLS`

مجموعة مهارات معروفة يتم البحث عنها داخل CV أو job description.

أمثلة:

- Python
- SQL
- Machine Learning
- FastAPI
- Docker
- Business Analysis
- UAT

#### `STOP_WORDS`

كلمات عامة يتم تجاهلها عند استخراج keywords.

مثال:

- the
- and
- job
- team
- experience
- required

#### `GENERIC_MISSING_TERMS`

كلمات عامة لا نريد إظهارها كمهارات ناقصة.

مثال:

- Developer
- Required
- Responsibilities
- Team
- Role

#### `DISPLAY_NOISE_TERMS`

نسخة lowercase من `GENERIC_MISSING_TERMS`.

تستخدم لتصفية الكلمات العامة من النتائج المعروضة.

### `normalize_text(text: str) -> str`

تنظف النص.

الخطوات:

1. تستبدل `\x00` بمسافة.
2. تحول أي مسافات متكررة أو أسطر كثيرة إلى مسافة واحدة.
3. تعمل `strip`.

ترجع النص في شكل نظيف.

### `extract_email(text: str) -> str | None`

تبحث عن أول email داخل النص باستخدام regex.

لو وجدت email، ترجعه.

لو لم تجد، ترجع:

```python
None
```

### `extract_phone(text: str) -> str | None`

تبحث عن رقم هاتف داخل النص باستخدام regex.

يدعم أرقام فيها:

- `+`
- spaces
- `.`
- `-`
- brackets

لو لم يجد رقم، يرجع `None`.

### `extract_known_skills(text: str) -> List[str]`

تبحث داخل النص عن المهارات الموجودة في `COMMON_SKILLS`.

الخطوات:

1. تحول النص إلى lowercase.
2. ترتب المهارات من الأطول للأقصر.
3. تبحث عن كل skill باستخدام regex.
4. تضيف المهارة لو موجودة.
5. تزيل التكرار عن طريق `dedupe_keep_order`.

ترجع list مثل:

```python
["Python", "Sql", "Fastapi"]
```

### `top_keywords(text: str, limit: int = 30) -> List[str]`

تستخرج أهم الكلمات المتكررة من النص.

الخطوات:

1. تستخدم regex لاستخراج الكلمات الإنجليزية.
2. تستبعد الكلمات الموجودة في `STOP_WORDS`.
3. تستبعد الكلمات القصيرة.
4. تعد التكرار باستخدام `Counter`.
5. ترجع أكثر الكلمات تكرارًا حسب `limit`.

### `lexical_score(query: str, document: str) -> float`

تحسب score بسيط بين query و document بناءً على الكلمات المشتركة.

الخطوات:

1. تستخرج keywords من query.
2. تستخرج keywords من document.
3. تحسب overlap بين المجموعتين.
4. تحسب recall و precision.
5. ترجع score من 100 تقريبًا.

تستخدم كـ fallback لو Chroma أو embeddings غير متاحة.

### `matched_terms(left: str, right: str, limit: int = 12) -> List[str]`

تستخرج الكلمات أو المهارات المشتركة بين نصين.

تستخدم غالبًا بين:

- CV text
- Job description

الخطوات:

1. تستخرج skills معروفة من النص الأول.
2. تتحقق أي skill منها موجودة في النص الثاني.
3. تستخرج keywords مشتركة.
4. تستبعد noise terms.
5. تزيل التكرار.
6. ترجع أول `limit` نتيجة.

### `missing_terms(cv_text: str, job_text: str, limit: int = 12) -> List[str]`

تستخرج المهارات أو الكلمات المهمة الموجودة في job description وغير موجودة في CV.

الخطوات:

1. تستخرج skills من job text.
2. تستبعد أي skill موجودة في CV.
3. تستبعد generic terms.
4. لو النتائج قليلة، تضيف keywords مهمة من job text غير موجودة في CV.
5. ترجع أول `limit` نتيجة.

### `dedupe_keep_order(items: Iterable[str]) -> List[str]`

تزيل التكرار من list مع الحفاظ على ترتيب العناصر.

مثال:

```python
["Python", "SQL", "Python"]
```

تصبح:

```python
["Python", "SQL"]
```

### `score_label(score: float) -> str`

تحول score رقمي إلى label:

- إذا score >= 70 يرجع `Good Fit`.
- إذا score >= 40 يرجع `Potential Fit`.
- غير ذلك يرجع `No Fit`.

---

## `core/job_filters.py`

هذا الملف يفلتر الوظائف غير الصالحة أو المخفية.

### `is_masked_job(row: Mapping[str, object]) -> bool`

تحدد هل job row غير صالحة.

الخطوات:

1. تأخذ `title`, `company`, `location`.
2. تحولهم إلى نص باستخدام `_to_text`.
3. لو title أو company لا يحتويان حروف، ترجع `True`.
4. تفحص هل أي field من الثلاثة يبدو masked باستخدام `_looks_masked`.
5. لو أي field masked، ترجع `True`.
6. لو الوظيفة طبيعية، ترجع `False`.

تستخدم في:

- `vector_store.py` أثناء بناء فهرس الوظائف.
- `job_service.py` أثناء الترشيح.

### `_looks_masked(value: str) -> bool`

تفحص هل النص يبدو مخفيًا بالنجوم.

أمثلة masked:

```text
*******
*** *** ***
Company ****
```

الخطوات:

1. تعمل `strip`.
2. تزيل المسافات لحساب نسبة النجوم.
3. لو فيه 3 نجوم أو أكثر ونسبة النجوم عالية، ترجع `True`.
4. تفصل النص إلى tokens.
5. لو وجدت أكثر من token مكون فقط من نجوم، ترجع `True`.
6. غير ذلك ترجع `False`.

### `_has_letters(value: str) -> bool`

تتحقق هل النص يحتوي على حروف إنجليزية أو عربية.

تستخدم regex:

```python
[A-Za-z\u0600-\u06FF]
```

### `_to_text(value: object) -> str`

تحول أي قيمة إلى string.

لو القيمة `None`، تتحول إلى string فارغ.

ثم تعمل `strip`.

---

## `core/job_service.py`

هذا الملف يحتوي منطق ترشيح الوظائف.

### `class JobService`

Service مسؤولة عن تحويل نتائج البحث إلى `JobRecommendation`.

### `recommend(self, cv_text: str, top_k: int | None = None) -> List[JobRecommendation]`

ترشح وظائف بناءً على نص CV.

الخطوات:

1. لو `top_k` غير محدد، يستخدم:

```python
settings.DEFAULT_TOP_JOBS
```

2. يبحث في `vector_store`:

```python
results = vector_store.search_jobs(cv_text, top_k=top_k)
```

3. ينشئ list فارغة اسمها `recommendations`.

4. يمر على كل result.

5. لو الوظيفة masked، يتخطاها:

```python
if is_masked_job(result):
    continue
```

6. يأخذ document والـ score.

7. يبني object من `JobRecommendation` يحتوي:

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

8. يرجع أول `top_k` وظيفة.

### `job_service = JobService()`

Object جاهز يتم استيراده في باقي المشروع.

---

## `core/ats_service.py`

هذا الملف يحتوي منطق تقييم ATS.

### `class ATSService`

Service مسؤولة عن تقييم CV وإرجاع `ATSResult`.

### `evaluate(self, cv_text: str, top_jobs: int = 8) -> ATSResult`

الدالة الرئيسية للتقييم.

الخطوات:

1. تجلب وظائف مناسبة:

```python
jobs = job_service.recommend(cv_text, top_k=top_jobs)
```

2. تحسب breakdown:

```python
breakdown = self._score_breakdown(cv_text, jobs)
```

3. تحسب score النهائي:

```python
final_score = self._final_score(breakdown)
```

4. تحول score إلى label:

```python
label = score_label(final_score)
```

5. تجمع المهارات المتطابقة:

```python
matched = self._collect_terms(jobs, "matched_terms")
```

6. تجمع المهارات الناقصة:

```python
missing = self._collect_terms(jobs, "missing_terms")
```

7. تنشئ explanation.

8. ترجع `ATSResult`.

### `_blend_score(self, jobs: List[JobRecommendation]) -> float`

تحسب score مدمج من أفضل الوظائف.

الخطوات:

1. لو لا توجد وظائف، ترجع `0.0`.
2. تأخذ scores أول 5 وظائف.
3. تحسب أعلى score.
4. تحسب المتوسط.
5. ترجع:

```python
0.7 * best + 0.3 * average
```

### `_score_breakdown(self, cv_text: str, jobs: List[JobRecommendation]) -> dict[str, float]`

ترجع breakdown مكون من:

- `job_alignment`
- `skills_coverage`
- `cv_structure`
- `impact_evidence`

كل جزء يتم حسابه بدالة منفصلة.

### `_final_score(self, breakdown: dict[str, float]) -> float`

تحسب score النهائي باستخدام أوزان:

```python
job_alignment = 0.40
skills_coverage = 0.30
cv_structure = 0.20
impact_evidence = 0.10
```

ثم تحد النتيجة بين 0 و 100.

### `_job_alignment_score(self, jobs: List[JobRecommendation]) -> float`

تحسب مدى ارتباط CV بأفضل الوظائف.

الخطوات:

1. تستدعي `_blend_score`.
2. لو score صفر، ترجع صفر.
3. تحول retrieval score المحافظ إلى score أكبر مناسب لـ ATS:

```python
15 + raw * 2.15
```

4. تحد النتيجة بين 0 و 100.

### `_skills_coverage_score(self, cv_text: str) -> float`

تحسب score بناءً على المهارات الموجودة في CV.

الخطوات:

1. تستخرج skills من CV.
2. كل skill تضيف 5 درجات بحد أقصى 70.
3. تضيف bonus لو CV يحتوي مجموعات مهارات مهمة مثل:

- programming
- machine learning
- business analysis
- cloud/devops
- web frameworks
- databases

4. تحد النتيجة عند 100.

### `_structure_score(self, cv_text: str) -> float`

تحسب score لتنظيم CV.

تضيف درجات عند وجود:

- email
- phone
- summary/profile/objective
- experience
- education
- skills
- projects
- certifications

وتضيف درجات إضافية حسب طول CV بالكلمات.

### `_impact_score(self, cv_text: str) -> float`

تحسب score للأثر والإنجازات.

تبحث عن:

- أرقام.
- نسب مئوية.
- مبالغ.
- action verbs مثل:
  - built
  - developed
  - improved
  - automated
  - managed

كل رقم أو فعل يرفع score.

### `_collect_terms(self, jobs: List[JobRecommendation], attr: str) -> List[str]`

تجمع terms من أول 5 وظائف.

`attr` قد يكون:

- `matched_terms`
- `missing_terms`

تزيل التكرار وترجع أول 15 term.

### `_explain(self, score, label, jobs, breakdown) -> str`

تنشئ رسالة شرح للـ ATS result.

لو لا توجد وظائف:

```text
No local jobs were available for comparison.
```

لو `Good Fit`:

ترجع رسالة تقول إن CV قوي مع أقرب وظيفة.

لو `Potential Fit`:

ترجع رسالة تقول إن CV متوسط ويحتاج تحسين keywords والإنجازات.

لو `No Fit`:

ترجع رسالة تقول إن التوافق منخفض.

### `ats_service = ATSService()`

Object جاهز للاستخدام في باقي المشروع.

---

## `core/cv_parser.py`

هذا الملف يحتوي كود قراءة ملفات CV.

### `class CVParser`

Service مسؤولة عن استخراج النص والملخص من CV.

### `SUPPORTED_EXTENSIONS`

امتدادات الملفات المدعومة:

```python
{".pdf", ".docx", ".txt"}
```

### `parse(self, file_path: Path) -> str`

الدالة الرئيسية لاستخراج النص من الملف.

الخطوات:

1. تقرأ extension.
2. لو extension غير مدعوم، ترمي `ValueError`.
3. لو الملف TXT، تقرأه مباشرة.
4. لو PDF، تستدعي `_parse_pdf`.
5. لو DOCX، تستدعي `_parse_docx`.
6. تنظف النص باستخدام `normalize_text`.
7. لو النص أقل من 80 حرف، ترمي `ValueError` برسالة عربية واضحة.
8. ترجع النص.

### `summarize(self, text: str) -> Dict`

تستخرج summary من نص CV.

الخطوات:

1. تستخرج skills:

```python
extract_known_skills(text)
```

2. تستخرج keywords:

```python
top_keywords(text, limit=20)
```

3. تستنتج roles:

```python
self._infer_roles(text, keywords)
```

4. ترجع dictionary يحتوي:

- name
- email
- phone
- skills
- likely_roles
- years_experience_hint
- text_length

### `_parse_pdf(self, file_path: Path) -> str`

تقرأ PDF.

تحاول 3 طرق:

1. PyMuPDF:

```python
import fitz
```

2. pypdf:

```python
from pypdf import PdfReader
```

3. Windows OCR:

```python
self._parse_pdf_with_windows_ocr(file_path)
```

لو كل الطرق فشلت، ترمي `RuntimeError` برسالة توضح أن PDF قد يكون scanned.

### `_parse_pdf_with_windows_ocr(self, file_path: Path) -> str`

تحاول قراءة PDF المصور عن طريق OCR.

الخطوات:

1. تفتح PDF باستخدام PyMuPDF.
2. تنشئ temporary directory.
3. تحول كل صفحة إلى صورة PNG.
4. تستدعي `_ocr_image_with_windows` على كل صورة.
5. تجمع النصوص وترجعها.

لو أي خطأ حصل، ترجع string فارغ.

### `_ocr_image_with_windows(self, image_path: Path) -> str`

تستخدم Windows OCR لقراءة صورة.

الخطوات:

1. تنشئ PowerShell script مؤقت.
2. السكريبت يستخدم Windows Runtime APIs:
   - `Windows.Media.Ocr.OcrEngine`
   - `BitmapDecoder`
   - `SoftwareBitmap`
3. تشغل السكريبت باستخدام `subprocess.run`.
4. لو نجح، ترجع `stdout`.
5. لو فشل، ترجع string فارغ.
6. تحذف السكريبت المؤقت في `finally`.

### `_parse_docx(self, file_path: Path) -> str`

تقرأ ملف Word.

الخطوات:

1. تستورد `Document` من `docx`.
2. تقرأ paragraphs.
3. تقرأ cells داخل الجداول.
4. تجمع النص كله وترجعه.

لو `python-docx` غير مثبت، ترمي `RuntimeError`.

### `_guess_name(self, text: str) -> str | None`

تحاول تخمين الاسم من أول 8 أسطر.

الشروط:

- السطر يحتوي من 2 إلى 4 كلمات.
- لا يحتوي `@`.
- لا يحتوي أرقام.

لو وجد سطر مناسب، يرجعه.

لو لم يجد، يرجع `None`.

### `_infer_roles(self, text: str, keywords: List[str]) -> List[str]`

تستنتج الأدوار المحتملة من CV.

تستخدم rules ثابتة.

مثال:

لو النص يحتوي:

- SQL
- Tableau
- Power BI

قد يرجع:

```python
["Data Analyst"]
```

الأدوار المدعومة في rules:

- Data Analyst
- Data Scientist
- Machine Learning Engineer
- Data Engineer
- Software Engineer
- Cybersecurity Analyst

لو لم يجد أي role، يرجع:

```python
["General Technology Candidate"]
```

### `_experience_hint(self, text: str) -> str | None`

تبحث عن صيغة سنوات خبرة.

Regex يلتقط مثل:

```text
3 years experience
5+ years of experience
```

لو وجد، يرجع النص المطابق.

لو لم يجد، يرجع `None`.

### `cv_parser = CVParser()`

Object جاهز للاستخدام.

---

## `core/cv_analysis_service.py`

هذا الملف يربط قراءة CV، تقييم ATS، الاقتراحات، وحفظ session.

### `class CVAnalysisService`

Service مسؤولة عن تنفيذ تحليل CV كامل وحفظ النتيجة.

### `analyze_and_save(self, file_content, filename, user_id=None, session_id=None) -> Dict[str, Any]`

الدالة الرئيسية لتحليل CV.

الخطوات:

1. تنظف اسم الملف:

```python
safe_name = safe_filename(filename)
```

2. تقرأ extension.

3. تتأكد أن extension مدعوم.

4. تتحقق من حجم الملف:

```python
settings.MAX_UPLOAD_MB
```

5. تجهز `session_id`.

لو موجود، تنظفه.

لو غير موجود، تنشئ UUID.

6. تجهز `user_id`.

لو غير موجود، تستخدم:

```python
"anonymous"
```

7. تنشئ upload directory.

8. تحفظ الملف في:

```python
settings.UPLOAD_DIR / f"{session_id}_{safe_name}"
```

9. تستخرج نص CV:

```python
cv_text = cv_parser.parse(upload_path)
```

10. تستخرج summary:

```python
summary_data = cv_parser.summarize(cv_text)
```

11. تحسب ATS:

```python
ats = ats_service.evaluate(cv_text, top_jobs=settings.DEFAULT_TOP_JOBS)
```

12. تولد suggestions:

```python
suggestions = gemini_service.suggest_cv_improvements(cv_text, ats.model_dump())
```

13. تحمل session قديمة لو موجودة:

```python
existing = session_store.load(session_id) or {}
```

14. تضيف رسالتين إلى `chat_history`:

- رسالة user تقول إنه رفع CV.
- رسالة assistant تقول إن التحليل تم.

15. تبني payload كامل.

16. تحفظه:

```python
session_store.save(session_id, payload)
```

17. ترجع dictionary يحتوي:

- session_id
- user_id
- filename
- summary
- ats
- improvement_suggestions
- cv_text
- payload

### `cv_analysis_service = CVAnalysisService()`

Object جاهز للاستخدام.

---

## `core/session_store.py`

هذا الملف مسؤول عن حفظ واسترجاع المستخدمين والمحادثات.

### `class SessionStore`

تدير التخزين بطريقتين:

- PostgreSQL لو متاح.
- JSON files لو PostgreSQL غير متاح.

### `__init__(self, session_dir: Path | None = None)`

تهيئة التخزين.

الخطوات:

1. تحدد session directory.
2. تنشئ المجلد.
3. تضبط backend الافتراضي:

```python
self.backend = "files"
```

4. لو `CONN_STR` موجود و `SESSION_BACKEND` يسمح بـ postgres، تستدعي `_connect_postgres`.

### `save(self, session_id: str, payload: Dict[str, Any]) -> None`

تحفظ session.

الخطوات:

1. تضيف أو تحدث:

```python
payload["updated_at"]
```

2. لو backend هو `postgres`، تستدعي `_pg_save`.
3. لو backend هو `files`، تحفظ JSON file.

### `load(self, session_id: str) -> Optional[Dict[str, Any]]`

تقرأ session.

لو backend `postgres`:

```python
self._pg_load(session_id)
```

لو backend `files`:

تقرأ:

```text
storage/sessions/{session_id}.json
```

لو الملف غير موجود، ترجع `None`.

### `require(self, session_id: str) -> Dict[str, Any]`

تستدعي `load`.

لو النتيجة `None`، ترمي:

```python
KeyError
```

تستخدم في routes التي تحتاج session موجودة.

### `create_user(self, user_id=None, display_name=None) -> Dict[str, Any]`

تنشئ user أو ترجعه.

لو backend postgres:

```python
self._pg_create_user(...)
```

لو files:

1. يقرأ `users.json`.
2. لو user غير موجود، يضيفه.
3. يحفظ الملف.
4. يرجع user data.

### `create_chat(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]`

تنشئ chat session جديدة.

تضع قيم افتراضية:

- filename = None
- cv_text = ""
- summary = None
- ats = None
- improvement_suggestions = []
- chat_history = []

ثم تحفظ session وترجع payload.

### `list_chats(self, user_id: str) -> List[Dict[str, Any]]`

ترجع كل sessions الخاصة بمستخدم.

لو postgres:

```python
self._pg_list_chats(user_id)
```

لو files:

1. تمر على JSON files في session_dir.
2. تتجاهل `users.json`.
3. تقرأ كل session.
4. تختار sessions التي `user_id` فيها يساوي المطلوب.
5. ترتبهم حسب `updated_at` من الأحدث.

### `delete_chat(self, session_id: str) -> bool`

تحذف chat session.

الخطوات:

1. تحمل session.
2. لو postgres، تحذف row من table.
3. لو files، تحذف JSON file.
4. لو يوجد upload_path، تحذف ملف CV من `UPLOAD_DIR`.
5. ترجع `True` لو تم الحذف.
6. ترجع `False` لو session غير موجودة.

### `append_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]`

تضيف رسالة إلى `chat_history`.

الخطوات:

1. تجلب session باستخدام `require`.
2. تضمن وجود `chat_history`.
3. تضيف:

```python
{"role": role, "content": content}
```

4. تحفظ session.
5. ترجع session.

### `_path(self, session_id: str) -> Path`

ترجع مسار JSON file الخاص بالـ session.

تستخدم `safe_identifier` قبل بناء اسم الملف.

### `_connect_postgres(self) -> None`

تحاول الاتصال بـ PostgreSQL.

الخطوات:

1. تستورد `psycopg`.
2. تنشئ connection.
3. تفعل autocommit.
4. تستدعي `_ensure_postgres_schema`.
5. تضبط:

```python
self.backend = "postgres"
```

لو حدث خطأ، تحفظه في `db_error` وتبقي backend على `files`.

### `_ensure_postgres_schema(self) -> None`

تنشئ الجداول المطلوبة إذا لم تكن موجودة.

تستخدم advisory lock لمنع أكثر من process ينشئ الجداول في نفس الوقت.

الجداول:

- `cv_assistant_users`
- `cv_assistant_sessions`

### `_pg_save(self, session_id: str, payload: Dict[str, Any]) -> None`

تحفظ session في PostgreSQL.

تستخدم:

```sql
INSERT ... ON CONFLICT DO UPDATE
```

وتحفظ payload كـ `JSONB`.

### `_pg_load(self, session_id: str) -> Optional[Dict[str, Any]]`

تقرأ payload من جدول `cv_assistant_sessions`.

لو لا يوجد row، ترجع `None`.

لو payload string، تحوله بـ `json.loads`.

### `_pg_create_user(self, user_id: str, display_name: Optional[str] = None) -> Dict[str, Any]`

تنشئ user في PostgreSQL.

تستخدم:

```sql
ON CONFLICT DO NOTHING
```

ثم تقرأ user وترجعه.

### `_pg_list_chats(self, user_id: str) -> List[Dict[str, Any]]`

تقرأ كل sessions الخاصة بـ user من PostgreSQL.

ترتبهم:

```sql
ORDER BY updated_at DESC
```

ثم ترجع list من payloads.

### `session_store = SessionStore()`

Object جاهز للاستخدام.

---

## `core/vector_store.py`

هذا الملف مسؤول عن Chroma والبحث في الوظائف والأسئلة.

### `class VectorStore`

تدير:

- Chroma client.
- بناء الفهرس.
- البحث في jobs.
- البحث في interview questions.
- fallback search.

### `__init__(self)`

تهيئة vector store.

الخطوات:

1. تضبط:

```python
self.chroma_available = False
self.client = None
self.embedding_function = None
```

2. تحاول استيراد Chroma.
3. تنشئ `settings.CHROMA_DIR`.
4. تنشئ `PersistentClient`.
5. تنشئ embedding function.
6. لو كل شيء نجح، تجعل `chroma_available = True`.
7. لو فشل، تحفظ الخطأ في `init_error`.

### `build_all(self, reset: bool = True) -> Dict[str, int]`

يبني كل collections.

يرجع dictionary:

```python
{
  "jobs": count,
  "interview_questions": count
}
```

### `search_jobs(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]`

يبحث عن الوظائف المناسبة.

الخطوات:

1. يحدد `search_k` أكبر من `top_k` حتى يستطيع فلترة masked jobs.
2. لو Chroma متاح و collection موجودة:
   - يستدعي `_query_collection`.
   - يفلتر masked jobs.
   - يرجع أول `top_k`.
3. لو Chroma غير متاح:
   - يرجع `_fallback_jobs`.

### `search_interview_questions(self, query, top_k=8, difficulty=None)`

يبحث في أسئلة الانترفيو.

لو Chroma متاح:

- يستخدم `_query_collection`.
- لو difficulty موجودة، يستخدم filter.

لو Chroma غير متاح:

- يقرأ CSV.
- يفلتر difficulty.
- يحسب lexical score لكل سؤال.
- يرجع أعلى نتائج.

### `search_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]`

يجمع context للـ chat.

الخطوات:

1. يبحث في jobs.
2. يبحث في interview questions.
3. يدمج النتائج.
4. يرجع أول `top_k`.

### `_build_jobs(self, reset: bool) -> int`

يبني collection الوظائف.

الخطوات:

1. يقرأ `settings.CLEAN_JOBS_PATH`.
2. لو Chroma غير متاح، يرجع عدد rows فقط.
3. يحصل على collection باسم `jobs`.
4. يمر على كل job.
5. يستبعد masked jobs.
6. يبني document من:
   - title
   - company
   - location
   - description
7. يبني metadata.
8. يضيف البيانات إلى Chroma على batches.
9. يرجع عدد الوظائف التي تمت إضافتها.

### `_build_interview_questions(self, reset: bool) -> int`

يبني collection أسئلة الانترفيو.

الخطوات:

1. يقرأ `settings.INTERVIEW_QUESTIONS_PATH`.
2. لو Chroma غير متاح، يرجع عدد rows.
3. يحصل على collection باسم `interview_questions`.
4. يمر على الأسئلة.
5. يبني ids و documents و metadata.
6. يضيفها إلى Chroma.
7. يرجع عدد الأسئلة.

### `_query_collection(self, name, query, top_k, where=None) -> List[Dict[str, Any]]`

تنفذ query على collection.

الخطوات:

1. تحصل على collection.
2. تبني query kwargs.
3. تضيف `where` لو موجود.
4. تستدعي:

```python
collection.query(...)
```

5. تقرأ documents و metadatas و distances.
6. تحول كل نتيجة إلى dictionary.
7. تضيف:

```python
"_distance_score"
```

8. ترجع النتائج.

### `_fallback_jobs(self, query: str, top_k: int) -> List[Dict[str, Any]]`

بحث بديل بدون Chroma.

الخطوات:

1. يقرأ jobs CSV.
2. يستبعد masked jobs.
3. يبني document لكل job.
4. يحسب `lexical_score`.
5. يرتب النتائج تنازليًا.
6. يرجع أول `top_k`.

### `_get_collection(self, name: str, reset: bool)`

يحضر Chroma collection.

الخطوات:

1. لو Chroma غير متاح، يرمي `RuntimeError`.
2. لو `reset=True` والـ collection موجودة، يحذفها.
3. يرجع:

```python
self.client.get_or_create_collection(...)
```

### `_collection_exists(self, name: str) -> bool`

يتحقق هل collection موجودة.

يحاول:

```python
self.client.get_collection(name)
```

لو نجح يرجع `True`.

لو حدث exception يرجع `False`.

### `_add_in_batches(self, collection, ids, documents, metadatas) -> None`

يضيف records إلى Chroma على batches.

حجم batch:

```python
100
```

لكل batch يستدعي:

```python
collection.add(...)
```

### `_read_csv(self, path: Path) -> List[Dict[str, str]]`

يقرأ CSV file.

لو الملف غير موجود، يرجع list فارغة.

لو موجود، يقرأه بـ:

```python
csv.DictReader
```

باستخدام encoding:

```python
utf-8-sig
```

### `_create_embedding_function(self)`

ينشئ embedding function.

يحاول:

```python
LocalSentenceTransformerEmbeddingFunction(settings.EMBEDDING_MODEL)
```

لو فشل، يرجع:

```python
HashEmbeddingFunction()
```

### `class LocalSentenceTransformerEmbeddingFunction`

Embedding function تعتمد على sentence-transformers.

### `LocalSentenceTransformerEmbeddingFunction.__init__(self, model_name: str)`

تحمل model:

```python
SentenceTransformer(model_name, local_files_only=True)
```

استخدام `local_files_only=True` يعني أنها لن تحمل model من الإنترنت، بل تستخدم الموجود محليًا.

### `LocalSentenceTransformerEmbeddingFunction.__call__(self, input)`

تحول list نصوص إلى embeddings.

تستخدم:

```python
self.model.encode(list(input), normalize_embeddings=True)
```

ثم ترجع `tolist()`.

### `class HashEmbeddingFunction`

Embedding fallback بسيط.

يستخدم hashing بدل model حقيقي.

### `HashEmbeddingFunction.__init__(self, dimensions: int = 384)`

يحفظ عدد أبعاد الـ vector.

الافتراضي:

```python
384
```

### `HashEmbeddingFunction.__call__(self, input)`

يستقبل list من النصوص.

يرجع list من vectors عن طريق:

```python
self._embed(text)
```

### `HashEmbeddingFunction._embed(self, text: str) -> List[float]`

يحول نص واحد إلى vector.

الخطوات:

1. ينشئ vector أصفار بطول `dimensions`.
2. يستخرج tokens من النص.
3. لكل token:
   - يحسب SHA-256.
   - يختار index داخل vector.
   - يحدد sign موجب أو سالب.
   - يضيف القيمة في هذا المكان.
4. يعمل normalization للـ vector.
5. يرجع vector.

### `vector_store = VectorStore()`

Object جاهز للاستخدام.

---

## `core/chat_service/__init__.py`

ملف فارغ تقريبًا. يجعل `chat_service` Python package.

---

## `core/chat_service/gemini_service.py`

هذا الملف مسؤول عن التعامل مع Gemini.

### `class GeminiService`

Service لإرسال prompts إلى Gemini واستقبال الردود.

### `__init__(self)`

تهيئة Gemini.

الخطوات:

1. يضبط:
   - `self.genai = None`
   - `self.model = None`
   - `self.model_name = None`
2. يبني قائمة موديلات مرشحة:

```python
self._model_candidates(settings.GEMINI_MODEL)
```

3. لو `GOOGLE_API_KEY` غير موجود:
   - يحفظ رسالة في `init_error`.
   - يخرج من الدالة.
4. لو المفتاح موجود:
   - يستورد `google.generativeai`.
   - يعمل configure بالـ API key.
   - يجهز أول model.

لو حدث خطأ، يحفظه في `init_error`.

### `available(self) -> bool`

Property ترجع:

```python
self.model is not None
```

يعني هل Gemini جاهز أم لا.

### `suggest_cv_improvements(self, cv_text: str, ats_payload: Dict) -> List[str]`

تولد اقتراحات لتحسين CV.

لو Gemini غير متاح:

```python
self._fallback_suggestions(ats_payload)
```

لو Gemini متاح:

1. تبني prompt يحتوي:
   - system prompt
   - improvement prompt
   - ATS result
   - CV text
2. تستدعي `_generate`.
3. تحول الرد إلى list باستخدام `_lines_to_list`.
4. لو النتيجة فارغة، تستخدم fallback.

### `stream_chat(self, cv_text, user_message, retrieved_context, history=None) -> Iterable[str]`

ترسل رسالة chat إلى Gemini وترجع الرد على أجزاء.

لو Gemini غير متاح:

1. تبني fallback chat.
2. تقسمه إلى chunks باستخدام `_chunk_text`.

لو Gemini متاح:

1. تبني prompt باستخدام `_build_chat_prompt`.
2. تمر على model candidates.
3. لكل model:
   - تستدعي:

```python
model.generate_content(prompt, stream=True)
```

4. ترجع كل chunk نصي.
5. لو model فشل، تجرب model آخر.
6. لو كل الموديلات فشلت، تستخدم fallback chat.

### `_generate(self, prompt: str) -> str`

استدعاء Gemini بدون streaming.

يستخدم غالبًا في suggestions.

الخطوات:

1. لو `genai` غير موجود، يرجع string فارغ.
2. يمر على model candidates.
3. يستدعي:

```python
model.generate_content(prompt)
```

4. يرجع `response.text`.
5. لو كل المحاولات فشلت، يحفظ آخر error ويرجع string فارغ.

### `_build_chat_prompt(self, cv_text, user_message, retrieved_context, history=None) -> str`

يبني prompt النهائي للشات.

يجهز:

1. `context_text` من نتائج البحث.
2. `history_text` من آخر 14 رسالة.
3. نص prompt يحتوي:
   - system prompt
   - conversation memory
   - user CV
   - retrieved local context
   - current user message
   - instructions

### `_chunk_text(self, text: str, size: int = 48) -> Iterable[str]`

تقسم text إلى أجزاء صغيرة بطول `size`.

تستخدم فقط في fallback حتى يبدو الرد streaming.

### `_get_model(self, model_name: str)`

ترجع model من cache.

لو model غير موجود في:

```python
self._models
```

تنشئه:

```python
self.genai.GenerativeModel(model_name)
```

ثم ترجعه.

### `_model_candidates(self, configured_model: str) -> List[str]`

تبني list موديلات للتجربة.

تبدأ بالموديل الموجود في settings، ثم تضيف بدائل:

- `gemini-2.5-flash-lite`
- `gemini-2.5-flash`
- `gemini-flash-latest`

تزيل التكرار وتحافظ على الترتيب.

### `_lines_to_list(self, text: str) -> List[str]`

تحول رد Gemini إلى list.

الخطوات:

1. تقسم النص إلى lines.
2. تزيل bullets أو numbering من البداية.
3. تتجاهل السطور العامة باستخدام `_is_non_action_line`.
4. ترجع list نظيفة.

### `_is_non_action_line(self, line: str) -> bool`

تحدد هل السطر كلام عام يجب تجاهله.

تتجاهل سطور تبدأ بـ:

- here are
- here is
- below are
- certainly
- of course

أو تحتوي نهايات مثل:

- hope this helps
- let me know

### `_fallback_suggestions(self, ats_payload: Dict) -> List[str]`

ترجع اقتراحات ثابتة لو Gemini غير متاح.

لو `ats_payload` يحتوي `missing_skills`، تضيف اقتراح يذكر هذه المهارات.

### `_fallback_chat(self, user_message: str, retrieved_context: List[Dict]) -> str`

ترجع رد fallback لو Gemini غير متاح.

لو يوجد retrieved context، تذكر أقرب context.

لو لا يوجد context، تطلب ضبط `GOOGLE_API_KEY`.

### `gemini_service = GeminiService()`

Object جاهز للاستخدام.

---

## `core/chat_service/streaming_chat_service.py`

هذا الملف مسؤول عن chat streaming.

### Type alias: `DisconnectChecker`

نوع يمثل function اختيارية تتحقق هل client قطع الاتصال.

```python
Optional[Callable[[], Awaitable[bool]]]
```

### `class StreamingChatService`

Service تنفذ flow الشات وترجع SSE events.

### `stream_chat(self, session_id, message="", user_id=None, uploaded_filename=None, uploaded_content=None, is_disconnected=None) -> AsyncGenerator[str, None]`

الدالة الرئيسية للشات.

الخطوات:

1. تهيئ:

```python
final_text = ""
current_message = message.strip()
```

2. تحمل session:

```python
session_store.require(session_id)
```

3. ترسل SSE event:

```json
{"type": "start", "session_id": "..."}
```

4. لو يوجد ملف مرفوع:
   - تستدعي `cv_analysis_service.analyze_and_save`.
   - ترسل event نوعه `analysis` يحتوي:
     - filename
     - summary
     - ats
     - improvement_suggestions

5. لو الرسالة فارغة، تضع رسالة افتراضية.

6. تحمل session مرة أخرى بعد التحليل.

7. تقرأ:
   - `history`
   - `cv_text`

8. تبني query:

لو يوجد CV:

```python
message + "\n\nCV:\n" + cv_text[:5000]
```

لو لا يوجد CV:

```python
message
```

9. تبحث عن context:

```python
vector_store.search_context(query, top_k=6)
```

10. ترسل event نوعه `context` يحتوي sources.

11. تحفظ رسالة المستخدم:

```python
session_store.append_message(session_id, "user", current_message)
```

12. تستدعي Gemini streaming:

```python
gemini_service.stream_chat(...)
```

13. لكل chunk:
   - تتحقق هل client disconnected.
   - تضيف chunk إلى `final_text`.
   - ترسل event نوعه `delta`.

14. بعد نهاية الرد:
   - تحفظ رد assistant في session.

15. ترسل event نوعه `done`.

16. ترسل:

```text
data: [DONE]
```

17. لو حدث exception:
   - تسجل الخطأ بالـ logger.
   - ترسل event نوعه `error`.
   - ترسل `[DONE]`.

### `_client_disconnected(self, is_disconnected: DisconnectChecker) -> bool`

تتحقق هل المستخدم أغلق الاتصال.

لو `is_disconnected` غير موجود، ترجع `False`.

لو موجود:

```python
await is_disconnected()
```

لو حدث خطأ، ترجع `False`.

### `_sse(self, payload: dict) -> str`

تحول dictionary إلى SSE string.

مثال:

```python
self._sse({"type": "start"})
```

يرجع:

```text
data: {"type": "start"}

```

### `_source_payload(self, item: dict) -> dict`

تنظف source result قبل إرساله للواجهة.

ترجع dictionary فيه:

- title
- company
- category
- link
- score

### `streaming_chat_service = StreamingChatService()`

Object جاهز للاستخدام.

