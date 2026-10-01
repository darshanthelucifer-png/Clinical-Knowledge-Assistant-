/**
 * ==============================================================================
 * ClinSaarthi AI - Clinical Guideline Page Content Database
 * ==============================================================================
 * Provides structured multi-column page content, sections, and reference tables
 * for the 5 certified clinical practice guidelines loaded in the system:
 * 1. Cardiology: 2026 AHA/ACC/HRS Atrial Fibrillation Guideline
 * 2. Endocrinology: 2026 ADA Standards of Care in Diabetes
 * 3. Hypertension: 2026 ACC/AHA High Blood Pressure Guideline
 * 4. Pulmonology: 2026 GOLD Global Strategy for COPD
 * 5. Infectious Disease: 2026 IDSA/ATS Community-Acquired Pneumonia Guideline
 * ==============================================================================
 */

export interface PageContent {
  headerJournal: string;
  sectionTitle: string;
  col1Paragraphs: string[];
  col2Paragraphs: string[];
  table?: {
    title: string;
    rows: Array<{ label: string; value: string }>;
  };
}

export interface GuidelineDocumentData {
  id: string;
  domain: 'afib' | 'diabetes' | 'hypertension' | 'copd' | 'pneumonia';
  title: string;
  shortTitle: string;
  specialty: string;
  totalPages: number;
  pages: Record<number, PageContent>;
}

