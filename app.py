import streamlit as st
import sqlite3
import pandas as pd
import math
import re
import time
import random
from datetime import datetime

st.set_page_config(
    page_title="Quiet Harbor | الملاذ الهادئ",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
        background-color: #F4F8F9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    section[data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
        background-color: #E6F0F2;
    }
    .stMarkdown, p, h1, h2, h3, h4, label, .stMetric {
        direction: rtl;
        text-align: right;
    }
    .calm-card {
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 12px;
        border-right: 5px solid #2B7A78;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .book-badge {
        background-color: #DEF2F1;
        color: #17252A;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 6px;
    }
    div.stButton > button {
        background-color: #2B7A78;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

DB_NAME = "quiet_harbor_live.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            valence REAL,
            arousal REAL,
            sleep_hours REAL,
            wellness_score REAL,
            quadrant TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# مكتبة كتب علم النفس الموثوقة بصياغة حوارية إنسانية طبيعية
PSYCHOLOGY_BOOKS = [
    {
        "id": "burns_1980",
        "title": "الشعور الجيد (Feeling Good)",
        "author": "د. ديفيد بيرنز",
        "category": "العلاج المعرفي السلوكي (CBT)",
        "corpus": "تهويل فشل سقوط امتحان مستقبل ضاع كارثه مصيبه ابيض اسود دائما ابدا مستحيل انجح اكتئاب نتيجه",
        "turn1": "حاسس بيك أوي، والضغط ده طبيعي لما تحس إن مستقبلك متوقف على حاجة واحدة. بس عارف، دكتور ديفيد بيرنز في كتاب (الشعور الجيد) اتكلم عن إن مخنا ساعة الخوف بيعمل حاجة اسمها 'التهويل'، يعني بيخلينا نشوف أي تعثر كأنه نهاية العالم. قولي بصراحة، إيه أكتر سيناريو مخوفك دلوقتي؟",
        "turn2": "فهمتك جدًا، وعندك حق تقلق. بس جرب تبصلها زي ما بيرنز بيقول في كتابه: اكتب الفكرة اللي مخوفاك دي في ورقة، واسأل نفسك إيه الدليل الواقعي اللي يثبت إنها هتحصل فعلاً، وإيه الحاجات اللي في إيدك تعملها النهاردة ولو بسيطة. تحب نركز على خطوة واحدة صغيرة نبدأ بيها دلوقتي؟",
        "summary": "يشرح كيف تسبب التشوهات الفكرية مثل التهويل القلق والاكتئاب، وكيفية استبدالها بنظرة واقعية متوازنة.",
        "exercise": "اكتب الفكرة المقلقة واكتب قصادها دليلين واقعيين من حياتك يثبتوا عكسها."
    },
    {
        "id": "clear_2018",
        "title": "العادات الذرية (Atomic Habits)",
        "author": "جيمس كلير",
        "category": "بناء العادات والتغلب على التسويف",
        "corpus": "مكسل تسويف مراكم مذاكره مش قادر ابدا مفيش حماس بضيع وقتي تاجيل دروس واجب",
        "turn1": "بص يا صديقي، إحساس التقل لما الحاجات تتراكم علينا ده كلنا بنمر بيه، ومش معناه أبدًا إنك شخص كسول. جيمس كلير في كتاب (العادات الذرية) بيقول إن التسويف بيحصل لما مخنا يشوف المهمة ضخمة ومُرهقة فبيقفل منها. إيه أكتر حاجة مراكمها وحاسس إنها تقيلة على قلبك دلوقتي؟",
        "turn2": "منطقي جدًا إنها تبان تقيلة بالمنظر ده. الحل اللي جيمس كلير بيقترحه في كتابه بسيط أوي واسمه 'قاعدة الدقيقتين': سيبك من إنك تخلصها كلها النهاردة، افتح بس الكتاب أو اللابتوب واقرأ صفحة واحدة أو اشتغل دقيقتين بالظبط. جربها كده وقولي حسيت بإيه؟",
        "summary": "يشرح كيفية التغلب على التسويف عبر تصغير البدايات وبناء عادات يومية بسيطة.",
        "exercise": "طبّق قاعدة الدقيقتين: ابدأ بأصغر جزء ممكن من المهمة لمدة دقيقتين فقط."
    },
    {
        "id": "harris_2008",
        "title": "فخ السعادة (The Happiness Trap)",
        "author": "د. روس هاريس",
        "category": "التعامل مع التفكير الزائد (Overthinking)",
        "corpus": "بفكر كتير دماغي هتتفجر مش عارف ابطل تفكير اوفر ثينكينج افكار بتلف في دماغي وسواس سرحان",
        "turn1": "آه من دوامة التفكير اللي مبتفصلش دي، بتسحب طاقة الواحد وهو قاعد مكانه. دكتور روس هاريس في كتاب (فخ السعادة) بيشبه دماغنا براديو شغال طول الوقت عشان يحاول يحمينا، بس المشكلة إننا بنصدق كل كلمة بيقولها. إيه الموضوع اللي واخد حيز كبير من تفكيرك دلوقتي؟",
        "turn2": "طبيعي جدًا إن الموضوع ده يشغلك. بس جرب حركة لطيفة قال عليها روس هاريس في كتابه: بدل ما تغرق جوه الفكرة، قول لنفسك بهدوء 'أنا ملاحظ إن عقلي بيفكر في كذا دلوقتي'.. مجرد إنك تراقب الفكرة كأنها سحابة معدية بيهدّي دوشة دماغك جدًا. جرب تاخد نفس عميق كده وقولي الدنيا هديت شوية؟",
        "summary": "يساعد في التحرر من دوامة التفكير الزائد والقلق عبر مراقبة الأفكار دون الاندماج فيها.",
        "exercise": "راقب الفكرة وقل: 'عقلي يرسل لي فكرة الآن' بدلاً من التعامل معها كحقيقة."
    },
    {
        "id": "neff_2011",
        "title": "التعاطف مع الذات (Self-Compassion)",
        "author": "د. كريستين نيف",
        "category": "تقدير الذات ووقف جلد الذات",
        "corpus": "انا غبي انا فاشل انا السبب عيب فيا ماليش لازمه بكره نفسي جلد ذات مقصر مش كفايه غلطت",
        "turn1": "هون على نفسك شوية بالله عليك، واضح إنك قاسي على نفسك أوي النهاردة. دكتورة كريستين نيف في كتاب (التعاطف مع الذات) بتقول إن جلد الذات بيكسر الواحد وبيمنعه يصلح غلطه، مش بيشجعه زي ما إحنا فاكرين. احكيلي إيه اللي حصل وخلاك تلوم نفسك بالشكل ده؟",
        "turn2": "اسمعني كويس.. لو أعز صاحب ليك جه حكالك نفس الموقف ده وهو زعلان، عمرك ما كنت هتقوله الكلام القاسي اللي بتقوله لنفسك ده، صح؟ كريستين نيف بتنصحنا في كتابها إننا نكلم نفسنا بنفس اللطف اللي بنكلم بيه صحابنا وقت أزمتهم. إنت إنسان بتحاول وبتتعلم، مش مطلوب منك الكمال.",
        "summary": "يثبت علميًا أن التعامل بلطف وتفهم مع النفس وقت التعثر أكثر فاعلية من النقد الذاتي القاسي.",
        "exercise": "وجّه لنفسك جملة دعم صادقة كما لو كنت تواسي صديقك المقرّب."
    },
    {
        "id": "beck_1979",
        "title": "العلاج المعرفي (Cognitive Therapy)",
        "author": "د. آرون بيك",
        "category": "فهم العلاقات وإعادة البناء المعرفي",
        "corpus": "بيكرهوني نظرتهم ليا بيضحكوا عليا اكيد زعلانين مني عارف بيفكروا في ايه رفض صحابي ناس",
        "turn1": "صعب أوي الإحساس إنك حاسس إن اللي حواليك مش متقبلينك أو واخدين موقف منك. بس عارف، دكتور آرون بيك مؤسس العلاج المعرفي بيقول إننا ساعات بنقع في فخ 'قراءة الأفكار'، يعني بنفترض إننا عارفين الناس بتفكر في إيه من غير دليل أكيد. إيه التصرف اللي خلاك تحس بكده؟",
        "turn2": "عندك حق إن الموقف ده يضايق ويحير، بس تفتكر ممكن يكون الشخص ده مضغوط في حياته أو سرحان في مشاكله الخاصة ومش قاصدك إنت خالص؟ آرون بيك دايمًا بيقول إننا نعامل أفكارنا كأنها احتمالات مش حقائق مؤكدة عشان نريّح قلبنا.",
        "summary": "يعلمنا كيفية اختبار توقعاتنا السلبية عن أنفسنا وعن نظرة الآخرين لنا بموضوعية.",
        "exercise": "ضع 3 تفسيرات بديلة ومحايدة لتصرف الشخص قبل الحكم على نواياه."
    },
    {
        "id": "goleman_1995",
        "title": "الذكاء العاطفي (Emotional Intelligence)",
        "author": "د. دانيال جولمان",
        "category": "إدارة الغضب والانفعالات",
        "corpus": "متعصب غضبان اتخانقت مش طايق حد نرفزه خناقه اهل صحاب زعل استفزاز",
        "turn1": "خد نفس عميق وهدّي أعصابك، باين إن الموقف استفزك على الآخر. دانيال جولمان في كتاب (الذكاء العاطفي) بيشرح إن لحظة الغضب الشديد مركز الانفعال في المخ بيسيطر علينا قبل ما نفكر بهدوء. فضفضلي إيه اللي حصل وعصّبك كده؟",
        "turn2": "ليّك حق تتضايق، الموقف فعلاً مستفز. بس زي ما جولمان بيقول في كتابه، أجمل انتصار إنك متخليش حد يسحبك لرد فعل تندم عليه بعدين؛ مجرد إنك سمّيت إحساسك وفضفضت بيه دلوقتي ده لوحده بيهدي نار الغضب. تحب تاخد دقيقتين تهدى فيهم قبل ما تاخد أي قرار؟",
        "summary": "يشرح كيفية السيطرة على نوبات الغضب وفهم المشاعر الحقيقية خلف الانفعال.",
        "exercise": "أجّل أي رد فعل لمدة 6 ثوانٍ مع تنفس بطيء لاستعادة التحكم المنطقي."
    },
    {
        "id": "porges_2011",
        "title": "النظرية البوليفاجالية (The Polyvagal Theory)",
        "author": "د. ستيفن بورجس",
        "category": "تهدئة نوبات الهلع والجهاز العصبي",
        "corpus": "قلبي بيدق بسرعه مرعوب هلع مش عارف اخد نفسي خوف شديد توتر مفاجئ جسمي بيرتعش",
        "turn1": "أنا معاك ومش هسيبك، ركز في صوتي دلوقتي.. جسمك في حالة إنذار طبيعية عشان يحميك، وده اللي مخلي ضربات قلبك سريعة. دكتور ستيفن بورجس في (النظرية البوليفاجالية) بيقول إن أسرع طريقة نطمن بيها جهازنا العصبي هي إننا نطوّل الزفير. تقدر تاخد معايا نفس عميق من مناخيرك دلوقتي وتطلعه بالراحة أوي من بقك؟",
        "turn2": "عاش عليك، كمل نفسين تلاتة بنفس البطء ده.. كل زفير بطيء بيبعت رسالة أمان مباشرة لمخك إن الخطر خلص. لو حابب، افتح قسم (تمارين تهدئة الأعصاب) في القائمة الجانبية وجرّب مؤقت التنفس لمدة دقيقة، هتفرق معاك جدًا.",
        "summary": "يشرح كيفية تهدئة العصب الحائر وخفض التوتر الجسدي ونوبات الهلع بالتنفس البطيء.",
        "exercise": "تنفس 4-7-8: شهيق 4 ثوانٍ، حبس 7 ثوانٍ، وزفير بطيء 8 ثوانٍ."
    },
    {
        "id": "frankl_1946",
        "title": "الإنسان يبحث عن المعنى (Man's Search for Meaning)",
        "author": "د. فيكتور فرانكل",
        "category": "تجاوز الإحباط وفقدان الشغف",
        "corpus": "زهقان ملل مفيش هدف فراغ حياه ملهاش معني احباط فقدان شغف وحيد طهقان",
        "turn1": "حاسس بيك.. ساعات الواحد بيوصل لمرحلة يحس فيها إن الأيام شبه بعضها ومفيش شغف لحاجة. دكتور فيكتور فرانكل في كتابه العظيم (الإنسان يبحث عن المعنى) كان بيقول إن المعنى مش حاجة ضخمة بندور عليها، ده حاجة صغيرة إحنا اللي بنصنعها في يومنا. إيه أكتر حاجة مخلياك حاسس بالملل أو الفراغ الفترة دي؟",
        "turn2": "فهمتك أوي. فرانكل في كتابه بيقترح فكرة بسيطة بتفرق جدًا: اختار حاجة واحدة صغيرة تعملها النهاردة ليها قيمة عندك — سواء تساعد حد، تتعلم معلومة جديدة، أو حتى تهتم بنفسك. جرب تدّي ليومك هدف صغير النهاردة وقولي حاسس بإيه.",
        "summary": "يوضح كيف يمنح وجود هدف ومعنى صغير للإنسان صلابة نفسية في مواجهة الإحباط والفراغ.",
        "exercise": "حدد فعلاً صغيراً ذا قيمة ليك ونفذه اليوم."
    }
]

def normalize_arabic(text):
    text = text.lower().strip()
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    replacements = {
        "هسقط": "سقوط فشل امتحان",
        "هفشل": "فشل سقوط",
        "مفيش": "لا يوجد مستحيل",
        "دايما": "دائما ابدا",
        "بيكرهوني": "يكرهني رفض",
        "مش قادر": "عاجز ضغط",
        "مخنوق": "ضيق قلق توتر",
        "مرعوب": "خوف هلع قلق",
        "تعبان": "ضغط ارهاق ضيق",
        "زعلان": "حزن ضيق زعل",
        "مكسل": "تسويف كسل تاجيل",
        "مراكم": "تسويف مذاكره ضغط",
        "متعصب": "غضب نرفزه خناقه",
        "بفكر كتير": "تفكير زائد اوفر ثينكينج"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def compute_cosine_similarity(text1, text2):
    words1 = normalize_arabic(text1).split()
    words2 = normalize_arabic(text2).split()
    vocab = set(words1).union(set(words2))
    if not vocab:
        return 0.0
    vec1 = [words1.count(w) for w in vocab]
    vec2 = [words2.count(w) for w in vocab]
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def generate_human_reply(user_text):
    norm_text = normalize_arabic(user_text)

    # 1. بروتوكول الطوارئ
    crisis_terms = ["انتحار", "اموت نفسي", "اقتل نفسي", "ايذاء نفسي", "انهي حياتي", "مش عايز اعيش"]
    if any(term in norm_text for term in crisis_terms):
        return (
            "حياتك غالية جدًا وأنا خايف عليك.. من فضلك متواجهش الألم ده لوحدك، كلم متخصص فورًا على الخط الساخن للصحة النفسية في مصر (16328) أو خط النجدة (16000)، أو اتكلم حالاً مع حد قريب منك بتثق فيه."
        )

    # 2. التحيات والكلام العادي
    greetings = ["ازيك", "عامل ايه", "السلام عليكم", "اهلا", "هاي", "هلو", "صباح الخير", "مساء الخير", "اخبارك"]
    if any(g in norm_text for g in greetings) and len(norm_text.split()) <= 4:
        st.session_state.active_book = None
        st.session_state.turn_stage = 0
        return random.choice([
            "أهلاً بيك يا صديقي! أنا الحمد لله بخير، إنت عامل إيه النهاردة؟ طمني عليك.",
            "أهلاً وسهلاً بيك.. منورني. أخبارك إيه النهاردة؟ حابب نحكي في إيه؟"
        ])

    # 3. الشكر وإنهاء الكلام
    thanks = ["شكرا", "تسلم", "متشكر", "كتر خيرك", "ربنا يخليك", "تمام", "ماشي"]
    if any(t in norm_text for t in thanks) and len(norm_text.split()) <= 4:
        st.session_state.active_book = None
        st.session_state.turn_stage = 0
        return random.choice([
            "على إيه بس، إحنا إخوات وأنا موجود هنا في أي وقت تحتاج تفضفض فيه. ربنا يطمن قلبك دايمًا.",
            "ربنا يسعدك ويريح بالك يا رب.. لو احتجت تتكلم في أي حاجة تانية أنا معاك."
        ])

    # 4. لو الجملة قصيرة أوي زي "مخنوق" أو "متضايق" نسأله الأول زي البشر
    vague_words = ["مخنوق", "متضايق", "زعلان", "تعبان", "قرفان", "مش كويس"]
    if len(norm_text.split()) <= 2 and any(v in norm_text for v in vague_words):
        return "سلامتك من الضيق يا صديقي.. تحب تحكيلي إيه اللي وصّلك للإحساس ده؟ أنا سامعك بكل اهتمام."

    # 5. البحث عن أنسب كتاب لحالته
    best_book = None
    best_score = 0.0
    for book in PSYCHOLOGY_BOOKS:
        score = compute_cosine_similarity(norm_text, book["corpus"] + " " + book["summary"])
        if score > best_score:
            best_score = score
            best_book = book

    # لو المستخدم بيكمل نفس الحوار (الرد التاني على سؤال المساعد)
    if st.session_state.get("active_book") and st.session_state.get("turn_stage") == 1 and best_score < 0.25:
        book = st.session_state.active_book
        st.session_state.turn_stage = 2
        return book["turn2"]

    # لو فتح موضوع جديد ومطابق لكتاب معين
    if best_book and best_score > 0:
        st.session_state.active_book = best_book
        st.session_state.turn_stage = 1
        return best_book["turn1"]

    # لو بيحكي موقف عام مش مرتبط بكلمات مفتاحية محددة
    if st.session_state.get("turn_stage") == 1:
        st.session_state.turn_stage = 2
        return "كلامك مفهوم جدًا، ومن حقك تحس بكده في موقف زي ده. تفتكر إيه أكتر حاجة لو حصلت دلوقتي هتخليك تحس إنك أهدى وأحسن ولو بنسبة بسيطة؟"

    st.session_state.turn_stage = 1
    return "أنا سامعك ومقدّر جدًا إنك بتشاركني ده.. ممكن تحكيلي تفاصيل أكتر شوية عن الموقف عشان نقدر نفكر فيه سوا بهدوء؟"

def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# القائمة الجانبية
with st.sidebar:
    st.title("⚓ Quiet Harbor")
    st.caption("مساحتك الآمنة للفضفضة والدعم")
    st.markdown("---")
    page = st.radio(
        "اختر القسم:",
        [
            "1. 💬 فضفض مع صديقك الذكي",
            "2. 📚 مكتبة كتب علم النفس",
            "3. 🎭 قياس المزاج اليومي",
            "4. 🧘 تمارين تهدئة الأعصاب",
            "5. 📈 سجل حالتك"
        ]
    )
    st.markdown("---")
    st.info("🔒 محادثاتك خاصة تمامًا ولا يتم مشاركة هويتك مع أي جهة.")

# ==========================================
# 1. الشاشة الرئيسية: الشات الطبيعي
# ==========================================
if page.startswith("1."):
    st.title("⚓ الملاذ الهادئ | Quiet Harbor")
    st.caption("احكي اللي في قلبك براحتك.. كأنك بتكلم صاحبك اللي بيفهمك.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "أهلاً بيك ⚓ عامل إيه النهاردة؟ لو في حاجة شاغلة بالك أو مضايقاك احكيلي وأنا سامعك."
            }
        ]
        st.session_state.active_book = None
        st.session_state.turn_stage = 0

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("اكتب اللي في بالك هنا..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = generate_human_reply(prompt)
        with st.chat_message("assistant"):
            if hasattr(st, "write_stream"):
                st.write_stream(stream_text(response))
            else:
                box = st.empty()
                typed = ""
                for w in response.split(" "):
                    typed += w + " "
                    box.markdown(typed)
                    time.sleep(0.03)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# 2. مكتبة كتب علم النفس
# ==========================================
elif page.startswith("2."):
    st.title("📚 مكتبة كتب علم النفس الموثوقة")
    st.markdown("الكتب والمراجع العلمية اللي مبني عليها أسلوب الدعم والحوار:")

    for book in PSYCHOLOGY_BOOKS:
        st.markdown(f"""
        <div class="calm-card">
            <span class="book-badge">{book['category']}</span>
            <h4>📖 {book['title']} — {book['author']}</h4>
            <p>{book['summary']}</p>
            <p><b>خطوة عملية:</b> {book['exercise']}</p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. قياس المزاج
# ==========================================
elif page.startswith("3."):
    st.title("🎭 قياس المزاج والطاقة")
    valence = st.slider("مؤشر الارتياح النفسي (من -5 ضيق شديد إلى +5 سعادة وارتياح):", -5.0, 5.0, 0.0, 0.5)
    arousal = st.slider("مؤشر التوتر والطاقة (من -5 خمول وهدوء إلى +5 توتر أو حماس عالٍ):", -5.0, 5.0, 0.0, 0.5)
    sleep_hours = st.number_input("ساعات النوم آخر 24 ساعة:", 0.0, 16.0, 7.5, 0.5)

    v_norm = ((valence + 5) / 10) * 50
    a_norm = (1 - (abs(arousal) / 5)) * 25
    s_norm = (1 - min(abs(sleep_hours - 8.0), 8.0) / 8.0) * 25
    score = round(v_norm + a_norm + s_norm, 1)

    if valence >= 0 and arousal >= 0:
        q_label = "طاقة إيجابية وحماس"
    elif valence >= 0 and arousal < 0:
        q_label = "هدوء واسترخاء واتزان"
    elif valence < 0 and arousal >= 0:
        q_label = "توتر وقلق عالٍ"
    else:
        q_label = "إرهاق وخمول"

    st.info(f"**حالتك الآن:** {q_label} | **مؤشر الاتزان:** {score}%")

    if st.button("💾 حفظ القياس"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO mood_logs (timestamp, valence, arousal, sleep_hours, wellness_score, quadrant) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), valence, arousal, sleep_hours, score, q_label)
        )
        conn.commit()
        conn.close()
        st.success("تم حفظ قياسك بنجاح!")

# ==========================================
# 4. تمارين تهدئة الأعصاب
# ==========================================
elif page.startswith("4."):
    st.title("🧘 تمارين تهدئة الأعصاب السريعة")
    st.markdown("""
    <div class="calm-card">
        <span class="book-badge">تنفس 4-7-8 لتهدئة ضربات القلب</span>
        <p>شهيق 4 ثوانٍ، حبس النفس 7 ثوانٍ، زفير بطيء 8 ثوانٍ.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("▶️ ابدأ تمرين التنفس الآن"):
        box = st.empty()
        for label, sec in [("🌬️ شهيق عميق من الأنف...", 4), ("⏸️ احبس نفسك بهدوء...", 7), ("😮‍💨 زفير بطيء من الفم...", 8)]:
            for i in range(sec, 0, -1):
                box.info(f"### {label} ({i})")
                time.sleep(1)
        box.success("✅ ممتاز! حسيت بهدوء أكتر دلوقتي؟")

# ==========================================
# 5. سجل الحالة
# ==========================================
elif page.startswith("5."):
    st.title("📈 سجل تطور حالتك")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM mood_logs", conn)
    conn.close()
    if not df.empty:
        st.line_chart(df.set_index("timestamp")["wellness_score"])
        st.dataframe(df[["timestamp", "quadrant", "sleep_hours", "wellness_score"]], use_container_width=True)
    else:
        st.warning("سجّل قياسك اليومي في قسم (قياس المزاج) عشان يظهرلك الرسم البياني هنا.")