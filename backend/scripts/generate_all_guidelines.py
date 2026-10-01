"""
================================================================================
ClinSaarthi AI - Comprehensive Clinical Guidelines PDF Generator & Ingestion
================================================================================
Generates 5 realistic, multi-column, multi-page clinical guidelines across
major medical specialties (Cardiology, Endocrinology, Hypertension, Pulmonology,
and Infectious Disease) and indexes them into PostgreSQL/SQLite and ChromaDB.
================================================================================
"""
from pathlib import Path
import os
import sys
import django
import pymupdf

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.documents.models import Document
from services.ingestion_service import IngestionService

GUIDELINES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "guidelines"
GUIDELINES_DIR.mkdir(parents=True, exist_ok=True)


def build_page_layout(doc, title_text, col1_text, col2_text, page_number_str="Page 1 of 4", table_data=None):
    """Creates a standard 2-column A4 clinical guideline page."""
    page = doc.new_page(width=595, height=842)  # A4 size

    # Header / Title banner
    title_rect = pymupdf.Rect(40, 35, 555, 80)
    page.insert_textbox(
        title_rect,
        title_text,
        fontsize=12,
        fontname="helv",
        color=(0.1, 0.22, 0.45),
        align=pymupdf.TEXT_ALIGN_CENTER
    )

    # Decorative header rule
    shape = page.new_shape()
    shape.draw_line(pymupdf.Point(40, 85), pymupdf.Point(555, 85))
    shape.finish(color=(0.7, 0.75, 0.85), width=1)
    shape.commit()

    # Column 1 (Left: x0=40, x1=285)
    col1_rect = pymupdf.Rect(40, 95, 285, 770)
    page.insert_textbox(col1_rect, col1_text, fontsize=9.2, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)

    # Column 2 (Right: x0=310, x1=555)
    bottom_y = 620 if table_data else 770
    col2_rect = pymupdf.Rect(310, 95, 555, bottom_y)
    page.insert_textbox(col2_rect, col2_text, fontsize=9.2, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)

    # Optional table in bottom right
    if table_data:
        table_rect = pymupdf.Rect(310, 630, 555, 770)
        table_lines = [table_data["title"]] + [f"{k}: {v}" for k, v in table_data["rows"].items()]
        table_content = "\n".join(table_lines)
        page.draw_rect(table_rect, color=(0.2, 0.4, 0.7), fill=(0.95, 0.97, 1.0), width=0.8)
        page.insert_textbox(pymupdf.Rect(315, 635, 550, 765), table_content, fontsize=8.5, fontname="helv")

    # Footer rule and page number
    shape = page.new_shape()
    shape.draw_line(pymupdf.Point(40, 785), pymupdf.Point(555, 785))
    shape.finish(color=(0.8, 0.8, 0.8), width=0.5)
    shape.commit()

    footer_rect = pymupdf.Rect(40, 790, 555, 810)
    page.insert_textbox(
        footer_rect,
        f"ClinSaarthi AI Certified Guideline Repository  |  {page_number_str}  |  Evidence Grade: Class I, Level A",
        fontsize=8,
        fontname="helv",
        color=(0.4, 0.4, 0.4),
        align=pymupdf.TEXT_ALIGN_CENTER
    )
    return page