export const GUIDELINE_PAGE_DATA: Record<string, GuidelineDocumentData> = {
  afib: {
    id: 'afib',
    domain: 'afib',
    title: '2026 AHA/ACC/HRS Guideline for the Management of Atrial Fibrillation',
    shortTitle: 'AHA/ACC/HRS AFib Guideline (2026)',
    specialty: 'Cardiology',
    totalPages: 4,
    pages: {
      1: {
        headerJournal: 'Circulation & JACC (2026) 153:e100-e185',
        sectionTitle: 'Section 1: Clinical Evaluation, Diagnosis & Classification Framework',
        col1Paragraphs: [
          'Atrial fibrillation (AF) is the most prevalent sustained supraventricular arrhythmia globally. AF is associated with a 5-fold increase in thromboembolic stroke, a 3-fold elevation in heart failure risk, and a 1.5- to 1.9-fold increase in all-cause mortality.',
          'A definitive clinical diagnosis of AF requires documentation on a standard 12-lead electrocardiogram (ECG) or a continuous rhythm strip of at least 30 seconds showing irregular R-R intervals without discernible, organized P waves.',
          'Initial comprehensive evaluation must include transthoracic echocardiography (TTE) to evaluate left atrial size and LVEF, serum TSH, and baseline renal/hepatic function panels.',
        ],
        col2Paragraphs: [
          'Classification Patterns:\n• Paroxysmal AF: Spontaneously terminates or converts with intervention within 7 days of onset.\n• Persistent AF: Continuous AF sustained beyond 7 days, requiring pharmacological or electrical cardioversion.\n• Long-Standing Persistent AF: Continuous AF lasting longer than 12 months.\n• Permanent AF: Patient and clinician agree to cease further rhythm control strategies.',
          'Acute hemodynamically unstable AF (hypotension, pulmonary edema, angina) mandates immediate synchronized electrical cardioversion regardless of arrhythmia duration.',
        ],
      },
      2: {
        headerJournal: 'Circulation & JACC (2026) 153:e100-e185',
        sectionTitle: 'Section 2: Thromboembolic Stroke Stratification (CHA2DS2-VASc)',
        col1Paragraphs: [
          'The CHA2DS2-VASc scoring model is the gold standard for thromboembolic stroke risk determination in non-valvular AF. Score >= 2 in Men or >= 3 in Women indicates oral anticoagulation is strongly recommended (Class I, Level A).',
          'Score = 1 in Men or = 2 in Women indicates oral anticoagulation should be considered based on shared decision-making. Score = 0 in Men or = 1 in Women indicates no antithrombotic therapy is recommended.',
        ],
        col2Paragraphs: [
          'Evaluating bleeding risk with the HAS-BLED score helps identify modifiable risk factors (e.g. uncontrolled systolic BP >160 mmHg, NSAID/aspirin use, labile INRs, alcohol excess). A HAS-BLED score >= 3 indicates high bleeding risk requiring frequent clinical monitoring rather than withholding anticoagulation.',
        ],
        table: {
          title: 'Table 1: CHA2DS2-VASc Stroke Risk Stratification',
          rows: [
            { label: 'Score 0 (Men) / 1 (Women)', value: 'Low Risk: No antithrombotic therapy' },
            { label: 'Score 1 (Men) / 2 (Women)', value: 'Intermediate: Consider DOAC therapy' },
            { label: 'Score >= 2 (Men) / >= 3 (Women)', value: 'High Risk: DOAC strongly indicated (Class I)' },
            { label: 'Prior Stroke / TIA (+2 pts)', value: 'Automatic high thromboembolic risk' },
          ],
        },
      },
      3: {
        headerJournal: 'Circulation & JACC (2026) 153:e100-e185',
        sectionTitle: 'Section 4.2: Direct Oral Anticoagulant (DOAC) Dosing & Renal Function',
        col1Paragraphs: [
          'Direct Oral Anticoagulants (DOACs) are recommended in preference to vitamin K antagonists (Warfarin) for stroke prevention in non-valvular AF due to superior safety profiles and significantly reduced intracranial hemorrhage.',
          'For non-valvular atrial fibrillation, Rivaroxaban 20 mg once daily with the evening meal is recommended for patients with normal renal function (CrCl >= 50 mL/min). In patients with moderate renal impairment (CrCl 15–49 mL/min), reduce dose to 15 mg once daily.',
        ],
        col2Paragraphs: [
          'Apixaban standard dose is 5 mg orally twice daily. Dose reduction to 2.5 mg twice daily is required if patient meets at least TWO of: Age >= 80 years, Body weight <= 60 kg, or Serum creatinine >= 1.5 mg/dL.',
          'Dabigatran standard dose is 150 mg twice daily (reduce to 75 mg twice daily if CrCl 15-30 mL/min). DOACs are strictly contraindicated in mechanical prosthetic valves or moderate-to-severe mitral stenosis.',
        ],
        table: {
          title: 'Table 2: DOAC Renal Dosing Matrix',
          rows: [
            { label: 'Rivaroxaban Normal', value: '20 mg once daily taken with evening meal' },
            { label: 'Rivaroxaban CrCl 15-49', value: '15 mg once daily with evening meal' },
            { label: 'Apixaban Normal', value: '5 mg twice daily' },
            { label: 'Apixaban (2 criteria met)', value: '2.5 mg twice daily' },
          ],
        },
      },
      4: {
        headerJournal: 'Circulation & JACC (2026) 153:e100-e185',
        sectionTitle: 'Section 4: Rate vs Rhythm Control Strategies & Cardioversion Protocols',
        col1Paragraphs: [
          'Ventricular rate control is initial therapy for the majority of symptomatic AF patients. Target resting heart rate is < 100 to 110 beats per minute.',
          'First-line rate control agents include beta-blockers (Metoprolol Succinate 50-200 mg daily, Bisoprolol 2.5-10 mg daily, Carvedilol 3.125-25 mg bid) and non-DHP CCBs (Diltiazem ER 120-360 mg, Verapamil 120-360 mg). CCBs are contraindicated in HFrEF.',
        ],
        col2Paragraphs: [
          'For AF of >= 48 hours duration or unknown duration, therapeutic anticoagulation (DOAC or Warfarin) is mandatory for at least 3 consecutive weeks prior to elective cardioversion, and MUST be continued for a minimum of 4 weeks post-cardioversion.',
          'Catheter ablation (pulmonary vein isolation) is recommended as Class I therapy for symptomatic paroxysmal AF refractory to antiarrhythmic drugs and in patients with heart failure with reduced ejection fraction.',
        ],
      },
    },
  },
  diabetes: {
    id: 'diabetes',
    domain: 'diabetes',
    title: '2026 ADA Standards of Care in Diabetes: Type 2 Diabetes Management',
    shortTitle: 'ADA Standards of Care in Diabetes (2026)',
    specialty: 'Endocrinology',
    totalPages: 4,
    pages: {
      1: {
        headerJournal: 'Diabetes Care (2026) 49 (Suppl. 1):S1-S270',
        sectionTitle: 'Section 1: Diagnostic Criteria, Glycemic Targets & Holistic Management',
        col1Paragraphs: [
          'Diagnosis of Type 2 Diabetes requires confirmation by one of the following criteria (repeated on a second occasion):\n• Fasting Plasma Glucose (FPG) >= 126 mg/dL (7.0 mmol/L) after an 8-hour fast.\n• 2-Hour Plasma Glucose >= 200 mg/dL (11.1 mmol/L) during a 75-g oral glucose tolerance test.\n• Glycated Hemoglobin (HbA1c) >= 6.5% (48 mmol/mol) via certified NGSP assay.\n• Random Plasma Glucose >= 200 mg/dL with classic hyperglycemic symptoms.',
          'Prediabetes is defined as FPG 100-125 mg/dL, 2-hr PG 140-199 mg/dL, or HbA1c 5.7%-6.4%. Lifestyle intervention and Metformin consideration are recommended.',
        ],
        col2Paragraphs: [
          'Individualized Glycemic Targets:\n• Standard Target: HbA1c < 7.0% (53 mmol/mol) for most non-pregnant adults to prevent microvascular complications.\n• Stringent Target (< 6.5%): For younger patients with short disease duration and no cardiovascular disease, without causing hypoglycemia.\n• Relaxed Target (< 8.0%): For patients with severe hypoglycemia history, limited life expectancy, or advanced complications.',
          'Foundational lifestyle management requires >= 150 minutes/week of moderate aerobic exercise and structured medical nutrition therapy.',
        ],
      },
      2: {
        headerJournal: 'Diabetes Care (2026) 49 (Suppl. 1):S1-S270',
        sectionTitle: 'Section 2: First-Line Pharmacotherapy: Metformin & Renal Precautions',
        col1Paragraphs: [
          'Metformin (biguanide) remains the established foundational first-line agent for type 2 diabetes. It reduces hepatic gluconeogenesis and improves peripheral insulin sensitivity via AMPK activation.',
          'Dosing Protocol: Initiate immediate-release Metformin at 500 mg orally once or twice daily with meals. Titrate weekly by 500 mg to target 1000 mg twice daily (or Extended-Release 2000 mg once daily with dinner) to mitigate gastrointestinal side effects.',
        ],
        col2Paragraphs: [
          'Renal Function & eGFR Thresholds:\n• eGFR >= 60 mL/min/1.73m2: Full dose safe (up to 2000-2550 mg/day).\n• eGFR 45-59 mL/min/1.73m2: Continue therapy; monitor eGFR every 3-6 months.\n• eGFR 30-44 mL/min/1.73m2: Dose reduction recommended (max 1000 mg daily). Do not initiate in treatment-naive patients.\n• eGFR < 30 mL/min/1.73m2: Strictly Contraindicated. Discontinue immediately due to high risk of fatal lactic acidosis.',
          'Periodic serum vitamin B12 testing is recommended every 2 to 3 years to monitor for Metformin-induced B12 deficiency.',
        ],
        table: {
          title: 'Table 1: Metformin eGFR Dosing & Renal Safety Protocol',
          rows: [
            { label: 'eGFR >= 60 mL/min', value: 'Full dose (up to 2000 mg daily)' },
            { label: 'eGFR 45 to 59 mL/min', value: 'Maintain dose, monitor renal panel q3-6m' },
            { label: 'eGFR 30 to 44 mL/min', value: 'Reduce dose (maximum 1000 mg daily)' },
            { label: 'eGFR < 30 mL/min', value: 'STRICTLY CONTRAINDICATED (Discontinue immediately)' },
          ],
        },
      },
      3: {
        headerJournal: 'Diabetes Care (2026) 49 (Suppl. 1):S1-S270',
        sectionTitle: 'Section 3: Cardiorenal Protection: SGLT2 Inhibitors & GLP-1 RAs',
        col1Paragraphs: [
          'In patients with established ASCVD, Heart Failure, or Chronic Kidney Disease, SGLT2 inhibitors or GLP-1 receptor agonists with proven benefit are recommended regardless of baseline HbA1c or Metformin use.',
          'SGLT2 Inhibitors (Empagliflozin 10-25 mg daily, Dapagliflozin 10 mg daily): Preferred in Heart Failure (HFrEF/HFpEF) and CKD (eGFR 20-60 mL/min with albuminuria). Proven reduction in HF hospitalizations and CKD progression.',
        ],
        col2Paragraphs: [
          'GLP-1 Receptor Agonists (Semaglutide 0.25 to 2.0 mg SC weekly, Dulaglutide 0.75 to 4.5 mg weekly): Preferred in established ASCVD (prior MI, stroke, revascularization) and where robust weight loss is needed.',
          'Dual GIP/GLP-1 receptor agonist Tirzepatide (5 to 15 mg weekly) provides superior glycemic reduction and weight loss.',
        ],
        table: {
          title: 'Table 2: Cardiorenal Risk-Based Drug Selection',
          rows: [
            { label: 'Heart Failure (HFrEF/HFpEF)', value: 'SGLT2i preferred (Empagliflozin / Dapagliflozin)' },
            { label: 'Chronic Kidney Disease', value: 'SGLT2i (eGFR >= 20) or GLP-1 RA if contraindicated' },
            { label: 'Established ASCVD', value: 'GLP-1 RA or SGLT2i with proven cardiovascular reduction' },
            { label: 'High Weight Loss Need', value: 'Tirzepatide or Semaglutide subcutaneous' },
          ],
        },
      },
      4: {
        headerJournal: 'Diabetes Care (2026) 49 (Suppl. 1):S1-S270',
        sectionTitle: 'Section 4: Basal Insulin Initiation & The Rule of 15 Protocol',
        col1Paragraphs: [
          'Basal Insulin Initiation: Initiate Insulin Glargine or Degludec at 10 units once daily or 0.1-0.2 units/kg/day. Self-titrate by increasing dose by 2 units every 3 days until fasting glucose reaches 80-130 mg/dL without hypoglycemia. Reduce dose by 10-20% if fasting glucose < 70 mg/dL.',
        ],
        col2Paragraphs: [
          'The Rule of 15 Hypoglycemia Protocol:\n1. Ingest 15-20 grams of fast-acting carbohydrate (4 glucose tablets or 1/2 cup juice).\n2. Recheck blood glucose in exactly 15 minutes.\n3. If blood glucose remains < 70 mg/dL, repeat 15 grams of glucose.\n4. Once normalized, consume a complex carbohydrate and protein snack.',
        ],
        table: {
          title: 'Table 3: Hypoglycemia Severity Classification',
          rows: [
            { label: 'Level 1 Hypoglycemia', value: 'Glucose 54 - 69 mg/dL (Alert value: apply Rule of 15)' },
            { label: 'Level 2 Hypoglycemia', value: 'Glucose < 54 mg/dL (Clinically significant)' },
            { label: 'Level 3 Hypoglycemia', value: 'Severe cognitive impairment requiring external assistance' },
          ],
        },
      },
    },
  },
  hypertension: {
    id: 'hypertension',
    domain: 'hypertension',
    title: '2026 ACC/AHA Practice Guideline for the Prevention and Management of High Blood Pressure',
    shortTitle: 'ACC/AHA High Blood Pressure Guideline (2026)',
    specialty: 'Cardiovascular',
    totalPages: 4,
    pages: {
      1: {
        headerJournal: 'Hypertension & JACC (2026) 83:1200-1285',
        sectionTitle: 'Section 1: BP Classification, Measurement & Universal Targets',
        col1Paragraphs: [
          'Blood pressure categories based on >= 2 automated oscillometric office readings:\n• Normal BP: Systolic < 120 mmHg AND Diastolic < 80 mmHg.\n• Elevated BP: Systolic 120-129 mmHg AND Diastolic < 80 mmHg.\n• Stage 1 Hypertension: Systolic 130-139 mmHg OR Diastolic 80-89 mmHg.\n• Stage 2 Hypertension: Systolic >= 140 mmHg OR Diastolic >= 90 mmHg.\n• Hypertensive Crisis: Systolic > 180 mmHg and/or Diastolic > 120 mmHg.',
        ],
        col2Paragraphs: [
          'Universal BP Target: A target of < 130/80 mmHg is recommended for all non-pregnant adults with confirmed hypertension, including those with Diabetes, CKD, or Age >= 65 years (Class I, Level A).',
          'Stage 2 Hypertension mandates immediate initiation of combination pharmacotherapy with TWO first-line agents of different classes.',
        ],
      },
      2: {
        headerJournal: 'Hypertension & JACC (2026) 83:1200-1285',
        sectionTitle: 'Section 2: First-Line Antihypertensive Classes & Dosages',
        col1Paragraphs: [
          'Four primary drug classes have demonstrated equivalence in reducing major cardiovascular events:\n1. ACE Inhibitors (Lisinopril 10-40 mg daily, Enalapril 5-40 mg daily).\n2. Angiotensin II Receptor Blockers (Losartan 50-100 mg daily, Valsartan 80-320 mg daily).\n3. Dihydropyridine CCBs (Amlodipine 5-10 mg daily) — first-line in Black adults.\n4. Thiazide Diuretics (Chlorthalidone 12.5-25 mg daily, preferred over HCTZ).',
        ],
        col2Paragraphs: [
          'Adverse Effects & Precautions:\n• ACEi: Dry cough (bradykinin mediated), hyperkalemia, angioedema. Contraindicated in pregnancy.\n• ARBs: Preferred alternative if ACEi cough occurs.\n• CCBs: Dose-dependent peripheral ankle edema.\n• Diuretics: Hypokalemia, hyponatremia, hyperuricemia (gout).',
        ],
        table: {
          title: 'Table 1: First-Line Antihypertensive Dosages',
          rows: [
            { label: 'Lisinopril (ACEi)', value: '10 - 40 mg once daily (Monitor K+ and Cr)' },
            { label: 'Losartan (ARB)', value: '50 - 100 mg once daily (Alternative to ACEi)' },
            { label: 'Amlodipine (CCB)', value: '5 - 10 mg once daily (First-line in Black adults)' },
            { label: 'Chlorthalidone (Diuretic)', value: '12.5 - 25 mg once daily (Preferred over HCTZ)' },
          ],
        },
      },
      3: {
        headerJournal: 'Hypertension & JACC (2026) 83:1200-1285',
        sectionTitle: 'Section 3: Combination Strategies & Resistant Hypertension',
        col1Paragraphs: [
          'Combination Therapy: In Stage 2 hypertension, initiate two first-line agents, preferably in a single-pill fixed-dose combination (e.g. Lisinopril + Amlodipine, or Losartan + Chlorthalidone). Dual RAAS blockade (ACEi + ARB) is strictly contraindicated due to hyperkalemia and acute kidney injury risks.',
        ],
        col2Paragraphs: [
          'Resistant Hypertension: Defined as blood pressure above target (> 130/80 mmHg) despite adherence to optimal doses of 3 antihypertensive classes including a diuretic.\n• Step 4 Therapy: Spironolactone (25-50 mg daily) is the drug of choice. Baseline serum potassium must be < 4.5 mEq/L and eGFR >= 30 mL/min/1.73m2.',
        ],
        table: {
          title: 'Table 2: Stepped Care in Resistant Hypertension',
          rows: [
            { label: 'Step 1-3 Baseline', value: 'Triple therapy: ACEi/ARB + CCB + Chlorthalidone' },
            { label: 'Step 4 Add-on', value: 'Spironolactone 25 - 50 mg daily (Drug of Choice)' },
            { label: 'Safety Threshold', value: 'Serum K+ < 4.5 mEq/L and eGFR >= 30 mL/min' },
          ],
        },
      },
      4: {
        headerJournal: 'Hypertension & JACC (2026) 83:1200-1285',
        sectionTitle: 'Section 4: Hypertensive Crises: Emergency vs Urgency Protocols',
        col1Paragraphs: [
          'Hypertensive Emergency: Severe BP elevation (> 180/120 mmHg) WITH acute target organ damage (ACS, pulmonary edema, aortic dissection, encephalopathy, acute stroke).\n• Immediate ICU admission with continuous IV infusions (Nicardipine 5-15 mg/h or Labetalol 20-80 mg IV).\n• Reduce MAP by no more than 20-25% in the first hour to avoid cerebral ischemia, then toward 160/100 mmHg over 2-6 hours.',
        ],
        col2Paragraphs: [
          'Hypertensive Urgency: Severe BP elevation WITHOUT acute end-organ damage.\n• Manage in outpatient or observation setting with oral antihypertensives (oral Captopril, Labetalol, or Amlodipine).\n• Rapid IV blood pressure reduction is hazardous and contraindicated.',
        ],
      },
    },
  },
  copd: {
    id: 'copd',
    domain: 'copd',
    title: '2026 GOLD Global Strategy for the Diagnosis and Management of COPD',
    shortTitle: 'GOLD Strategy for COPD (2026)',
    specialty: 'Pulmonology',
    totalPages: 3,
    pages: {
      1: {
        headerJournal: 'Am J Respir Crit Care Med (2026) 213:450-512',
        sectionTitle: 'Section 1: Diagnosis, Spirometry Criteria & ABE Assessment',
        col1Paragraphs: [
          'A post-bronchodilator FEV1/FVC ratio < 0.70 is mandatory to confirm persistent airflow limitation.',
          'GOLD Spirometric Grading (post-BD FEV1 % predicted):\n• GOLD 1 (Mild): FEV1 >= 80%\n• GOLD 2 (Moderate): 50% <= FEV1 < 80%\n• GOLD 3 (Severe): 30% <= FEV1 < 50%\n• GOLD 4 (Very Severe): FEV1 < 30%',
        ],
        col2Paragraphs: [
          'The ABE Assessment Tool combines symptoms and exacerbation history:\n• Group A: 0-1 moderate exacerbations (no hospitalization), low symptoms (mMRC 0-1, CAT < 10).\n• Group B: 0-1 moderate exacerbations, high symptoms (mMRC >= 2, CAT >= 10).\n• Group E: >= 2 moderate exacerbations or >= 1 leading to hospital admission.',
        ],
      },
      2: {
        headerJournal: 'Am J Respir Crit Care Med (2026) 213:450-512',
        sectionTitle: 'Section 2: Maintenance Bronchodilation & Inhaled Corticosteroids',
        col1Paragraphs: [
          'Dual Bronchodilation (LABA + LAMA): Dual therapy with a LAMA (Tiotropium 18 mcg or 5 mcg daily) plus LABA (Formoterol 12 mcg bid) is superior to monotherapy and is recommended as initial maintenance therapy for Groups B and E.',
          'Fixed-dose combinations: Umeclidinium/Vilanterol (62.5/25 mcg once daily) or Tiotropium/Olodaterol (5/5 mcg once daily).',
        ],
        col2Paragraphs: [
          'Inhaled Corticosteroid (ICS) Guidance:\n• Blood Eosinophils >= 300 cells/uL: Strong recommendation for triple therapy (LABA + LAMA + ICS).\n• Blood Eosinophils 100 to 299 cells/uL with >= 2 exacerbations/year: Consider ICS addition.\n• Blood Eosinophils < 100 cells/uL: ICS is NOT recommended due to lack of efficacy and increased pneumonia risk.',
        ],
        table: {
          title: 'Table 1: GOLD Maintenance Pharmacotherapy Matrix',
          rows: [
            { label: 'Group A', value: 'Single bronchodilator (SABA or LABA)' },
            { label: 'Group B', value: 'LABA + LAMA dual bronchodilation' },
            { label: 'Group E (Eos < 300)', value: 'LABA + LAMA dual bronchodilation' },
            { label: 'Group E (Eos >= 300)', value: 'LABA + LAMA + ICS triple therapy' },
          ],
        },
      },
      3: {
        headerJournal: 'Am J Respir Crit Care Med (2026) 213:450-512',
        sectionTitle: 'Section 3: Acute Exacerbations, Corticosteroids & Oxygen Targets',
        col1Paragraphs: [
          'Acute Exacerbation Management: Oral Prednisone 40 mg once daily for 5 days is recommended. Courses longer than 5 days do not improve outcomes and increase adverse effects.',
          'Antibiotics (Amoxicillin-Clavulanate 875/125 mg bid for 5-7 days) are indicated if all three cardinal symptoms (dyspnea, sputum volume, purulent sputum) are present.',
        ],
        col2Paragraphs: [
          'Controlled Oxygen Therapy: Supplemental oxygen should be titrated to achieve a target oxygen saturation (SpO2) of 88% to 92% in patients at risk of hypercapnic respiratory failure.',
          'CAUTION: Excessive hyperoxia blunts hypoxic drive and worsens V/Q mismatch.',
          'BiPAP (non-invasive ventilation) is first-line for acute hypercapnic respiratory failure (pH < 7.35 and PaCO2 > 45 mmHg).',
        ],
      },
    },
  },
  pneumonia: {
    id: 'pneumonia',
    domain: 'pneumonia',
    title: '2026 IDSA/ATS Guideline for Community-Acquired Pneumonia (CAP)',
    shortTitle: 'IDSA/ATS CAP Guideline (2026)',
    specialty: 'Infectious Disease',
    totalPages: 3,
    pages: {
      1: {
        headerJournal: 'Clin Infect Dis & Am J Respir Crit Care Med (2026) 72:e1-e48',
        sectionTitle: 'Section 1: Clinical Diagnosis & CURB-65 Risk Stratification',
        col1Paragraphs: [
          'Community-Acquired Pneumonia (CAP) requires radiographic demonstration of pulmonary infiltrate accompanied by acute clinical features including fever, cough, purulent sputum, dyspnea, and focal crackles.',
          'CURB-65 Risk Score (1 point each):\n• C: Confusion (abbreviated mental score <= 8)\n• U: BUN > 19 mg/dL (urea > 7 mmol/L)\n• R: Respiratory rate >= 30 breaths/min\n• B: BP (Systolic < 90 mmHg or Diastolic <= 60 mmHg)\n• 65: Age >= 65 years',
        ],
        col2Paragraphs: [
          'Site-of-Care Decisions:\n• Score 0 or 1: Low risk (mortality < 1.5%) — Outpatient management.\n• Score 2: Moderate risk (mortality 9.2%) — Inpatient hospital admission.\n• Score 3 to 5: High risk (mortality 15-40%) — Urgent hospital admission; scores 4-5 require ICU evaluation.',
        ],
        table: {
          title: 'Table 1: CURB-65 Triage & Mortality Score',
          rows: [
            { label: 'Score 0 - 1', value: 'Outpatient management (Mortality < 1.5%)' },
            { label: 'Score 2', value: 'Inpatient hospital admission (Mortality ~9%)' },
            { label: 'Score 3', value: 'Inpatient admission (Mortality ~17%)' },
            { label: 'Score 4 - 5', value: 'ICU admission indicated (Mortality up to 40%)' },
          ],
        },
      },
      2: {
        headerJournal: 'Clin Infect Dis & Am J Respir Crit Care Med (2026) 72:e1-e48',
        sectionTitle: 'Section 2: Empiric Antimicrobial Regimens: Outpatient vs Inpatient',
        col1Paragraphs: [
          'Outpatient Therapy:\n• Without comorbidities: Amoxicillin 1000 mg orally TID for 5 days (preferred Class I), or Doxycycline 100 mg orally BID for 5 days.\n• With comorbidities (heart, lung, liver, renal disease, diabetes): Amoxicillin-Clavulanate 875/125 mg BID PLUS Azithromycin 500 mg day 1, then 250 mg daily; or Levofloxacin 750 mg daily monotherapy.',
        ],
        col2Paragraphs: [
          'Inpatient Ward Therapy (Non-Severe):\n• Combination: Ampicillin-Sulbactam 1.5-3g IV q6h OR Ceftriaxone 1-2g IV daily PLUS Azithromycin 500 mg IV/oral daily.\n• Duration: A minimum of 5 days; patient must be afebrile for >= 48 hours and clinically stable before discontinuation.',
        ],
      },
      3: {
        headerJournal: 'Clin Infect Dis & Am J Respir Crit Care Med (2026) 72:e1-e48',
        sectionTitle: 'Section 3: Severe CAP & MRSA / Pseudomonas Coverage',
        col1Paragraphs: [
          'Empiric MRSA coverage (Vancomycin 15 mg/kg IV q12h or Linezolid 600 mg IV q12h) and anti-pseudomonal coverage (Piperacillin-Tazobactam 4.5g IV q6h, Cefepime 2g IV q8h, or Meropenem 1g IV q8h) are indicated ONLY if the patient has prior respiratory isolation of the pathogen or recent hospitalization with parenteral antibiotics within 90 days.',
        ],
        col2Paragraphs: [
          'Severe CAP (ICU criteria): Requires either 1 major criterion (invasive mechanical ventilation or septic shock with vasopressors) OR at least 3 minor criteria (respiratory rate >= 30, PaO2/FiO2 <= 250, multilobar infiltrates, confusion, BUN >= 20, leukopenia, thrombocytopenia, hypothermia, hypotension).',
        ],
      },
    },
  },
};

export function detectGuidelineDomain(
  titleOrFilename?: string
): 'afib' | 'diabetes' | 'hypertension' | 'copd' | 'pneumonia' {
  if (!titleOrFilename) return 'afib';
  const text = titleOrFilename.toLowerCase();
  if (text.includes('diabet') || text.includes('ada') || text.includes('endocrin')) return 'diabetes';
  if (text.includes('hypertens') || text.includes('blood pressure') || text.includes('htn')) return 'hypertension';
  if (text.includes('copd') || text.includes('gold') || text.includes('pulmon')) return 'copd';
  if (text.includes('pneumon') || text.includes('cap') || text.includes('infect')) return 'pneumonia';
  return 'afib';
}
