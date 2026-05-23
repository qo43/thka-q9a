const translations = {
    ar: {
        dir: "rtl",
        title: "واثق | مراجعة المستندات القضائية",
        brand: "منصة واثق",
        heroTitle: "مراجعة وصياغة المستندات القضائية",
        uploadEyebrow: "رفع مستند",
        formTitle: "بيانات مقدم الطلب",
        fullNameLabel: "الاسم الكامل",
        fullNamePlaceholder: "اكتب الاسم الكامل",
        nationalIdLabel: "رقم الهوية",
        nationalIdPlaceholder: "مثال: 1023456789",
        documentLabel: "المستند",
        chooseFile: "اختيار ملف",
        fileHint: "PDF أو صورة JPG/PNG",
        noFile: "لم يتم اختيار ملف بعد",
        submit: "تحليل المستند",
        busySubmit: "جار تحليل المستند...",
        analyzing: "جار استخراج النص وتحليل الصياغة. قد يستغرق ذلك قليلا...",
        nameMissing: "الرجاء إدخال الاسم الكامل.",
        idMissing: "رقم الهوية يجب أن يتكون من 10 أرقام.",
        fileMissing: "الرجاء اختيار ملف PDF أو صورة.",
        connectionError: "تعذر الاتصال بالخادم. تأكد من تشغيل الخدمة ثم حاول مرة أخرى.",
        serverError: "تعذر الاتصال بالخادم. حاول مرة أخرى.",
        analyzed: "تم تحليل المستند.",
        notAnalyzed: "تعذر تحليل المستند.",
        resultEyebrow: "نتيجة المراجعة",
        reportTitle: "تقرير واثق",
        metricLanguage: "اللغة",
        metricYear: "السنة",
        metricCaseType: "نوع القضية",
        metricConfidence: "جودة القراءة",
        issuesTitle: "الملاحظات ومواقعها",
        rewriteTitle: "أفضل صياغة مقترحة",
        extractedTitle: "النص المستخرج من المستند",
        noIssues: "لم يتم العثور على ملاحظات واضحة.",
        wholeDocument: "المستند بالكامل",
        noRewrite: "لم يتم توليد صياغة مقترحة.",
        successWithYear: (year) => `تم تحليل المستند بنجاح. مستند لعام ${year}.`,
        languageNames: { ar: "العربية", en: "الإنجليزية" },
        caseTypes: {
            Administrative: "إدارية",
            Financial: "مالية",
            Enforcement: "تنفيذ",
            Other: "أخرى",
        },
        severities: {
            high: "مهم",
            medium: "متوسط",
            low: "تحسين",
            fallback: "ملاحظة",
        },
    },
    en: {
        dir: "ltr",
        title: "Wathiq | Legal Document Review",
        brand: "Wathiq Platform",
        heroTitle: "Legal Document Review and Drafting",
        uploadEyebrow: "Upload document",
        formTitle: "Applicant information",
        fullNameLabel: "Full name",
        fullNamePlaceholder: "Enter full name",
        nationalIdLabel: "National ID",
        nationalIdPlaceholder: "Example: 1023456789",
        documentLabel: "Document",
        chooseFile: "Choose file",
        fileHint: "PDF or JPG/PNG image",
        noFile: "No file selected yet",
        submit: "Analyze document",
        busySubmit: "Analyzing document...",
        analyzing: "Extracting text and reviewing the legal writing. This may take a moment...",
        nameMissing: "Please enter the full name.",
        idMissing: "National ID must be 10 digits.",
        fileMissing: "Please choose a PDF or image file.",
        connectionError: "Could not connect to the server. Make sure the service is running and try again.",
        serverError: "Could not connect to the server. Please try again.",
        analyzed: "Document analyzed.",
        notAnalyzed: "Could not analyze the document.",
        resultEyebrow: "Review result",
        reportTitle: "Wathiq report",
        metricLanguage: "Language",
        metricYear: "Year",
        metricCaseType: "Case type",
        metricConfidence: "Text quality",
        issuesTitle: "Issues and locations",
        rewriteTitle: "Best suggested rewrite",
        extractedTitle: "Extracted document text",
        noIssues: "No clear issues were found.",
        wholeDocument: "Whole document",
        noRewrite: "No suggested rewrite was generated.",
        successWithYear: (year) => `Document analyzed successfully. Document year: ${year}.`,
        languageNames: { ar: "Arabic", en: "English" },
        caseTypes: {
            Administrative: "Administrative",
            Financial: "Financial",
            Enforcement: "Enforcement",
            Other: "Other",
        },
        severities: {
            high: "Important",
            medium: "Medium",
            low: "Improve",
            fallback: "Note",
        },
    },
};