# ==============================================================================
# 1. CARDIOLOGY: 2026 AHA/ACC/HRS Guideline for Atrial Fibrillation (4 Pages)
# ==============================================================================
def create_cardiology_afib_pdf(output_path: Path):
    doc = pymupdf.open()

    # Page 1
    t1 = "2026 AHA/ACC/HRS PRACTICE GUIDELINE FOR ATRIAL FIBRILLATION\nClinical Evaluation, Diagnosis & Classification Framework"
    c1_1 = (
        "1. CLINICAL OVERVIEW & EPIDEMIOLOGY\n"
        "Atrial fibrillation (AF) is the most prevalent sustained supraventricular arrhythmia globally. "
        "AF is associated with a 5-fold increase in thromboembolic stroke, a 3-fold elevation in heart failure risk, "
        "and a 1.5- to 1.9-fold increase in all-cause mortality. Early identification and systematic stroke risk "
        "stratification are vital components of modern cardiovascular care.\n\n"
        "2. DIAGNOSTIC CRITERIA & WORKUP\n"
        "A definitive clinical diagnosis of AF requires documentation on a standard 12-lead electrocardiogram (ECG) "
        "or a continuous rhythm strip of at least 30 seconds showing irregular R-R intervals without discernible, "
        "organized P waves. Initial comprehensive evaluation must include:\n"
        "• Transthoracic echocardiography (TTE) to evaluate left atrial size, LVEF, and valvular morphology.\n"
        "• Serum thyroid-stimulating hormone (TSH) to exclude hyperthyroidism.\n"
        "• Complete metabolic panel and serum creatinine/eGFR for baseline renal assessment.\n"
        "• Complete blood count (CBC) to screen for occult anemia."
    )
    c1_2 = (
        "3. ARRHYTHMIA CLASSIFICATION PATTERNS\n"
        "• Paroxysmal AF: Spontaneously terminates or converts with intervention within 7 days of onset.\n"
        "• Persistent AF: Continuous AF sustained beyond 7 days, requiring pharmacological or electrical cardioversion.\n"
        "• Long-Standing Persistent AF: Continuous AF lasting longer than 12 months in duration.\n"
        "• Permanent AF: Patient and clinician agree to cease further rhythm control strategies.\n\n"
        "4. INITIAL STABILIZATION\n"
        "Patients presenting with acute hemodynamically unstable AF (hypotension, acute pulmonary edema, angina) "
        "mandate immediate synchronized electrical cardioversion regardless of arrhythmia duration."
    )
    build_page_layout(doc, t1, c1_1, c1_2, "Page 1 of 4")

    # Page 2
    t2 = "2026 AHA/ACC/HRS PRACTICE GUIDELINE FOR ATRIAL FIBRILLATION\nThromboembolic Stroke Stratification & Bleeding Risk Assessment"
    c2_1 = (
        "5. STROKE RISK STRATIFICATION (CHA2DS2-VASc)\n"
        "The CHA2DS2-VASc scoring model is the gold standard for thromboembolic risk determination in non-valvular AF:\n"
        "• Congestive Heart Failure or LVEF <= 40% (+1 point)\n"
        "• Hypertension / resting BP >= 140/90 mmHg (+1 point)\n"
        "• Age >= 75 years (+2 points)\n"
        "• Diabetes Mellitus (+1 point)\n"
        "• Prior Stroke, TIA, or Thromboembolism (+2 points)\n"
        "• Vascular Disease (Prior MI, PAD, aortic plaque) (+1 point)\n"
        "• Age 65 to 74 years (+1 point)\n"
        "• Sex Category Female (+1 point)\n\n"
        "RECOMMENDATIONS FOR ANTICOAGULATION:\n"
        "• Score >= 2 in Men or >= 3 in Women: Oral anticoagulation is strongly recommended (Class I, Level A).\n"
        "• Score = 1 in Men or = 2 in Women: Oral anticoagulation should be considered based on clinical shared decision-making.\n"
        "• Score = 0 in Men or = 1 in Women: No antithrombotic therapy is recommended."
    )
    c2_2 = (
        "6. BLEEDING RISK EVALUATION (HAS-BLED)\n"
        "Evaluating bleeding risk helps identify modifiable risk factors rather than serving as a reason to withhold "
        "anticoagulation. A HAS-BLED score >= 3 indicates high bleeding risk requiring frequent clinical monitoring.\n\n"
        "MODIFIABLE BLEEDING RISK FACTORS:\n"
        "• Uncontrolled hypertension (systolic BP > 160 mmHg).\n"
        "• Concomitant use of antiplatelet agents (aspirin, clopidogrel) or NSAIDs.\n"
        "• Excessive alcohol intake (> 8 units per week).\n"
        "• Labile INR values in patients on Warfarin.\n"
        "• Modifiable liver or renal impairment."
    )
    table_afib_score = {
        "title": "TABLE 1: CHA2DS2-VASc SCORE VS ANNUAL STROKE RISK",
        "rows": {
            "Score 0": "0.2% annual stroke risk (No therapy)",
            "Score 1": "0.6% annual stroke risk (Consider DOAC)",
            "Score 2": "2.2% annual stroke risk (DOAC Indicated)",
            "Score 3": "3.2% annual stroke risk (DOAC Indicated)",
            "Score 4+": "4.8% - 11.2% annual stroke risk (High Risk)"
        }
    }
    build_page_layout(doc, t2, c2_1, c2_2, "Page 2 of 4", table_data=table_afib_score)

    # Page 3
    t3 = "2026 AHA/ACC/HRS PRACTICE GUIDELINE FOR ATRIAL FIBRILLATION\nDirect Oral Anticoagulants (DOACs): Pharmacotherapy & Renal Adjustments"
    c3_1 = (
        "7. FIRST-LINE ORAL ANTICOAGULATION (DOACs)\n"
        "Direct Oral Anticoagulants (DOACs) are recommended in preference to vitamin K antagonists (Warfarin) "
        "for stroke prevention in non-valvular AF due to superior safety profiles and significantly reduced "
        "rates of fatal intracranial hemorrhage.\n\n"
        "RECOMMENDED DOAC REGIMENS:\n"
        "• Apixaban: Standard dose is 5 mg orally twice daily.\n"
        "  Dose reduction to 2.5 mg orally twice daily is required if the patient meets at least TWO of the "
        "  following criteria: Age >= 80 years, Body weight <= 60 kg, or Serum creatinine >= 1.5 mg/dL (133 umol/L).\n\n"
        "• Rivaroxaban: Standard dose is 20 mg orally once daily taken with the evening meal (food is required "
        "  to achieve consistent oral bioavailability).\n"
        "  Dose reduction to 15 mg orally once daily is indicated for patients with moderate renal impairment "
        "  (Creatinine Clearance CrCl 15 to 49 mL/min)."
    )
    c3_2 = (
        "• Dabigatran: Direct thrombin inhibitor. Standard dose is 150 mg orally twice daily.\n"
        "  Dose reduction to 75 mg orally twice daily is indicated for CrCl 15 to 30 mL/min.\n\n"
        "• Edoxaban: Factor Xa inhibitor. Standard dose is 60 mg orally once daily.\n"
        "  Reduce to 30 mg orally once daily if CrCl 15 to 50 mL/min or body weight <= 60 kg.\n\n"
        "CONTRAINDICATIONS TO DOACs:\n"
        "DOACs are strictly contraindicated in patients with mechanical prosthetic heart valves or moderate-to-severe "
        "mitral stenosis. Warfarin (target INR 2.0 to 3.0) remains the mandatory anticoagulation choice for mechanical valves."
    )
    table_doac_dosing = {
        "title": "TABLE 2: DOAC FIRST-LINE DOSING MATRIX",
        "rows": {
            "Apixaban": "5 mg bid (2.5 mg bid if 2 of: age>=80, wt<=60kg, Cr>=1.5)",
            "Rivaroxaban": "20 mg qd with food (15 mg qd if CrCl 15-49 mL/min)",
            "Dabigatran": "150 mg bid (75 mg bid if CrCl 15-30 mL/min)",
            "Edoxaban": "60 mg qd (30 mg qd if CrCl 15-50 mL/min)"
        }
    }
    build_page_layout(doc, t3, c3_1, c3_2, "Page 3 of 4", table_data=table_doac_dosing)

    # Page 4
    t4 = "2026 AHA/ACC/HRS PRACTICE GUIDELINE FOR ATRIAL FIBRILLATION\nRate vs Rhythm Control Strategies & Catheter Ablation Protocols"
    c4_1 = (
        "8. RATE CONTROL PHARMACOTHERAPY\n"
        "Ventricular rate control is initial therapy for the majority of symptomatic AF patients. "
        "Target resting heart rate is < 100 to 110 beats per minute.\n\n"
        "FIRST-LINE RATE CONTROL AGENTS:\n"
        "• Beta-Blockers (Preserved or Reduced LVEF):\n"
        "  - Metoprolol Succinate: 50 to 200 mg orally once daily.\n"
        "  - Bisoprolol: 2.5 to 10 mg orally once daily.\n"
        "  - Carvedilol: 3.125 to 25 mg orally twice daily.\n\n"
        "• Non-Dihydropyridine Calcium Channel Blockers (Preserved LVEF > 40% only):\n"
        "  - Diltiazem Extended Release: 120 to 360 mg orally once daily.\n"
        "  - Verapamil: 120 to 360 mg orally once daily.\n"
        "  CAUTION: CCBs are contraindicated in heart failure with reduced ejection fraction (HFrEF).\n\n"
        "• Digoxin: 0.125 to 0.25 mg orally once daily. Useful in sedentary patients or as add-on in HFrEF."
    )
    c4_2 = (
        "9. RHYTHM CONTROL & CARDIOVERSION PROTOCOLS\n"
        "Early rhythm control improves cardiovascular outcomes in patients diagnosed within 1 year.\n\n"
        "ANTICOAGULATION PERI-CARDIOVERSION MANDATE:\n"
        "For AF of >= 48 hours duration or unknown duration, therapeutic anticoagulation (DOAC or Warfarin) "
        "is mandatory for at least 3 consecutive weeks prior to elective cardioversion, and MUST be continued "
        "for a minimum of 4 weeks post-cardioversion regardless of successful sinus rhythm restoration.\n\n"
        "10. CATHETER ABLATION INDICATIONS\n"
        "Pulmonary vein isolation (PVI) catheter ablation is recommended as Class I therapy for symptomatic "
        "paroxysmal AF refractory or intolerant to at least one antiarrhythmic drug (AAD), and as first-line therapy "
        "in patients with heart failure and reduced ejection fraction to improve survival."
    )
    build_page_layout(doc, t4, c4_1, c4_2, "Page 4 of 4")

    doc.save(str(output_path))
    doc.close()
    print(f"Generated Cardiology Guideline: {output_path.name}")


