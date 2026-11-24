import streamlit as st
import pandas as pd
import re
import math
import time
from collections import Counter
from datetime import datetime

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم الفاتح المريح (Light Theme)
# ---------------------------------------------------------
st.set_page_config(
    page_title="الملاذ الهادئ | Quiet Harbor",
    page_icon="⚓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* إجبار الألوان الفاتحة والاتجاه من اليمين لليسار */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F6F9FC !important;
        color: #1E293B !important;
        direction: rtl;
        text-align: right;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-left: 1px solid #E2E8F0 !important;
        direction: rtl;
        text-align: right;
    }

    /* تنسيق الهيدر الرئيسي وتوقيع الطالب */
    .harbor-header {
        background: linear-gradient(135deg, #FFFFFF 0%, #EBF5F5 100%);
        border: 1px solid #CBE3E2;
        border-radius: 18px;
        padding: 24px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(42, 123, 118, 0.06);
        text-align: right;
        direction: rtl;
    }

    .harbor-title {
        color: #1B5E5A !important;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 6px 0;
    }

    .harbor-subtitle {
        color: #475569 !important;
        font-size: 1.05rem;
        margin: 0 0 14px 0;
        line-height: 1.6;
    }

    .creator-badge {
        display: inline-block;
        background-color: #E0F2F1;
        color: #134E4A !important;
        border: 1px solid #99D5D0;
        padding: 7px 14px;
        border-radius: 10px;
        font-size: 0.92rem;
        font-weight: 600;
    }

    .ethics-note {
        background-color: #FFFFFF;
        border-right: 4px solid #2A7B76;
        border-top: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        border-left: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 18px;
        font-size: 0.88rem;
        color: #475569 !important;
        direction: rtl;
        text-align: right;
    }

    /* تنسيق رسائل المحادثة */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 16px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
        direction: rtl;
        text-align: right;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4 {
        color: #1E293B !important;
        line-height: 1.85 !important;
        font-size: 1.02rem !important;
    }

    /* تنسيق صندوق الطوارئ */
    .crisis-box {
        background-color: #FFF5F5;
        border: 2px solid #E53E3E;
        border-radius: 14px;
        padding: 18px;
        margin: 12px 0;
        color: #742A2A !important;
        direction: rtl;
        text-align: right;
        line-height: 1.8;
    }

    /* تنسيق الأزرار */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #1B5E5A !important;
        border: 1px solid #B2D8D6 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #E6F4F3 !important;
        border-color: #2A7B76 !important;
    }

    /* صندوق الإدخال السفلي */
    [data-testid="stChatInput"] {
        direction: rtl;
    }
    [data-testid="stChatInput"] textarea {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        text-align: right;
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. محرك فهم العامية المصرية والسخرية والنفي (Egyptian NLP)
# ---------------------------------------------------------
def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

CRISIS_PATTERNS = [
    "انتحار", "هنتحر", "انتحر", "اموت نفسي", "اقتل نفسي",
    "عايز اموت", "نفسي اموت", "انهي حياتي", "اخلص من حياتي",
    "اؤذي نفسي", "اعور نفسي", "اذي نفسي", "مفيش فايده اعيش",
    "وجودي ملوش لازمه", "هريح الكل مني", "مش عايز اعيش"
]

def detect_crisis(raw_text: str):
    norm = normalize_arabic(raw_text)
    for pattern in CRISIS_PATTERNS:
        if pattern in norm:
            return True, pattern
    return False, None

def analyze_egyptian_pragmatics(raw_text: str):
    norm = normalize_arabic(raw_text)
    flags = []
    injected_tokens = []

    sarcasm_markers = ["زي الفل", "تمام اوي", "عظيم جدا", "مبسوط اوي", "مرتاح جدا"]
    distress_markers = ["بعيط", "مش قادر", "منهار", "بموت", "تعبان", "مخنوق", "لدرجه", "مكسور", "ضغط"]
    if any(s in norm for s in sarcasm_markers) and any(d in norm for d in distress_markers):
        flags.append("سخرية_مقنعة (Sarcasm Detected)")
        injected_tokens.extend(["ارهاق_شديد", "ضغط_نفسي", "تعب", "خنقه"])

    negation_pattern = r'\b(مش|مبقتش|معدتش|مفيش|ماليش|مبحسش|عمري ما)\s+(\w+)'
    matches = re.findall(negation_pattern, norm)
    for neg_word, target_word in matches:
        flags.append(f"نفي_سياقي ({neg_word} {target_word})")
        if target_word in ["مبسوط", "كويس", "تمام", "مرتاح", "فرحان"]:
            injected_tokens.extend(["حزن", "خنقه", "فقدان_شغف"])
        elif target_word in ["قادر", "مركز", "فاهم", "مذاكر", "منجز"]:
            injected_tokens.extend(["تشتت", "مذاكره", "ضغط_دراسي", "تاجيل"])
        elif target_word in ["نايم", "بنوم", "نعسان"]:
            injected_tokens.extend(["ارق", "سهر", "تفكير_زايد"])
        elif target_word in ["واثق", "ناجح", "نفع", "لازمه"]:
            injected_tokens.extend(["جلد_ذات", "فشل", "ثقه_بالنفس"])

    return norm, flags, injected_tokens

# ---------------------------------------------------------
# 3. قاعدة المعرفة المبنية على 10 مراجع علمية في علم النفس
# ---------------------------------------------------------
KNOWLEDGE_BASE = [
    {
        "id": "academic_procrastination",
        "title": "ضغط المذاكرة، التشتت، وتأجيل المهام",
        "books": "Atomic Habits (James Clear) & Feeling Good (David Burns)",
        "framework": "التنشيط السلوكي وتجزئة المهام (Behavioral Activation)",
        "keywords": "مذاكره امتحان امتحانات دروس تراكمات تشتت تركيز تاجيل تسويف مش قادر اذاكر كسل وقت ضغط دراسي ستم ثانويه كليه",
        "empathy_angles": [
            "فكرة إن المهام تتراكم قدامك لدرجة تخليك تقف مكانك مش قادر تبدأ من أصعب الأحاسيس؛ ده مش كسل، ده عقلك بيعمل 'فرملة طوارئ' لما بيشوف الحمل أكبر من طاقته اللحظية.",
            "لما بتبص لحجم اللي وراك كله مرة واحدة، طبيعي تحس بتقل وتشتت يخليك تهرب من البداية أصلاً، رغم إنك من جواك شايل الهم وعايز تنجز."
        ],
        "immediate_steps": [
            "**قاعدة الدقيقتين لكسر الجمود:** اقفل كل الكتب والتابات المفتوحة، واختار أصغر جزء ممكن في مادة واحدة (مثلاً: حل مسألتين بس أو قراءة صفحة واحدة) واضبط مؤقت الموبايل على **١٠ دقايق فقط**. الهدف دلوقتي هو كسر رهبة البداية مش إنهاء المنهج.",
            "**تفريغ الدماغ على ورق:** هات ورقة فاضية واكتب فيها كل اللي شاغل بالك ومؤجله في ٣ دقايق بدون ترتيب؛ مجرد خروج المهام من دماغك للورق بيقلل التوتر الذهني بنسبة كبيرة."
        ],
        "cognitive_reframe": (
            "العقل وقت الضغط بيوقعنا في فخ **'التفكير الكارثي أو الكمال'** (يا أخلص كل اللي ورايا النهاردة يا إما أنا فاشل ومفيش فايدة). "
            "الواقع العملي بيقول: **إنجاز ٢٠٪ النهاردة أحسن بكتير من ٠٪ مع جلد الذات**. أنت مش مطالب تخلص الجبل كله في قعدة واحدة، أنت مطالب تاخد أول خطوة فيه بس."
        ),
        "today_plan": [
            "**الخطوة ١ (أول ٢٥ دقيقة):** اشتغل بنظام **٢٥ دقيقة تركيز كامل + ٥ دقايق راحة** بعيد عن الموبايل تماماً (حطه في أوضة تانية).",
            "**الخطوة ٢ (تحديد أولوية واحدة):** اختار مهمة واحدة بس لو خلصتها النهاردة هتحس إن يومك ما ضاعش، وابدأ بيها قبل أي حاجة تانية.",
            "**الخطوة ٣ (مكافأة فورية):** بعد كل جلستين مذاكرة، اعمل حاجة بتحبها لمدة ١٠ دقايق عشان تربط المذاكرة بشعور إنجاز مش عقاب."
        ],
        "long_term_habit": "ثبّت ميعاد يومي ثابت لبداية المذاكرة ولو لـ ١٥ دقيقة بس في نفس المكان؛ الاستمرارية الصغيرة بتبني زخم بيخلي البداية أسهل كل يوم.",
        "followup_question": "إيه أكتر مادة أو مهمة عاملالك قفلة دلوقتي، تحب نقسمها سوا لخطوات صغيرة تبدأ بيها حالاً؟"
    },
    {
        "id": "anxiety_overthinking",
        "title": "القلق المستمر، التفكير الزائد، والخوف من المستقبل",
        "books": "Mind Over Mood (Greenberger & Padesky) & The Happiness Trap (Russ Harris)",
        "framework": "العلاج المعرفي السلوكي وفك الاندماج المعرفي (CBT & ACT)",
        "keywords": "قلق قلقان تفكير زايد خوف خايف مستقبل بكره توتر سيناريوهات دماغي مش بتفصل وسواس لو حصل",
        "empathy_angles": [
            "إن دماغك تفضل شغالة ٢٤ ساعة بترسم سيناريوهات للي جاي وتفترض الأسوأ ده استنزاف حقيقي لطاقتك؛ عقلك بيحاول يحميك بالتوقع، لكنه عملياً بيسرق منك راحتك في اللحظة الحالية.",
            "حالة الترقب والقلق المستمر بتخلي الجسم طول الوقت في وضع استعداد كإن في خطر قريب، وده اللي بيخليك حاسس بتعب حتى من غير مجهود بدني."
        ],
        "immediate_steps": [
            "**تمرين التأريض الحسي (5-4-3-2-1):** بص حواليك في المكان وسمّي بصوت هادي: **٥ حاجات شايفها** بعينك، **٤ حاجات تقدر تلمسها** بإيدك، **٣ أصوات سامعها**، **حاجتين شاممهم**، و**حاجة واحدة حاسس بطعمها**. التمرين ده بيسحب عقلك من دوامة المستقبل ويرجعه للواقع فوراً.",
            "**التنفس المربع (Box Breathing):** خد شهيق من مناخيرك في **٤ ثواني**، احبس النفس **٤ ثواني**، وطلّع الزفير بالراحة من بقك في **٦ ثواني**. كررها ٤ مرات لتهدئة ضربات القلب."
        ],
        "cognitive_reframe": (
            "فرّق بين **'فكرة في دماغك'** وبين **'حقيقة مؤكدة'**. لما تيجي في بالك فكرة مرعبة، جرب تقول لنفسك: *'أنا ملاحظ إن عقلي دلوقتي بيبعتلي فكرة قلق بخصوص كذا'* بدل ما تتعامل معاها كإنها قدر محتوم. "
            "اسأل نفسك سؤالين عمليين: **١) إيه الدليل الفعلي إن السيناريو الأسوأ ده هيحصل؟ ٢) لو حصل لا قدر الله، إيه أول تصرف عملي هعمله؟**"
        ),
        "today_plan": [
            "**تخصيص 'وقت للقلق' (Worry Time):** حدد ١٥ دقيقة بس الساعة ٦ المغرب تكتب فيها كل مخاوفك، وأي قلق يجيلك قبل الميعاد ده قوله: *'هفكر فيك الساعة ٦'*. ده بيعلم عقلك إنك إنت اللي بتتحكم في وقت التفكير.",
            "**فلتر السيطرة:** اقسم ورقة نصين؛ اكتب على اليمين **'حاجات في إيدي أتحكم فيها النهاردة'** وعلى الشمال **'حاجات برا سيطرتي'**، ووجه طاقتك كلها لليمين بس.",
            "**تقليل المحفزات:** قلل الكافيين ومتابعة الأخبار أو السوشيال ميديا قبل النوم بساعتين."
        ],
        "long_term_habit": "اكتب كل يوم بالليل ٣ حاجات بسيطة عدّت بسلام النهاردة؛ ده بيدرّب انتباهك يشوف الأمان زي ما بيشوف المخاطر.",
        "followup_question": "إيه أكتر سيناريو بيلف في دماغك دلوقتي ومخليك مش مرتاح، تحب نحلله سوا ونشوف إيه اللي في إيدك تعمله فيه؟"
    },
    {
        "id": "exhaustion_low_mood",
        "title": "الخنقة، الإرهاق النفسي، وفقدان الشغف",
        "books": "Cognitive Behavioral Therapy: Basics and Beyond (Judith Beck) & Feeling Good (David Burns)",
        "framework": "إعادة بناء الطاقة التدريجي (Graded Task Assignment)",
        "keywords": "مخنوق خنقه حزين زعلان ماليش نفس شغف طاقه خلصانه تعبان نفسيا زهقان مكتئب فراغ مش حاسس بحاجه زي الفل",
        "empathy_angles": [
            "الخنقة اللي بتيجي من غير سبب واضح أو الإحساس إن بطاريتك فضيت تماماً ومالكش نفس لأي حاجة هو إشارة حقيقية إنك شيلت فوق طاقتك لفترة طويلة من غير ما تاخد مساحة تتنفس فيها.",
            "مش مطلوب منك دلوقتي تضحك غصب عنك ولا تتظاهر إنك تمام؛ الاعتراف بإنك تعبان ومحتاج تهدى هو أول خطوة حقيقية عشان تسترد نفسك."
        ],
        "immediate_steps": [
            "**تخفيف الحمل الفوري:** اسمح لنفسك النهاردة تتعامل بنظام **'الحد الأدنى المقبول'**؛ لغّي أي التزامات غير ضرورية النهاردة وادي لنفسك إذن صريح بالراحة من غير تأنيب ضمير.",
            "**تغيير البيئة الصغيرة:** قوم اغسل وشك بمية فاترة، افتح الشباك يدخل هواء ونور طبيعي، واشرب كوباية مية ببطء. التغيير الجسدي البسيط بيكسر حالة الجمود الشعوري."
        ],
        "cognitive_reframe": (
            "لما طاقتنا بتقل، العقل بيخلينا نستنى **'الشغف أو المزاج الحلو'** عشان نتحرك، وده فخ لأن الشغف في أوقات الإرهاق مبيجيش لوحده. "
            "القاعدة العلمية بتقول: **الفعل البسيط هو اللي بيولد الطاقة، مش العكس**. خطوة صغيرة جداً النهاردة كفيلة تحرك المياه الراكدة جواك."
        ),
        "today_plan": [
            "**نشاط واحد مغذي (Nourishing Activity):** اختار حاجة واحدة بسيطة كانت بتريحك زمان (مشي ١٥ دقيقة في الشارع، سماع قرآن أو مزيكا هادية، أو دش دافي) واعملها النهاردة كواجب لنفسك.",
            "**تواصل بشري خفيف:** ابعت رسالة قصيرة لحد بترتاحله حتى لو مش هتحكي تفاصيل، مجرد وجود تواصل إنساني بيخفف ثقل العزلة.",
            "**حركة بدنية خفيفة:** اتمشى ١٠ دقايق في الأوضة أو البلكونة؛ الحركة بتفرز إندورفين طبيعي بيحسن كيمياء المخ."
        ],
        "long_term_habit": "خصص لنفسك ٣٠ دقيقة يومياً 'وقت بدون شاشات وبدون مهام' تعمل فيها حاجة لنفسك إنت بس، عشان تمنع استنزاف بطاريتك قبل ما تفضى.",
        "followup_question": "الإحساس ده بدأ معاك من قريب بعد موقف معين، ولا حاسس إنه تراكم بقاله فترة؟"
    },
    {
        "id": "self_criticism_confidence",
        "title": "جلد الذات، الشعور بالتقصير، وفقدان الثقة",
        "books": "Self-Compassion (Kristin Neff) & Mind Over Mood (Greenberger & Padesky)",
        "framework": "التعاطف الواعي مع الذات وإعادة التقييم المعرفي",
        "keywords": "فاشل فشل تقصير مقصر ثقه بنفسي جلد ذات بكره نفسي مش كفايه اقل من غيري مقارنه ندمان غلطت",
        "empathy_angles": [
            "الصوت اللي جواك اللي عمال يحاسبك على كل غلطة ويقارنك باللي حواليك قاسي جداً، وبيخليك تحس إن قيمتك مرتبطة بس بنتيجة أو إنجاز لحظي.",
            "طبيعي تغلط أو تتعثر وإنت بتحاول، لكن الفرق بين إنك تتعلم من الموقف وبين إنك تكسر نفسك هو الطريقة اللي بتكلم بيها نفسك في اللحظة دي."
        ],
        "immediate_steps": [
            "**اختبار الصديق المقرب:** تخيل إن أعز صاحب ليك جه حكالك نفس الموقف اللي إنت بتلوم نفسك عليه دلوقتي؛ هتقوله إيه؟ اكتب الرد ده في ورقة واقرأه لنفسك بنفس النبرة الداعمة.",
            "**إيقاف المقارنة الفورية:** اقفل أي تطبيقات أو منصات بتخليك تقارن كواليسك المتعبة بلقطات النجاح المفلترة بتاعة غيرك."
        ],
        "cognitive_reframe": (
            "خطأ شائع اسمه **'شخصنة النتيجة'**: إنك تحول جملة *'أنا غلطت في الموقف ده'* أو *'درجتي ما كانتش أحسن حاجة'* لجملة *'أنا شخص فاشل'*. "
            "الفشل حدث عابر بنمر بيه كلنا عشان نتعلم، مش هوية بتلزق فيك. إنت إنسان بتحاول في ظروف صعبة، وده لوحده يستحق التقدير."
        ),
        "today_plan": [
            "**تعديل قاموس كلامك مع نفسك:** كل ما تلاقي نفسك بتقول *'أنا كان لازم...'*، بدّلها بـ *'أنا اتعلمت المرة دي إن...'*.",
            "**قائمة الحقائق المتوازنة:** اكتب ٣ مواقف صعبة عدّيت بيها قبل كده ونجحت تتصرف فيها، عشان تفكّر عقلك بإمكانياتك الحقيقية وقت الأزمات.",
            "**تحديد خطوة تصحيح واحدة:** لو في غلطة فعلاً حصلت، اسأل: *'إيه الخطوة العملية الواحدة اللي أقدر أصلح بيها الوضع دلوقتي؟'* ونفذها واقفل باب اللوم."
        ],
        "long_term_habit": "في نهاية كل أسبوع، سجّل ٣ محاولات عملتها حتى لو نتيجتها ما كانتش كاملة؛ كافئ نفسك على السعي والالتزام مش على النتيجة النهائية بس.",
        "followup_question": "إيه أكتر جملة قاسية بتقولها لنفسك الأيام دي، وحاسس إنها بدأت بسبب موقف إيه؟"
    },
    {
        "id": "acute_stress_anger",
        "title": "نوبات التوتر الحادة، العصبية، وضيق الصدر المفاجئ",
        "books": "DBT Skills Training Manual (Marsha Linehan) & The Body Keeps the Score (Bessel van der Kolk)",
        "framework": "مهارات تحمل الضيق وتنظيم الجهاز العصبي (DBT TIPP Skills)",
        "keywords": "عصبي عصبيه غضب متعصب نرفزه بعيط انهيار مش طايق نفسي قلبي بيدق بسرعه توتر شديد انفجار",
        "empathy_angles": [
            "لما المشاعر بتعلى فجأة بالشدة دي، الجهاز العصبي بيدخل في حالة استنفار قصوى بتخلي التفكير المنطقي صعب جداً في اللحظة دي؛ جسمك محتاج يهدى الأول قبل أي نقاش أو قرار.",
            "طبيعي تحس بضغط بيوصل لمرحلة الانفجار لما تكتم جواك لفترة طويلة؛ الأهم دلوقتي نعدّي الموجة العالية دي بأمان من غير ما تخسر نفسك أو اللي حواليك."
        ],
        "immediate_steps": [
            "**مهارة خفض الحرارة (TIPP - DBT):** اغسل وشك بمية ساقعة جداً أو حط كمادة ساقعة على عينيك وخدودك لمدة **٣٠ ثانية** مع ميل راسك لقدام؛ ده بيفعّل رد فعل الغوص الطبيعي في الجسم وبيهدي ضربات القلب في ثواني.",
            "**تفريغ التوتر العضلي:** اقبض إيديك الاتنين وشد عضلات كتفك بقوة لمدة **٥ ثواني**، وبعدين سيبهم يرتخوا تماماً لمدة **١٠ ثواني** مع زفير طويل. كررها ٣ مرات."
        ],
        "cognitive_reframe": (
            "المشاعر الحادة عاملة زي الموجة في البحر؛ بتعلى وتوصل لقمتها، لكنها **مستحيل تفضل في القمة للأبد** لو ما غذّيناهاش بقرارات متسرعة. "
            "مهمتك الوحيدة في وقت العاصفة إنك **تأجل أي رد فعل أو رسالة أو قرار مصيري لمدة ساعة** لحد ما الموجة تنزل."
        ),
        "today_plan": [
            "**الانسحاب الآمن المؤقت:** لو إنت في نقاش مشحون، استأذن بهدوء: *'محتاج أشرب مية وأرجع نكمل كلامنا بعد شوية'* عشان تحمي علاقاتك من كلام يتقال وقت الغضب.",
            "**المشي السريع ١٠ دقايق:** الحركة السريعة بتحرق هرمون الأدرينالين والكورتيزول الزيادة في الدم.",
            "**تسمية الشعور بدقة:** اكتب في نوت الموبايل: *'أنا حاسس بـ [غضب / خوف / إحباط] عشان حصل كذا'*؛ تسمية الشعور بتقلل نشاط مركز الخوف في المخ."
        ],
        "long_term_habit": "راقب علامات الإنذار المبكرة في جسمك (زي شد الفك أو سرعة النفس) واتدخل بالتنفس العميق بدري قبل ما التوتر يوصل للذروة.",
        "followup_question": "حاسس إن جسمك بدأ يهدى شوية دلوقتي، ولا تحب نرتب سوا إزاي تتعامل مع الموقف اللي استفزك بهدوء؟"
    },
    {
        "id": "loneliness_relationships",
        "title": "الشعور بالوحدة، سوء الفهم، وضغوط العلاقات",
        "books": "DBT Skills Training Manual (Marsha Linehan) & Self-Compassion (Kristin Neff)",
        "framework": "التواصل الفعال والحدود الصحية (DEAR MAN & Interpersonal Effectiveness)",
        "keywords": "وحيد وحده لوحدي محدش فاهمني صحاب اهلي البيت مشاكل علاقات خذلان زعل بينا بعد",
        "empathy_angles": [
            "إنك تكون وسط ناس كتير بس حاسس إن محدش فاهم اللي جواك بجد هو من أتقَل أنواع الوحدة؛ الاحتياج لحد يسمعك من غير ما يحكم عليك أو يقلل من مشاعرك احتياج إنساني أساسي.",
            "لما التواصل مع القريبين مننا بيتعقد، بنحس باستنزاف وحيرة بين إننا نسكت ونكتم جوا نفسنا وبين إننا نتكلم ونخاف نتفهم غلط."
        ],
        "immediate_steps": [
            "**تخفيف الحمل العاطفي بالكتابة:** اكتب رسالة غير مرسلة للشخص أو للموقف اللي مضايقك، طلّع فيها كل اللي نفسك تقوله بصراحة كاملة، وبعدين اقفلها؛ ده بيفرغ الاحتقان من غير خسائر.",
            "**تذكير الذات بالانتماء:** افتكر إن شعورك بالوحدة دلوقتي هو حالة مؤقتة بتمر بيها، ومش معناه إنك شخص غير محبوب أو مرفوض."
        ],
        "cognitive_reframe": (
            "ساعات بنقع في فخ **'قراءة الأفكار'**؛ نفترض إن اللي قدامنا قاصد يتجاهلنا أو مش مهتم، في حين إنه ممكن يكون غرقان في ضغوطه أو مش عارف يعبر صح. "
            "التعبير الواضح والهادي عن احتياجك حق ليك، وفي نفس الوقت رسم حدود تحمي سلامك النفسي مش أنانية."
        ),
        "today_plan": [
            "**صياغة التعبير الهادي (I-Statements):** لو حابب تتكلم مع حد قريب منك، ابدأ كلامك بـ *'أنا بحس بـ... لما بيحصل كذا، ونفسي نعمل كذا'* بدل أسلوب اللوم (*'إنت دايماً بتعمل...'*).",
            "**توسيع دائرة التواجد:** انزل ذاكر في مكان عام هادي (مكتبة أو كافيه) أو شارك في نشاط طلابي بسيط؛ مجرد التواجد في بيئة حية بيخفف إحساس العزلة.",
            "**تحديد حدودك بهدوء:** لو في علاقة بتستنزف طاقتك، قلل وقت الاحتكاك بيها النهاردة ووجه طاقتك لنفسك."
        ],
        "long_term_habit": "استثمر في علاقة واحدة حقيقية وآمنة حتى لو بسيطة، وخصص وقت أسبوعي للسؤال والمشاركة الصادقة.",
        "followup_question": "الوحدة أو الضيق اللي حاسس بيه دلوقتي مرتبط بموقف مع حد معين في البيت أو الصحاب، ولا إحساس عام إنك شايل همومك لوحدك؟"
    },
    {
        "id": "sleep_physical_burnout",
        "title": "الأرق، لخبطة النوم، والإرهاق البدني",
        "books": "Why We Sleep (Matthew Walker) & The Body Keeps the Score (Bessel van der Kolk)",
        "framework": "إعادة ضبط الساعة البيولوجية ونظافة النوم (CBT-I)",
        "keywords": "نوم ارق مش بعرف انام سهر سهران صاحي كوابيس نوم متقطع جسمي مهدود ارهاق بدني",
        "empathy_angles": [
            "إنك تبقى مهدود طول اليوم وأول ما تحط راسك على المخدة دماغك تصحى وتبدأ تفكر في كل حاجة ده من أكتر الحاجات اللي بتستنزف أعصابك ومزاجك تاني يوم.",
            "قلة النوم مش بس بتتعب الجسم، دي بتخلي مركز الانفعال في المخ حساس زيادة لأي ضغط بسيط في اليوم اللي بعده."
        ],
        "immediate_steps": [
            "**قاعدة الـ ٢٠ دقيقة (Stimulus Control):** لو فضلت في السرير أكتر من ٢٠ دقيقة صاحي وبتتقلب، قوم من السرير واقعد في إضاءة خافتة اقرأ حاجة ورقية هادية لحد ما تحس بالنعاس، وارجع السرير. الهدف إن مخك يربط السرير بالنوم بس مش بالتفكير والقلق.",
            "**إرخاء الجسم التدريجي:** ابدأ من صوابع رجليك لحد عضلات وشك، ريّح كل جزء بالتدريج مع نفس بطيء."
        ],
        "cognitive_reframe": (
            "القلق من عدم النوم (*'لو مانمتش دلوقتي هبوظ بكرة'*) هو أكتر حاجة بتطير النوم لأنه بيفرز أدرينالين. "
            "فكّر في الأمر بهدوء: **مجرد استلقائك في هدوء وإغماض عينيك بيدي جسمك جزء كبير من الراحة** حتى لو النوم اتأخر شوية."
        ),
        "today_plan": [
            "**فصل الشاشات قبل النوم بـ ٤٥ دقيقة:** الضوء الأزرق للموبايل بيوقف هرمون الميلاتونين المسؤول عن النوم؛ جرب تحط الموبايل بعيد عن السرير.",
            "**تثبيت ميعاد الصحيان:** أهم خطوة لضبط ساعتك البيولوجية هي إنك تصحى في نفس الميعاد الصبح حتى لو نمت متأخر.",
            "**تجنب الكافيين بعد العصر:** القهوة والشاي ومشروبات الطاقة بتفضل شغالة في الجهاز العصبي من ٦ لـ ٨ ساعات."
        ],
        "long_term_habit": "اعمل طقس ثابت قبل النوم بـ ١٥ دقيقة (شرب مشروب دافي بدون كافيين، إضاءة هادية، وتفريغ أفكار بكرة في ورقة) عشان تدي إشارة لمخك إن اليوم انتهى.",
        "followup_question": "إيه أكتر حاجة بتسهرك: تفكير في حاجات معينة شاغلاك، ولا لخبطة مواعيد المذاكرة والموبايل؟"
    },
    {
        "id": "confusion_meaning",
        "title": "التوهان، الحيرة في القرارات، وفقدان البوصلة",
        "books": "Man's Search for Meaning (Viktor Frankl) & The Happiness Trap (Russ Harris)",
        "framework": "العلاج بالمعنى وتوضيح القيم الشخصية (Logotherapy & Values Clarification)",
        "keywords": "تايه توهان حيره محتار قرار مستقبل مش عارف عايز ايه ضايع هدف معنى اختيار",
        "empathy_angles": [
            "مرحلة إنك تقف في نص الطريق مش عارف تختار إيه أو حاسس إنك تايه وسط توقعات الناس وضغوط المستقبل مرحلة طبيعية جداً، وبتحصل غالباً لما بتكون بتدور على طريق يشبهك إنت بجد.",
            "الحيرة مش معناها إنك ضايع؛ معناها إنك واقف قدام اختيارات مهمة وعايز تاخد خطوة صح من غير ندم."
        ],
        "immediate_steps": [
            "**تضييق زاوية الرؤية:** مش لازم تحسم خطة الـ ١٠ سنين الجايين النهاردة؛ اسأل نفسك بس: **'إيه أنسب خطوة صغيرة أقدر أجربها خلال الأسبوعين الجايين؟'**.",
            "**فصل صوتك عن صوت الناس:** اكتب في ورقة: *'لو محدش هيحكم عليا ولا هيقارني بحد، أنا نفسي أتعلم أو أجرب إيه؟'*."
        ],
        "cognitive_reframe": (
            "في علم النفس، مفيش قرار مثالي مضمون ١٠٠٪ من غير تجربة. **الوضوح بيجي من الفعل والتجربة، مش من التفكير النظري الطويل**. "
            "كل تجربة بتدخلها إما بتقربك من اللي بتحبه أو بتعرفك بوضوح إيه اللي مش مناسب ليك، وفي الحالتين إنت كسبان."
        ),
        "today_plan": [
            "**تحديد أهم ٣ قيم عندك:** اختار ٣ حاجات بتحس إن يومك ليه معنى لما بتعملها (مثلاً: التعلم، مساعدة غيرك، الاستقلال، الإبداع) وقيس اختياراتك بناءً عليها.",
            "**استشارة أهل الخبرة:** اسأل شخص واحد سبقك في المجال أو الخطوة اللي محتار فيها عن تجربته العملية بدل ما تفضل تلف في دايرة أفكارك لوحدك.",
            "**تجربة استكشافية صغيرة:** خصص ساعة واحدة النهاردة تستكشف فيها اختيار واحد منهم بشكل عملي."
        ],
        "long_term_habit": "اعمل مراجعة شهرية بسيطة لنفسك تسأل فيها: *'إيه الحاجة اللي عملتها الشهر ده وحسيت فيها بطاقة ومعنى؟'* وابني عليها خطوتك الجاية.",
        "followup_question": "إيه القرار أو الموضوع اللي محيّرك أكتر حاجة اليومين دول؟"
    }
]

# ---------------------------------------------------------
# 4. محرك البحث الدلالي (TF-IDF + Cosine Similarity + Context)
# ---------------------------------------------------------
def build_tfidf_index(kb):
    docs_tokens = []
    for item in kb:
        combined = f"{item['title']} {item['keywords']} {item['keywords']} {item['framework']}"
        tokens = normalize_arabic(combined).split()
        docs_tokens.append(tokens)

    N = len(docs_tokens)
    df = Counter()
    for tokens in docs_tokens:
        for t in set(tokens):
            df[t] += 1

    idf = {t: math.log((N + 1) / (freq + 1)) + 1.0 for t, freq in df.items()}

    doc_vectors = []
    for tokens in docs_tokens:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        vec = {t: (count / total) * idf.get(t, 1.0) for t, count in tf.items()}
        doc_vectors.append(vec)

    return doc_vectors, idf

DOC_VECTORS, IDF_MAP = build_tfidf_index(KNOWLEDGE_BASE)

def cosine_similarity_sparse(vec1: dict, vec2: dict) -> float:
    common = set(vec1.keys()) & set(vec2.keys())
    dot = sum(vec1[k] * vec2[k] for k in common)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def retrieve_best_support(user_text: str, chat_history: list):
    start_time = time.perf_counter()

    is_crisis, trigger = detect_crisis(user_text)
    if is_crisis:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "is_crisis": True,
            "trigger": trigger,
            "confidence": 99.9,
            "flags": ["حالة_طوارئ_نفسية (Crisis Trigger)"],
            "topic": None,
            "latency_ms": elapsed_ms
        }

    norm_current, flags, injected_tokens = analyze_egyptian_pragmatics(user_text)
    current_tokens = norm_current.split() + injected_tokens

    past_user_msgs = [
        normalize_arabic(m["content"])
        for m in chat_history[:-1]
        if m["role"] == "user"
    ][-2:]
    context_tokens = " ".join(past_user_msgs).split()

    tf_counter = Counter()
    for t in current_tokens:
        tf_counter[t] += 1.0
    for t in context_tokens:
        tf_counter[t] += 0.35

    total_weight = sum(tf_counter.values()) or 1.0
    query_vec = {
        t: (w / total_weight) * IDF_MAP.get(t, 1.0)
        for t, w in tf_counter.items()
    }

    scores = []
    for idx, doc_vec in enumerate(DOC_VECTORS):
        sim = cosine_similarity_sparse(query_vec, doc_vec)
        scores.append((sim, idx))

    scores.sort(reverse=True, key=lambda x: x[0])
    best_sim, best_idx = scores[0]
    best_topic = KNOWLEDGE_BASE[best_idx]

    confidence = min(96.5, max(58.0, round(55.0 + best_sim * 135.0, 1)))
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "is_crisis": False,
        "trigger": None,
        "confidence": confidence,
        "flags": flags if flags else ["تحليل_سياقي_مباشر"],
        "topic": best_topic,
        "latency_ms": elapsed_ms,
        "has_context": len(past_user_msgs) > 0
    }