let uiLanguage = localStorage.getItem("wathiq-ui-language") || "ar";
if (!translations[uiLanguage]) uiLanguage = "ar";

let languageSwitchTimer;
let lastApiJson = null;
let selectedFileName = "";

const nameInput = document.querySelector("#name");
const nationalIdInput = document.querySelector("#national-id");
const fileDisplay = document.querySelector("#chosen-files");
const pdfInput = document.querySelector("#pdf-input");
const uploadBtn = document.querySelector("#submit");
const mainStatusDiv = document.querySelector(".status");
const mainStatus = document.querySelector("#status-text");
const loading = document.querySelector(".loading");
const resultsPanel = document.querySelector("#analysis-results");
const resultLanguage = document.querySelector("#result-language");
const resultYear = document.querySelector("#result-year");
const resultType = document.querySelector("#result-type");
const resultConfidence = document.querySelector("#result-confidence");
const issuesList = document.querySelector("#issues-list");
const bestRewrite = document.querySelector("#best-rewrite");
const extractedText = document.querySelector("#extracted-text");
const languageToggle = document.querySelector("#language-toggle");

const t = (key) => translations[uiLanguage][key];
const isValidNationalId = (value) => /^[0-9]{10}$/.test(value.trim());

const refreshLanguageContent = (lang) => {
    uiLanguage = translations[lang] ? lang : "ar";
    const dictionary = translations[uiLanguage];

    localStorage.setItem("wathiq-ui-language", uiLanguage);
    document.documentElement.lang = uiLanguage;
    document.documentElement.dir = dictionary.dir;
    document.documentElement.dataset.uiLanguage = uiLanguage;
    document.title = dictionary.title;

    document.querySelectorAll("[data-i18n]").forEach((element) => {
        const key = element.dataset.i18n;
        element.textContent = dictionary[key] || "";
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
        const key = element.dataset.i18nPlaceholder;
        element.placeholder = dictionary[key] || "";
    });

    const nextLanguage = uiLanguage === "ar" ? "en" : "ar";
    languageToggle.dataset.lang = nextLanguage;
    languageToggle.setAttribute("aria-label", nextLanguage === "en" ? "Switch to English" : "Switch to Arabic");
    languageToggle.title = nextLanguage === "en" ? "Switch to English" : "Switch to Arabic";

    fileDisplay.textContent = selectedFileName || dictionary.noFile;
    uploadBtn.textContent = loading.hidden ? dictionary.submit : dictionary.busySubmit;

    if (lastApiJson && !resultsPanel.hidden) {
        renderReview(lastApiJson, { shouldScroll: false });
    }
};

const applyLanguage = (lang, options = {}) => {
    const nextLanguage = translations[lang] ? lang : "ar";
    const shouldAnimate = options.animate !== false;

    window.clearTimeout(languageSwitchTimer);

    if (!shouldAnimate) {
        document.body.classList.remove("language-switching");
        refreshLanguageContent(nextLanguage);
        return;
    }

    document.body.classList.add("language-switching");
    languageSwitchTimer = window.setTimeout(() => {
        refreshLanguageContent(nextLanguage);
        window.requestAnimationFrame(() => {
            document.body.classList.remove("language-switching");
        });
    }, 130);
};

const setBusy = (isBusy) => {
    loading.hidden = !isBusy;
    uploadBtn.disabled = isBusy;
    uploadBtn.textContent = isBusy ? t("busySubmit") : t("submit");
};

const resetResults = () => {
    lastApiJson = null;
    resultsPanel.hidden = true;
    resultsPanel.dataset.language = "";
    issuesList.replaceChildren();
    bestRewrite.textContent = "";
    extractedText.textContent = "";
};

const getReasonText = (apiJson) => {
    if (apiJson?.isValid && apiJson.caseYear) {
        return t("successWithYear")(apiJson.caseYear);
    }

    if (apiJson?.reason && uiLanguage === "ar") {
        return apiJson.reason;
    }

    return apiJson?.isValid ? t("analyzed") : t("notAnalyzed");
};

pdfInput.addEventListener("change", () => {
    const file = pdfInput.files[0];
    selectedFileName = file ? file.name : "";
    fileDisplay.textContent = selectedFileName || t("noFile");
    displayStatus("");
    resetResults();
});

languageToggle.addEventListener("click", () => applyLanguage(languageToggle.dataset.lang));