# ==============================================================================
# 2. ENDOCRINOLOGY: 2026 ADA Standards of Care in Type 2 Diabetes (4 Pages)
# ==============================================================================
def create_diabetes_guideline_pdf(output_path: Path):
    doc = pymupdf.open()

    # Page 1
    t1 = "2026 ADA STANDARDS OF MEDICAL CARE IN DIABETES\nDiagnostic Criteria, Glycemic Targets & Holistic Management"
    c1_1 = (
        "1. DIAGNOSTIC CRITERIA FOR TYPE 2 DIABETES\n"
        "Diagnosis of diabetes requires confirmation by one of the following criteria (repeated on a second occasion):\n"
        "• Fasting Plasma Glucose (FPG) >= 126 mg/dL (7.0 mmol/L) after an 8-hour fast.\n"
        "• 2-Hour Plasma Glucose >= 200 mg/dL (11.1 mmol/L) during a 75-g oral glucose tolerance test (OGTT).\n"
        "• Glycated Hemoglobin (HbA1c) >= 6.5% (48 mmol/mol) using a certified NGSP assay.\n"
        "• Random Plasma Glucose >= 200 mg/dL (11.1 mmol/L) in the presence of classic hyperglycemic symptoms "
        "(polyuria, polydipsia, unexplained weight loss).\n\n"
        "2. PREDIABETES CATEGORIES\n"
        "Impaired Fasting Glucose (FPG 100 to 125 mg/dL) or Impaired Glucose Tolerance (2-hr PG 140 to 199 mg/dL) "
        "or HbA1c 5.7% to 6.4% indicates high risk. Metformin therapy should be considered for prediabetes prevention."
    )
    c1_2 = (
        "3. INDIVIDUALIZED GLYCEMIC TARGETS\n"
        "• Standard Target: HbA1c < 7.0% (53 mmol/mol) is recommended for most non-pregnant adults to reduce "
        "microvascular and macrovascular complications.\n"
        "• Stringent Target (< 6.5%): Appropriate for younger patients, short diabetes duration, and without "
        "significant cardiovascular disease, if achievable without clinically significant hypoglycemia.\n"
        "• Relaxed Target (< 8.0%): Appropriate for patients with severe hypoglycemia history, limited life expectancy, "
        "advanced microvascular or macrovascular complications, or extensive comorbid conditions.\n\n"
        "4. LIFESTYLE INTERVENTIONS\n"
        "Structured medical nutrition therapy (Mediterranean or plant-based diet) and >= 150 minutes per week of "
        "moderate-to-vigorous aerobic exercise combined with resistance training are foundational."
    )
    build_page_layout(doc, t1, c1_1, c1_2, "Page 1 of 4")

    # Page 2
    t2 = "2026 ADA STANDARDS OF MEDICAL CARE IN DIABETES\nFirst-Line Pharmacotherapy: Metformin Guidelines & Renal Precautions"
    c2_1 = (
        "5. FIRST-LINE ORAL AGENT: METFORMIN\n"
        "Metformin (biguanide) remains the established foundational first-line agent for the management of type 2 diabetes "
        "in the absence of specific contraindications or end-organ complications.\n\n"
        "MECHANISM OF ACTION:\n"
        "Reduces hepatic gluconeogenesis, decreases intestinal absorption of glucose, and improves peripheral insulin "
        "sensitivity by activating AMP-activated protein kinase (AMPK).\n\n"
        "DOSING & TITRATION PROTOCOL:\n"
        "• Starting Dose: Metformin immediate-release 500 mg orally once or twice daily with morning and evening meals.\n"
        "• Titration: Increase by 500 mg weekly to minimize gastrointestinal adverse effects (nausea, diarrhea, abdominal cramps).\n"
        "• Maintenance Dose: 1000 mg orally twice daily (or Metformin Extended-Release 2000 mg once daily with the evening meal).\n"
        "• Maximum Effective Dose: 2000 mg to 2550 mg per day."
    )
    c2_2 = (
        "6. RENAL FUNCTION MONITORING & METFORMIN SAFETY\n"
        "Assess estimated Glomerular Filtration Rate (eGFR) prior to initiation and at least annually thereafter:\n"
        "• eGFR >= 60 mL/min/1.73m2: Full dose safe (up to 2000-2550 mg/day). Monitor renal panel annually.\n"
        "• eGFR 45 to 59 mL/min/1.73m2: Continued therapy permitted. Monitor renal function every 3 to 6 months.\n"
        "• eGFR 30 to 44 mL/min/1.73m2: Dose reduction recommended. Maximum daily dose should not exceed 1000 mg daily. "
        "Do not initiate in treatment-naive patients.\n"
        "• eGFR < 30 mL/min/1.73m2: Strictly Contraindicated. Discontinue immediately due to the elevated risk "
        "of fatal Metformin-associated lactic acidosis (MALA).\n\n"
        "VITAMIN B12 MONITORING:\n"
        "Long-term Metformin use is associated with biochemical vitamin B12 deficiency. Periodic serum B12 testing "
        "is recommended every 2 to 3 years, particularly in patients presenting with peripheral neuropathy or anemia."
    )
    table_metformin_renal = {
        "title": "TABLE 1: METFORMIN eGFR DOSING PROTOCOL",
        "rows": {
            "eGFR >= 60": "Standard dose (up to 2000 mg daily)",
            "eGFR 45 - 59": "Maintain dose, monitor eGFR q6m",
            "eGFR 30 - 44": "Reduce dose (max 1000 mg daily)",
            "eGFR < 30": "STRICTLY CONTRAINDICATED (Discontinue)"
        }
    }
    build_page_layout(doc, t2, c2_1, c2_2, "Page 2 of 4", table_data=table_metformin_renal)

    # Page 3
    t3 = "2026 ADA STANDARDS OF MEDICAL CARE IN DIABETES\nCardiorenal Protective Therapies: SGLT2 Inhibitors & GLP-1 Receptor Agonists"
    c3_1 = (
        "7. CARDIORENAL RISK-BASED SELECTION (INDEPENDENT OF HbA1c)\n"
        "In patients with established Atherosclerotic Cardiovascular Disease (ASCVD), Heart Failure (HF), or "
        "Chronic Kidney Disease (CKD), SGLT2 inhibitors or GLP-1 receptor agonists with proven cardiovascular benefit "
        "are recommended as part of the glucose-lowering regimen, regardless of baseline HbA1c or Metformin use.\n\n"
        "SODIUM-GLUCOSE COTRANSPORTER 2 (SGLT2) INHIBITORS:\n"
        "Preferred in patients with Heart Failure (HFrEF or HFpEF) or CKD (eGFR 20 to 60 mL/min with UACR > 30 mg/g):\n"
        "• Empagliflozin: 10 mg orally once daily; can titrate to 25 mg once daily. Proven reduction in cardiovascular "
        "  death, HF hospitalizations, and CKD progression.\n"
        "• Dapagliflozin: 10 mg orally once daily. Reduces HF hospitalizations and slows renal function decline.\n"
        "• Adverse Effects: Mycotic genital infections, euglycemic diabetic ketoacidosis (euDKA), volume depletion."
    )
    c3_2 = (
        "GLUCAGON-LIKE PEPTIDE-1 (GLP-1) RECEPTOR AGONISTS:\n"
        "Preferred in patients with established ASCVD (prior MI, stroke, revascularization) or high cardiovascular risk, "
        "and where weight reduction is a primary therapeutic goal:\n"
        "• Semaglutide: Subcutaneous 0.25 mg weekly for 4 weeks (initiation dose, not effective for glycemic control), "
        "  then increase to 0.5 mg weekly. If needed after 4 weeks, titrate to 1.0 mg weekly, up to maximum 2.0 mg weekly.\n"
        "• Dulaglutide: 0.75 mg subcutaneously once weekly; titrate to 1.5 mg up to 4.5 mg weekly.\n"
        "• Dual GIP/GLP-1 Agonist (Tirzepatide): 2.5 mg weekly for 4 weeks, titrate by 2.5 mg increments every 4 weeks "
        "  to target dose of 5 mg, 10 mg, or maximum 15 mg weekly.\n"
        "• Adverse Effects: Nausea, vomiting, diarrhea, pancreatitis risk. Contraindicated in personal or family "
        "  history of medullary thyroid carcinoma (MTC) or MEN2 syndrome."
    )
    table_cardiorenal = {
        "title": "TABLE 2: CARDIORENAL AGENT PREFERENCES",
        "rows": {
            "Heart Failure (HFrEF/HFpEF)": "SGLT2i preferred (Empagliflozin 10mg / Dapagliflozin 10mg)",
            "Chronic Kidney Disease": "SGLT2i (eGFR>=20) or GLP-1 RA if SGLT2i contraindicated",
            "Established ASCVD": "GLP-1 RA or SGLT2i with proven benefit",
            "Weight Loss Priority": "Tirzepatide or Semaglutide"
        }
    }
    build_page_layout(doc, t3, c3_1, c3_2, "Page 3 of 4", table_data=table_cardiorenal)

    # Page 4
    t4 = "2026 ADA STANDARDS OF MEDICAL CARE IN DIABETES\nBasal Insulin Initiation, Titration & Hypoglycemia Management"
    c4_1 = (
        "8. INSULIN THERAPY IN TYPE 2 DIABETES\n"
        "When oral agents and GLP-1 RAs fail to achieve glycemic targets, or in symptomatic severe hyperglycemia "
        "(HbA1c > 10% or blood glucose >= 300 mg/dL with catabolic features), basal insulin should be initiated.\n\n"
        "BASAL INSULIN PROTOCOL:\n"
        "• Agents: Insulin Glargine U-100/U-300, Insulin Degludec U-100/U-200, or Insulin Detemir.\n"
        "• Starting Dose: 10 units once daily at the same time each day, or weight-based 0.1 to 0.2 units/kg/day.\n"
        "• Titration Algorithm: Self-titrate by increasing dose by 2 units every 3 days until fasting plasma "
        "  glucose reaches target (80 to 130 mg/dL) without hypoglycemia.\n"
        "• If fasting glucose < 70 mg/dL: Decrease basal dose by 10% to 20% immediately."
    )
    c4_2 = (
        "9. HYPOGLYCEMIA DEFINITIONS & MANAGEMENT\n"
        "• Level 1: Glucose 54 to 69 mg/dL (Alert value).\n"
        "• Level 2: Glucose < 54 mg/dL (Clinically significant).\n"
        "• Level 3: Severe hypoglycemia accompanied by cognitive impairment requiring external assistance.\n\n"
        "THE 'RULE OF 15' PROTOCOL:\n"
        "1. Ingest 15 to 20 grams of fast-acting glucose (e.g., 4 glucose tablets, 1/2 cup fruit juice, or 1 tube glucose gel).\n"
        "2. Recheck blood glucose level in exactly 15 minutes.\n"
        "3. If blood glucose remains < 70 mg/dL, repeat 15 grams of glucose.\n"
        "4. Once glucose normalizes, consume a meal or snack containing complex carbohydrates and protein to prevent recurrence."
    )
    build_page_layout(doc, t4, c4_1, c4_2, "Page 4 of 4")

    doc.save(str(output_path))
    doc.close()
    print(f"Generated Diabetes Guideline: {output_path.name}")