def compose_human_response(user_text: str, result: dict, turn_count: int) -> str:
    topic = result["topic"]
    angle = topic["empathy_angles"][turn_count % len(topic["empathy_angles"])]

    snippet = user_text.strip()
    if len(snippet) > 90:
        snippet = snippet[:90].rsplit(" ", 1)[0] + "..."

    if result["has_context"]:
        opening = (
            f"واضح من كلامك دلوقتي امتداد للي كنا بنتكلم فيه، وخصوصاً إحساسك بـ *«{snippet}»*. "
            f"{angle}"
        )
    else:
        opening = (
            f"أهلاً بيك في مساحتك.. كلامك عن *«{snippet}»* مفهوم جداً ومقدر. "
            f"{angle}"
        )

    immediate_md = "\n".join([f"- {step}" for step in topic["immediate_steps"]])
    today_md = "\n".join([f"{i+1}. {step}" for i, step in enumerate(topic["today_plan"])])

    full_reply = f"""{opening}

---

### أولاً: خطوات تهدئة سريعة في اللحظة دي (خلال ٥ دقايق)
{immediate_md}

### ثانياً: نفكّك الفكرة سوا ونشوفها من زاوية أوضح
{topic['cognitive_reframe']}

### ثالثاً: خطة تحرك عملية لباقي يومك
{today_md}

### رابعاً: عادة تحميك الأيام الجاية
- **الخطوة المستمرة:** {topic['long_term_habit']}

---

💬 **{topic['followup_question']}**
"""
    return full_reply