const checkFormData = () => {
    if (!nameInput.value.trim()) {
        displayStatus(t("nameMissing"));
        nameInput.focus();
        return false;
    }

    if (!isValidNationalId(nationalIdInput.value)) {
        displayStatus(t("idMissing"));
        nationalIdInput.focus();
        return false;
    }

    if (!pdfInput.files.length) {
        displayStatus(t("fileMissing"));
        pdfInput.focus();
        return false;
    }

    return true;
};

const changeStatusColor = (isSuccess) => {
    mainStatusDiv.classList.toggle("error", Boolean(mainStatus.textContent) && !isSuccess);
    mainStatusDiv.classList.toggle("success", Boolean(mainStatus.textContent) && isSuccess);
};

function displayStatus(text, isSuccess = false) {
    mainStatus.textContent = text;
    changeStatusColor(isSuccess);
}

const labelForLanguage = (lang) => t("languageNames")[lang] || lang || "-";
const labelForCaseType = (caseType) => t("caseTypes")[caseType] || caseType || "-";
const labelForSeverity = (severity) => t("severities")[severity] || t("severities").fallback;

const renderReview = (apiJson, options = {}) => {
    const review = apiJson.review;
    if (!review) {
        resetResults();
        return;
    }

    lastApiJson = apiJson;

    const classification = review.classification || {};
    const reviewLanguage = review.language === "en" ? "en" : "ar";
    resultsPanel.dataset.language = reviewLanguage;
    resultLanguage.textContent = labelForLanguage(reviewLanguage);
    resultYear.textContent = apiJson.caseYear || "-";
    resultType.textContent = labelForCaseType(classification.case_type);
    resultConfidence.textContent = Number.isFinite(Number(apiJson.debugScore))
        ? `${Math.round(Number(apiJson.debugScore) * 100)}%`
        : "-";

    issuesList.replaceChildren();
    const issues = Array.isArray(review.issues) ? review.issues : [];

    if (!issues.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = t("noIssues");
        issuesList.append(empty);
    }

    for (const issue of issues) {
        const item = document.createElement("article");
        item.className = `issue-card severity-${issue.severity || "low"}`;
        item.dir = reviewLanguage === "en" ? "ltr" : "rtl";

        const badge = document.createElement("span");
        badge.className = "issue-badge";
        badge.textContent = labelForSeverity(issue.severity);

        const where = document.createElement("p");
        where.className = "issue-where";
        where.textContent = issue.where || t("wholeDocument");

        const problem = document.createElement("p");
        problem.className = "issue-problem";
        problem.textContent = issue.problem || "";

        const suggestion = document.createElement("p");
        suggestion.className = "issue-suggestion";
        suggestion.textContent = issue.suggestion || "";

        const replacement = document.createElement("pre");
        replacement.className = "issue-replacement";
        replacement.dir = reviewLanguage === "en" ? "ltr" : "rtl";
        replacement.textContent = issue.replacement || "";

        item.append(badge, where, problem, suggestion, replacement);
        issuesList.append(item);
    }

    bestRewrite.dir = reviewLanguage === "en" ? "ltr" : "rtl";
    extractedText.dir = reviewLanguage === "en" ? "ltr" : "rtl";
    bestRewrite.textContent = review.bestRewrite || t("noRewrite");
    extractedText.textContent = apiJson.text || "";
    resultsPanel.hidden = false;

    if (options.shouldScroll !== false) {
        resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
};

uploadBtn.addEventListener("click", async () => {
    displayStatus("");
    resetResults();

    if (!checkFormData()) return;

    const formData = new FormData();
    formData.append("name", nameInput.value.trim());
    formData.append("national_id", nationalIdInput.value.trim());
    formData.append("file", pdfInput.files[0]);

    setBusy(true);
    displayStatus(t("analyzing"), true);

    try {
        const aiResponse = await fetch("/api/scan", {
            method: "POST",
            body: formData,
        });

        let apiJson = {};
        try {
            apiJson = await aiResponse.json();
        } catch {
            apiJson = {};
        }

        if (!aiResponse.ok) {
            displayStatus(apiJson.reason && uiLanguage === "ar" ? apiJson.reason : t("serverError"));
            return;
        }

        const reviewLanguage = apiJson?.review?.language === "en" ? "en" : "ar";
        if (apiJson.review && reviewLanguage !== uiLanguage) {
            refreshLanguageContent(reviewLanguage);
        }

        displayStatus(getReasonText(apiJson), Boolean(apiJson.isValid));
        renderReview(apiJson);
    } catch (error) {
        console.error("[API ERROR]:", error);
        displayStatus(t("connectionError"));
    } finally {
        setBusy(false);
    }
});

applyLanguage(uiLanguage, { animate: false });