# ==============================================================================
# 3. HYPERTENSION: 2026 ACC/AHA Guideline for High Blood Pressure (4 Pages)
# ==============================================================================
def create_hypertension_guideline_pdf(output_path: Path):
    doc = pymupdf.open()

    # Page 1
    t1 = "2026 ACC/AHA PRACTICE GUIDELINE FOR HIGH BLOOD PRESSURE\nClassification, Blood Pressure Measurement & Treatment Targets"
    c1_1 = (
        "1. BLOOD PRESSURE CLASSIFICATION CATEGORIES\n"
        "Blood pressure (BP) must be categorized based on an average of >= 2 careful in-office readings "
        "obtained on >= 2 separate occasions using a validated automated oscillometric device:\n"
        "• Normal BP: Systolic < 120 mmHg AND Diastolic < 80 mmHg.\n"
        "• Elevated BP: Systolic 120 to 129 mmHg AND Diastolic < 80 mmHg.\n"
        "• Stage 1 Hypertension: Systolic 130 to 139 mmHg OR Diastolic 80 to 89 mmHg.\n"
        "• Stage 2 Hypertension: Systolic >= 140 mmHg OR Diastolic >= 90 mmHg.\n"
        "• Hypertensive Crisis: Systolic > 180 mmHg and/or Diastolic > 120 mmHg.\n\n"
        "2. OUT-OF-OFFICE BP CONFIRMATION\n"
        "Ambulatory Blood Pressure Monitoring (ABPM) or standardized Home BP Monitoring (HBPM) is recommended "
        "to confirm hypertension and rule out white-coat hypertension before pharmacotherapy initiation."
    )
    c1_2 = (
        "3. UNIVERSAL BLOOD PRESSURE TARGETS\n"
        "• Primary Target: BP < 130/80 mmHg is recommended for all non-pregnant adult patients with confirmed hypertension.\n"
        "• High-Risk Populations: Patients with Type 2 Diabetes, Chronic Kidney Disease (CKD), Congestive Heart Failure, "
        "or Age >= 65 years share the universal target of BP < 130/80 mmHg (Class I, Level A).\n\n"
        "4. THRESHOLDS FOR PHARMACOTHERAPY INITIATION\n"
        "• Stage 1 Hypertension: Initiate single-agent pharmacotherapy if estimated 10-year ASCVD risk is >= 10%, "
        "or if patient has known diabetes, CKD, or clinical cardiovascular disease.\n"
        "• Stage 2 Hypertension: Initiate combination pharmacotherapy immediately with TWO first-line agents "
        "of different pharmacological classes."
    )
    build_page_layout(doc, t1, c1_1, c1_2, "Page 1 of 4")

    # Page 2
    t2 = "2026 ACC/AHA PRACTICE GUIDELINE FOR HIGH BLOOD PRESSURE\nFirst-Line Antihypertensive Classes, Regimens & Dosing Protocols"
    c2_1 = (
        "5. FIRST-LINE ANTIHYPERTENSIVE CLASSES\n"
        "Four primary drug classes have demonstrated equivalence in reducing major cardiovascular events and mortality:\n\n"
        "1. ANGIOTENSIN-CONVERTING ENZYME (ACE) INHIBITORS:\n"
        "• Lisinopril: Initial 10 mg orally once daily; titrate to target 20 to 40 mg once daily.\n"
        "• Enalapril: Initial 5 mg orally once or twice daily; titrate to 10 to 40 mg daily.\n"
        "• Key Adverse Effects: Dry cough (5-20% due to bradykinin accumulation), hyperkalemia, angioedema. "
        "Contraindicated in pregnancy.\n\n"
        "2. ANGIOTENSIN II RECEPTOR BLOCKERS (ARBs):\n"
        "• Losartan: Initial 50 mg orally once daily; titrate to 100 mg once daily.\n"
        "• Valsartan: Initial 80 mg orally once daily; titrate to 160 to 320 mg once daily.\n"
        "• Preferred alternative in patients experiencing ACE inhibitor-induced cough. Contraindicated in pregnancy."
    )
    c2_2 = (
        "3. CALCIUM CHANNEL BLOCKERS (DIHYDROPYRIDINE CCBs):\n"
        "• Amlodipine: Initial 5 mg orally once daily; titrate to maximum 10 mg once daily.\n"
        "• Nifedipine Extended-Release: 30 to 60 mg orally once daily (maximum 90 mg daily).\n"
        "• First-line choice in Black patients and elderly individuals with isolated systolic hypertension.\n"
        "• Adverse Effect: Dose-dependent peripheral ankle edema.\n\n"
        "4. THIAZIDE / THIAZIDE-LIKE DIURETICS:\n"
        "• Chlorthalidone: 12.5 to 25 mg orally once daily. Preferred over HCTZ due to prolonged half-life and "
        "proven cardiovascular event reduction.\n"
        "• Hydrochlorothiazide (HCTZ): 25 to 50 mg orally once daily.\n"
        "• Adverse Effects: Hypokalemia, hyponatremia, hyperuricemia (may precipitate gout)."
    )
    table_bp_dosing = {
        "title": "TABLE 1: FIRST-LINE ANTIHYPERTENSIVE DOSAGES",
        "rows": {
            "Lisinopril (ACEi)": "10 - 40 mg qd (Check K+ and Cr)",
            "Losartan (ARB)": "50 - 100 mg qd (Alternative to ACEi)",
            "Amlodipine (CCB)": "5 - 10 mg qd (First-line in Black adults)",
            "Chlorthalidone (Diuretic)": "12.5 - 25 mg qd (Preferred over HCTZ)"
        }
    }
    build_page_layout(doc, t2, c2_1, c2_2, "Page 2 of 4", table_data=table_bp_dosing)

    # Page 3
    t3 = "2026 ACC/AHA PRACTICE GUIDELINE FOR HIGH BLOOD PRESSURE\nCombination Strategies, Resistant Hypertension & Fourth-Line Therapy"
    c3_1 = (
        "6. COMBINATION THERAPY STRATEGIES\n"
        "In Stage 2 hypertension (systolic BP >= 140 mmHg or >= 20/10 mmHg above goal), initiate prompt treatment "
        "with two first-line agents, ideally as a single-pill fixed-dose combination to maximize patient adherence.\n\n"
        "RECOMMENDED COMBINATIONS:\n"
        "• ACE Inhibitor + Dihydropyridine CCB (e.g., Lisinopril + Amlodipine).\n"
        "• ARB + Thiazide Diuretic (e.g., Losartan + Chlorthalidone).\n"
        "• CCB + Thiazide Diuretic (e.g., Amlodipine + Chlorthalidone).\n\n"
        "CONTRAINDICATED COMBINATION:\n"
        "Dual blockade of the renin-angiotensin-aldosterone system (combining an ACE inhibitor with an ARB or direct "
        "renin inhibitor) is strictly contraindicated due to elevated risks of hyperkalemia, acute kidney injury, "
        "and syncope without added cardiovascular benefit."
    )
    c3_2 = (
        "7. RESISTANT HYPERTENSION DEFINITION\n"
        "Resistant hypertension is defined as blood pressure that remains above target (> 130/80 mmHg) despite "
        "concurrent adherence to optimal doses of THREE antihypertensive drug classes, one of which must be a diuretic.\n\n"
        "STEP 4 THERAPY: MINERALOCORTICOID RECEPTOR ANTAGONISTS (MRAs)\n"
        "• Spironolactone is the drug of choice for resistant hypertension.\n"
        "• Dosage: 25 to 50 mg orally once daily.\n"
        "• Safety Requirement: Baseline serum potassium must be < 4.5 mEq/L and eGFR must be >= 30 mL/min/1.73m2. "
        "Recheck serum potassium and creatinine within 1 to 2 weeks following initiation."
    )
    build_page_layout(doc, t3, c3_1, c3_2, "Page 3 of 4")

    # Page 4
    t4 = "2026 ACC/AHA PRACTICE GUIDELINE FOR HIGH BLOOD PRESSURE\nHypertensive Crises: Emergencies vs Urgencies & ICU Protocols"
    c4_1 = (
        "8. HYPERTENSIVE CRISIS MANAGEMENT\n"
        "Hypertensive crisis is defined as severe blood pressure elevation (Systolic > 180 mmHg and/or Diastolic > 120 mmHg).\n\n"
        "A. HYPERTENSIVE EMERGENCY:\n"
        "Severe BP elevation accompanied by acute, progressive target organ damage (e.g., acute coronary syndrome, "
        "acute pulmonary edema, acute aortic dissection, hypertensive encephalopathy, acute ischemic stroke, or acute renal failure).\n"
        "• Setting: Immediate admission to an intensive care unit (ICU).\n"
        "• Treatment Protocol: Continuous intravenous titratable antihypertensive infusions.\n"
        "• BP Reduction Goal: Reduce Mean Arterial Pressure (MAP) by no more than 20% to 25% within the first hour to prevent "
        "cerebral hypoperfusion, then reduce toward 160/100 mmHg over the next 2 to 6 hours."
    )
    c4_2 = (
        "PREFERRED INTRAVENOUS EMERGENCY AGENTS:\n"
        "• Nicardipine IV: 5 mg/h IV infusion, titrate by 2.5 mg/h every 5-15 min to max 15 mg/h.\n"
        "• Labetalol IV: 20 mg initial IV push over 2 min, then 40-80 mg every 10 min, or continuous infusion 1-2 mg/min.\n"
        "• Sodium Nitroprusside: 0.3 to 2 mcg/kg/min IV; reserved for acute pulmonary edema or refractory crisis.\n\n"
        "B. HYPERTENSIVE URGENCY:\n"
        "Severe BP elevation (> 180/120 mmHg) WITHOUT acute target organ damage.\n"
        "• Setting: Outpatient or emergency observation.\n"
        "• Treatment: Re-initiation or upward titration of oral agents (e.g., oral Captopril, Labetalol, or Amlodipine). "
        "Rapid intravenous reduction is contraindicated and hazardous."
    )
    build_page_layout(doc, t4, c4_1, c4_2, "Page 4 of 4")

    doc.save(str(output_path))
    doc.close()
    print(f"Generated Hypertension Guideline: {output_path.name}")