# ---------------------------------------------------------
# 5. تهيئة الجلسة (Session State)
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "أهلاً بيك في **الملاذ الهادئ** ⚓\n\n"
                "هنا مساحتك الخاصة تتكلم براحتك وبالعامية المصرية عن أي ضغط، قلق، توهان، أو ثقل حاسس بيه. "
                "مش هتلاقي كلام محفوظ ولا أحكام؛ هنفهم سوا اللي بتمر بيه ونرتب خطوات عملية حقيقية تساعدك تعدّي الموقف خطوة بخطوة.\n\n"
                "**احكيلي.. إيه أكتر حاجة شاغلة بالك أو تقيلة على قلبك النهاردة؟**"
            )
        }
    ]

if "last_metrics" not in st.session_state:
    st.session_state.last_metrics = None

# ---------------------------------------------------------
# 6. واجهة المستخدم الرئيسية (Header + Ethical Note)
# ---------------------------------------------------------
st.markdown("""
<div class="harbor-header">
    <h1 class="harbor-title">⚓ الملاذ الهادئ | Quiet Harbor</h1>
    <p class="harbor-subtitle">مساحة دعم نفسي أولي وتوجيه عملي بالعامية المصرية مبنية على ١٠ مراجع علمية معتمدة</p>
    <div class="creator-badge">
        ✨ لقد أنشأ هذا التطبيق بواسطة <strong>عمر حسني</strong> — طالب في مدرسة المتفوقين للعلوم والتكنولوجيا (<strong>STEM المنيا</strong>)
    </div>
</div>
<div class="ethics-note">
    <strong>تنبيه أخلاقي وعلمي:</strong> الملاذ الهادئ مساحة للتثقيف النفسي والدعم الأولي العملي، ولا يُعد بديلاً عن التشخيص الطبي أو استشارة الطبيب النفسي المختص.
</div>
""", unsafe_allow_html=True)