# ==============================================================================
# 4. PULMONOLOGY: 2026 GOLD Report on COPD (3 Pages)
# ==============================================================================
def create_copd_guideline_pdf(output_path: Path):
    doc = pymupdf.open()

    # Page 1
    t1 = "2026 GOLD GLOBAL STRATEGY FOR COPD\nDiagnosis, Spirometry Criteria & Severity Assessment"
    c1_1 = (
        "1. DIAGNOSTIC CRITERIA & PATHOPHYSIOLOGY\n"
        "Chronic Obstructive Pulmonary Disease (COPD) is a common, preventable, and treatable respiratory disorder "
        "characterized by chronic respiratory symptoms (dyspnea, cough, sputum production) resulting from abnormalities "
        "of the airways (bronchitis) and/or alveoli (emphysema).\n\n"
        "SPIROMETRIC CONFIRMATION:\n"
        "A post-bronchodilator FEV1/FVC ratio < 0.70 is mandatory to confirm persistent airflow limitation.\n\n"
        "GOLD SPIROMETRIC GRADING (Based on post-BD FEV1 % predicted):\n"
        "• GOLD 1 (Mild): FEV1 >= 80% predicted.\n"
        "• GOLD 2 (Moderate): 50% <= FEV1 < 80% predicted.\n"
        "• GOLD 3 (Severe): 30% <= FEV1 < 50% predicted.\n"
        "• GOLD 4 (Very Severe): FEV1 < 30% predicted."
    )
    c1_2 = (
        "2. CLINICAL ASSESSMENT (ABE ASSESSMENT TOOL)\n"
        "Combines symptom burden (mMRC or CAT score) and exacerbation history:\n"
        "• Group A: 0 to 1 moderate exacerbation not leading to hospital admission, low symptoms (mMRC 0-1, CAT < 10).\n"
        "• Group B: 0 to 1 moderate exacerbation, high symptoms (mMRC >= 2, CAT >= 10).\n"
        "• Group E: >= 2 moderate exacerbations or >= 1 exacerbation leading to hospital admission, regardless of symptom score."
    )
    build_page_layout(doc, t1, c1_1, c1_2, "Page 1 of 3")

    # Page 2
    t2 = "2026 GOLD GLOBAL STRATEGY FOR COPD\nPharmacologic Maintenance: Bronchodilators & Inhaled Corticosteroids"
    c2_1 = (
        "3. MAINTENANCE BRONCHODILATION\n"
        "Long-acting bronchodilators are central to symptom management and exacerbation reduction in COPD.\n\n"
        "DUAL BRONCHODILATION (LABA + LAMA):\n"
        "Dual therapy with a Long-Acting Muscarinic Antagonist (LAMA) plus a Long-Acting Beta2-Agonist (LABA) "
        "is superior to monotherapy and is recommended as initial maintenance therapy for Groups B and E.\n"
        "• Tiotropium (LAMA): 18 mcg inhalation once daily (HandiHaler) or 5 mcg once daily (Respimat).\n"
        "• Formoterol (LABA): 12 mcg inhalation twice daily.\n"
        "• Fixed-dose combinations: Umeclidinium/Vilanterol (62.5/25 mcg once daily) or Tiotropium/Olodaterol (5/5 mcg once daily)."
    )
    c2_2 = (
        "4. INHALED CORTICOSTEROIDS (ICS) GUIDANCE\n"
        "ICS should NOT be used as monotherapy in COPD. Triple therapy (LABA + LAMA + ICS) is indicated under specific criteria:\n"
        "• Blood Eosinophils >= 300 cells/uL: Strong recommendation for ICS addition.\n"
        "• Blood Eosinophils 100 to 299 cells/uL WITH >= 2 moderate exacerbations per year: Consider ICS addition.\n"
        "• Blood Eosinophils < 100 cells/uL: ICS is NOT recommended due to lack of efficacy and increased risk of pneumonia.\n\n"
        "RECOMMENDED TRIPLE REGIMEN:\n"
        "Fluticasone Furoate / Umeclidinium / Vilanterol (100/62.5/25 mcg once daily) or Budesonide / Glycopyrrolate / Formoterol (320/18/9.6 mcg twice daily)."
    )
    table_copd = {
        "title": "TABLE 1: COPD MAINTENANCE REGIMENS",
        "rows": {
            "Group A": "Single bronchodilator (SABA or LABA)",
            "Group B": "LABA + LAMA dual bronchodilation",
            "Group E (Eos <300)": "LABA + LAMA dual therapy",
            "Group E (Eos >=300)": "LABA + LAMA + ICS triple therapy"
        }
    }
    build_page_layout(doc, t2, c2_1, c2_2, "Page 2 of 3", table_data=table_copd)

    # Page 3
    t3 = "2026 GOLD GLOBAL STRATEGY FOR COPD\nAcute Exacerbations: Systemic Steroids, Antibiotics & Oxygen Target"
    c3_1 = (
        "5. ACUTE EXACERBATIONS MANAGEMENT\n"
        "A COPD exacerbation is defined as acute worsening of dyspnea, cough, and/or sputum within <= 14 days.\n\n"
        "SYSTEMIC CORTICOSTEROIDS:\n"
        "• Oral Prednisone 40 mg once daily for 5 days is recommended.\n"
        "• Prolonged courses (> 5 days) do not improve outcomes and substantially increase adverse effects.\n\n"
        "ANTIBIOTIC THERAPY (5 TO 7 DAYS):\n"
        "Indicated if patient exhibits all three cardinal symptoms (increased dyspnea, increased sputum volume, "
        "and increased sputum purulence) or two symptoms if one is purulent sputum:\n"
        "• First-line: Amoxicillin-Clavulanate 875/125 mg orally twice daily, or Azithromycin 500 mg day 1, then 250 mg daily."
    )
    c3_2 = (
        "6. CONTROLLED OXYGEN THERAPY\n"
        "In acute exacerbations, supplemental oxygen should be titrated to achieve a target oxygen saturation (SpO2) "
        "of 88% to 92% in patients at risk of hypercapnic respiratory failure.\n"
        "CAUTION: Excessive hyperoxia blunts hypoxic drive, worsens V/Q mismatch, and induces severe hypercapnia and acidosis.\n\n"
        "7. NON-INVASIVE VENTILATION (NIV)\n"
        "Bi-level positive airway pressure (BiPAP) is the first-line intervention for acute hypercapnic respiratory failure "
        "(pH < 7.35 and PaCO2 > 45 mmHg), reducing intubation rates and mortality."
    )
    build_page_layout(doc, t3, c3_1, c3_2, "Page 3 of 3")

    doc.save(str(output_path))
    doc.close()
    print(f"Generated COPD Guideline: {output_path.name}")