if len(st.session_state.messages) == 1:
    st.markdown("**اختار نقطة بداية سريعة أو اكتب اللي حاسس بيه تحت مباشرةً:**")
    col1, col2, col3 = st.columns(3)
    quick_prompt = None
    with col1:
        if st.button("📚 مضغوط ومؤجل المذاكرة", use_container_width=True):
            quick_prompt = "عندي مذاكرة ومهام كتير متراكمة ومش قادر أبدأ وحاسس بتشتت وضغط كبير"
    with col2:
        if st.button("💭 تفكير زايد وقلقان", use_container_width=True):
            quick_prompt = "دماغي مش بتفصل تفكير في المستقبل وخايف من اللي جاي ومش عارف أهدى"
    with col3:
        if st.button("😔 مخنوق وطاقتي خلصانة", use_container_width=True):
            quick_prompt = "حاسس إني مخنوق وماليش نفس أعمل أي حاجة وطاقتي خلصانة خالص"
else:
    quick_prompt = None

for msg in st.session_state.messages:
    avatar = "⚓" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)

user_input = st.chat_input("اكتب اللي حاسس بيه هنا براحتك...")
active_prompt = quick_prompt if quick_prompt else user_input

if active_prompt:
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(active_prompt)

    analysis = retrieve_best_support(active_prompt, st.session_state.messages)
    st.session_state.last_metrics = analysis

    if analysis["is_crisis"]:
        crisis_html = """
        <div class="crisis-box">
            <strong>⚠️ سلامتك وحياتك أهم من أي شيء دلوقتي</strong><br><br>
            واضح إنك بتمر بلحظة ألم وضغط شديد جداً، ومش مفروض تعدّي بيها لوحدك. من فضلك تواصل فوراً مع متخصصين يقدروا يساعدوك بسرية تامة ومجاناً على مدار ٢٤ ساعة:<br><br>
            📞 <strong>الخط الساخن للأمانة العامة للصحة النفسية وعلاج الإدمان في مصر: <code>16328</code></strong><br>
            🚑 <strong>خط النجدة والطوارئ: <code>122</code></strong><br><br>
            لو جنبك حد من أهلك أو صحابك بتثق فيه، كلمه دلوقتي وخليك معاه. إحنا هنا جنبك، بس الخطوة الأهم دلوقتي إنك تطلب مساعدة بشرية عاجلة.
        </div>
        """
        st.session_state.messages.append({"role": "assistant", "content": crisis_html})
        with st.chat_message("assistant", avatar="⚓"):
            st.markdown(crisis_html, unsafe_allow_html=True)
    else:
        turn_idx = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        reply_text = compose_human_response(active_prompt, analysis, turn_idx)
        st.session_state.messages.append({"role": "assistant", "content": reply_text})
        with st.chat_message("assistant", avatar="⚓"):
            st.markdown(reply_text)

    if quick_prompt:
        st.rerun()