# ==============================================================================
# 5. INFECTIOUS DISEASE: 2026 IDSA/ATS Guideline for Pneumonia (3 Pages)
# ==============================================================================
def create_pneumonia_guideline_pdf(output_path: Path):
    doc = pymupdf.open()

    # Page 1
    t1 = "2026 IDSA/ATS GUIDELINE FOR COMMUNITY-ACQUIRED PNEUMONIA\nClinical Diagnosis, CURB-65 Triage & Site-of-Care Decisions"
    c1_1 = (
        "1. CLINICAL DIAGNOSTIC CRITERIA\n"
        "Community-Acquired Pneumonia (CAP) requires radiographic demonstration of pulmonary infiltrate (consolidation on "
        "chest X-ray or CT) accompanied by acute clinical features including fever, cough, purulent sputum production, "
        "dyspnea, pleuritic chest pain, and focal crackles on lung auscultation.\n\n"
        "2. CURB-65 RISK STRATIFICATION CRITERIA\n"
        "Assign 1 point for each feature present:\n"
        "• C: Confusion (abbreviated mental score <= 8, or acute disorientation)\n"
        "• U: Blood Urea Nitrogen > 19 mg/dL (or serum urea > 7 mmol/L)\n"
        "• R: Respiratory rate >= 30 breaths per minute\n"
        "• B: Blood pressure (Systolic < 90 mmHg or Diastolic <= 60 mmHg)\n"
        "• 65: Age >= 65 years"
    )
    c1_2 = (
        "SITE-OF-CARE RECOMMENDATIONS BASED ON CURB-65:\n"
        "• Score 0 or 1: Low risk (30-day mortality < 1.5%). Suitable for outpatient management.\n"
        "• Score 2: Moderate risk (mortality 9.2%). Inpatient hospital admission or closely monitored outpatient therapy.\n"
        "• Score 3 to 5: High risk (mortality 15% to 40%). Urgent hospital admission; scores 4 or 5 mandate intensive care (ICU) evaluation.\n\n"
        "MICROBIOLOGICAL TESTING:\n"
        "Blood cultures and sputum Gram stain/culture are recommended in hospitalized patients with severe CAP, or those "
        "empirically treated for MRSA or Pseudomonas aeruginosa."
    )
    table_curb = {
        "title": "TABLE 1: CURB-65 RISK STRATIFICATION",
        "rows": {
            "Score 0 - 1": "Outpatient management (Mortality <1.5%)",
            "Score 2": "Inpatient ward admission (Mortality ~9%)",
            "Score 3": "Inpatient admission (Mortality ~17%)",
            "Score 4 - 5": "ICU admission indicated (Mortality up to 40%)"
        }
    }
    build_page_layout(doc, t1, c1_1, c1_2, "Page 1 of 3", table_data=table_curb)

    # Page 2
    t2 = "2026 IDSA/ATS GUIDELINE FOR COMMUNITY-ACQUIRED PNEUMONIA\nEmpiric Antimicrobial Regimens: Outpatient vs Inpatient Ward"
    c2_1 = (
        "3. OUTPATIENT EMPIRIC ANTIMICROBIAL THERAPY\n"
        "A. Patients Without Comorbidities or Risk Factors:\n"
        "• Amoxicillin: 1000 mg orally three times daily for 5 days (preferred Class I).\n"
        "• Doxycycline: 100 mg orally twice daily for 5 days.\n"
        "• Macrolide (Azithromycin 500 mg day 1, then 250 mg daily) only in areas with pneumococcal macrolide resistance < 25%.\n\n"
        "B. Patients With Comorbidities (Heart, Lung, Liver, Renal Disease, Diabetes):\n"
        "• Combination Therapy (Preferred):\n"
        "  - Amoxicillin-Clavulanate 875/125 mg orally twice daily (or 2000/125 mg bid) PLUS Azithromycin 500 mg day 1, then 250 mg daily.\n"
        "• Monotherapy:\n"
        "  - Respiratory Fluoroquinolone: Levofloxacin 750 mg orally once daily, or Moxifloxacin 400 mg once daily."
    )
    c2_2 = (
        "4. INPATIENT NON-SEVERE CAP ANTIMICROBIAL REGIMENS\n"
        "Administer first antibiotic dose immediately in the emergency department.\n\n"
        "PREFERRED COMBINATION THERAPY:\n"
        "• Beta-Lactam + Macrolide:\n"
        "  - Ceftriaxone 1 to 2 g IV once daily PLUS Azithromycin 500 mg IV or oral daily.\n"
        "  - Alternative beta-lactams: Ampicillin-Sulbactam 1.5 to 3 g IV every 6 hours, or Cefotaxime 1 to 2 g IV every 8 hours.\n\n"
        "PREFERRED MONOTHERAPY:\n"
        "• Levofloxacin 750 mg IV or oral once daily, or Moxifloxacin 400 mg IV or oral once daily."
    )
    table_pneumonia_dosing = {
        "title": "TABLE 2: EMPIRIC CAP DOSAGES",
        "rows": {
            "Outpatient Healthy": "Amoxicillin 1 g tid or Doxycycline 100 mg bid",
            "Outpatient Comorbid": "Augmentin 875/125 bid + Azithromycin 500/250",
            "Inpatient Non-Severe": "Ceftriaxone 1-2 g IV qd + Azithromycin 500 mg",
            "Respiratory Quinolone": "Levofloxacin 750 mg qd (Alternative)"
        }
    }
    build_page_layout(doc, t2, c2_1, c2_2, "Page 2 of 3", table_data=table_pneumonia_dosing)

    # Page 3
    t3 = "2026 IDSA/ATS GUIDELINE FOR COMMUNITY-ACQUIRED PNEUMONIA\nSevere CAP, MRSA/Pseudomonas Protocols & Treatment Duration"
    c3_1 = (
        "5. SEVERE CAP & ICU REGIMENS\n"
        "Severe CAP requires combination therapy:\n"
        "• Ceftriaxone 2 g IV once daily PLUS Azithromycin 500 mg IV daily (or Levofloxacin 750 mg IV daily).\n\n"
        "RISK FACTORS FOR MRSA & PSEUDOMONAS AERUGINOSA:\n"
        "Prior respiratory isolation of the pathogen or recent hospitalization with IV antibiotic exposure in past 90 days.\n"
        "• If MRSA suspected: Add Vancomycin 15 to 20 mg/kg IV every 8 to 12 hours (target serum trough 15 to 20 mcg/mL) "
        "  OR Linezolid 600 mg IV every 12 hours.\n"
        "• If Pseudomonas suspected: Prescribe antipseudomonal beta-lactam (Piperacillin-Tazobactam 4.5 g IV every 6 hours, "
        "  or Cefepime 2 g IV every 8 hours, or Meropenem 1 g IV every 8 hours)."
    )
    c3_2 = (
        "6. DURATION OF ANTIMICROBIAL THERAPY\n"
        "• Minimum duration is 5 days.\n"
        "• Discontinuation Criteria: Patient must be afebrile for >= 48 hours and exhibit no more than 1 sign of clinical instability:\n"
        "  - Heart rate <= 100 bpm\n"
        "  - Respiratory rate <= 24 breaths/min\n"
        "  - Systolic BP >= 90 mmHg\n"
        "  - Oxygen saturation >= 90% on room air\n"
        "  - Normal mental status\n"
        "Procalcitonin levels can assist in guiding early cessation of antibiotic therapy."
    )
    build_page_layout(doc, t3, c3_1, c3_2, "Page 3 of 3")

    doc.save(str(output_path))
    doc.close()
    print(f"Generated Pneumonia Guideline: {output_path.name}")


# ==============================================================================
# Ingestion Orchestration
# ==============================================================================
def ingest_all():
    print("=================================================================")
    print("ClinSaarthi AI - Ingesting Comprehensive Medical Guidelines")
    print("=================================================================")

    # 1. Fetch default clinician user
    user = User.objects.filter(role=User.Role.CLINICIAN).first()
    if not user:
        user = User.objects.first()

    guidelines_config = [
        {
            "filename": "guideline_cardiology_afib.pdf",
            "title": "2026 AHA/ACC/HRS Guideline for the Management of Atrial Fibrillation",
            "generator": create_cardiology_afib_pdf
        },
        {
            "filename": "guideline_endocrinology_diabetes.pdf",
            "title": "2026 ADA Standards of Care in Diabetes: Type 2 Diabetes Management",
            "generator": create_diabetes_guideline_pdf
        },
        {
            "filename": "guideline_hypertension_cardiology.pdf",
            "title": "2026 ACC/AHA Practice Guideline for the Prevention and Management of High Blood Pressure",
            "generator": create_hypertension_guideline_pdf
        },
        {
            "filename": "guideline_pulmonology_copd.pdf",
            "title": "2026 GOLD Global Strategy for the Diagnosis and Management of COPD",
            "generator": create_copd_guideline_pdf
        },
        {
            "filename": "guideline_infectious_pneumonia.pdf",
            "title": "2026 IDSA/ATS Guideline for Community-Acquired Pneumonia (CAP)",
            "generator": create_pneumonia_guideline_pdf
        }
    ]

    for item in guidelines_config:
        pdf_path = GUIDELINES_DIR / item["filename"]
        # Generate the rich PDF
        item["generator"](pdf_path)

        # Register and process document in database
        doc, created = Document.objects.get_or_create(
            title=item["title"],
            defaults={
                "file": str(pdf_path),
                "uploaded_by": user
            }
        )
        print(f"Ingesting {item['title']}...")
        IngestionService.process_document(str(doc.id))
        doc.refresh_from_db()
        print(f" Successfully indexed: {doc.title} ({doc.chunks.count()} chunks, {doc.total_pages} pages)")

    print("\n All 5 comprehensive medical guideline PDFs generated and fully indexed!")

if __name__ == "__main__":
    ingest_all()