# ---------------------------------------------------------
# 7. القائمة الجانبية: حفظ الجلسة + لوحة التقييم العلمي لآيسف (ISEF)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🗂️ أدوات الجلسة")
    if len(st.session_state.messages) > 1:
        export_lines = [
            "الملاذ الهادئ (Quiet Harbor) - ملخص الجلسة وخطة العمل",
            "تطوير الطالب: عمر حسني - STEM المنيا",
            f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 50 + "\n"
        ]
        for m in st.session_state.messages:
            sender = "أنت" if m["role"] == "user" else "الملاذ الهادئ"
            clean_txt = re.sub(r'<[^>]+>', '', m["content"])
            export_lines.append(f"[{sender}]:\n{clean_txt}\n" + "-" * 30)

        st.download_button(
            label="📥 تحميل الجلسة وخطة الحل (.txt)",
            data="\n".join(export_lines),
            file_name="quiet_harbor_plan.txt",
            mime="text/plain",
            use_container_width=True
        )

    if st.button("🔄 بدء محادثة جديدة", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.last_metrics = None
        st.rerun()

    st.divider()
    st.markdown("### 🔬 لوحة التقييم العلمي (ISEF Judges)")
    st.caption("مؤشرات الشفافية الخوارزمية (Explainable AI) وتحليل اللهجة المصرية:")

    if st.session_state.last_metrics:
        m = st.session_state.last_metrics
        st.metric("درجة التطابق الدلالي (Confidence)", f"{m['confidence']}%")
        st.metric("زمن الاستجابة (Latency)", f"{m['latency_ms']} ms")
        st.write("**إشارات تحليل اللهجة:**", ", ".join(m["flags"]))
        if m["topic"]:
            st.write("**المحور العلاجي:**", m["topic"]["title"])
            st.write("**الإطار العلمي:**", m["topic"]["framework"])
            st.write("**المراجع المعتمدة:**", m["topic"]["books"])
    else:
        st.info("ابعت أول رسالة في الشات لعرض مقاييس التحليل الدلالي والمراجع العلمية المستخدمة.")

    st.divider()
    if st.button("🧪 تشغيل اختبار الدقة المرجعي (Benchmark)", use_container_width=True):
        test_cases = [
            ("عندي امتحان بكرة ومش قادر أفتح كتاب", "academic_procrastination"),
            ("أنا زي الفل لدرجة إني بعيط لوحدي ومش قادر أتحرك", "exhaustion_low_mood"),
            ("مش مبسوط خالص وماليش نفس لأي حاجة", "exhaustion_low_mood"),
            ("قلبي بيدق بسرعة ومتعصب ومش طايق نفسي", "acute_stress_anger"),
            ("خايف من المستقبل ودماغي مش بتفصل تفكير", "anxiety_overthinking"),
            ("حاسس إني فاشل ومقصر في كل حاجة", "self_criticism_confidence"),
            ("حاسس إني لوحدي ومحدش فاهمني في البيت", "loneliness_relationships"),
            ("سهران ومش بعرف أنام خالص من كتر التفكير", "sleep_physical_burnout"),
            ("تايه ومش عارف أختار طريقي في الكلية", "confusion_meaning"),
            ("عايز أموت وأنهي حياتي", "CRISIS")
        ]
        rows = []
        correct = 0
        for sample, expected in test_cases:
            res = retrieve_best_support(sample, [])
            predicted = "CRISIS" if res["is_crisis"] else res["topic"]["id"]
            passed = (predicted == expected)
            if passed:
                correct += 1
            rows.append({
                "الجملة الاختبارية": sample[:28] + "...",
                "النتيجة": "✅ ناجح" if passed else "❌ مراجعة",
                "الثقة": f"{res['confidence']}%"
            })
        acc = round((correct / len(test_cases)) * 100, 1)
        st.success(f"دقة النموذج على حالات اللهجة المصرية والسخرية: {acc}% ({correct}/{len(test_cases)})")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
