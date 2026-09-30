"""
Generates synthetic clinical guideline PDF for testing layout detection,
multi-column reading order, table extraction, and chunking.
"""
from pathlib import Path
import pymupdf

def generate_sample_afib_guideline(output_path: str):
    doc = pymupdf.open()

    # --------------------------------------------------------------------------
    # Page 1: 2-Column Clinical Guideline
    # --------------------------------------------------------------------------
    page1 = doc.new_page(width=595, height=842)  # A4 size

    # Full-width Title banner
    title_rect = pymupdf.Rect(40, 40, 555, 90)
    page1.insert_textbox(
        title_rect,
        "2026 CLINICAL PRACTICE GUIDELINE FOR ATRIAL FIBRILLATION\n"
        "AHA / ACC / HRS Task Force on Clinical Knowledge & Decision Support",
        fontsize=14,
        fontname="helv",
        color=(0.1, 0.2, 0.4),
        align=pymupdf.TEXT_ALIGN_CENTER
    )

    # Column 1 (Left: x0=40, x1=285)
    col1_rect = pymupdf.Rect(40, 110, 285, 780)
    col1_text = (
        "1. INTRODUCTION AND EPIDEMIOLOGY\n"
        "Atrial fibrillation (AF) is the most common sustained cardiac arrhythmia encountered in "
        "clinical practice. The lifetime risk of developing AF is approximately 1 in 3 in individuals "
        "of European ancestry. AF is associated with a 5-fold increased risk of ischemic stroke and a "
        "3-fold increased risk of heart failure. Early rhythm control and comprehensive stroke "
        "prevention are paramount.\n\n"
        "2. DIAGNOSTIC WORKUP\n"
        "Diagnosis requires documentation of irregular supraventricular rhythm without distinct P waves "
        "on a standard 12-lead ECG or rhythm strip persisting for at least 30 seconds. Initial evaluation "
        "should include transthoracic echocardiography (TTE), serum thyroid-stimulating hormone (TSH), "
        "complete blood count, and renal function panel."
    )
    page1.insert_textbox(col1_rect, col1_text, fontsize=9.5, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)

    # Column 2 (Right: x0=310, x1=555)
    col2_rect = pymupdf.Rect(310, 110, 555, 780)
    col2_text = (
        "3. STROKE RISK STRATIFICATION\n"
        "The CHA2DS2-VASc score is recommended for assessment of thromboembolic stroke risk in non-valvular "
        "AF. Points are assigned for Congestive heart failure (1), Hypertension (1), Age >= 75 (2), "
        "Diabetes mellitus (1), Prior Stroke or TIA (2), Vascular disease (1), Age 65-74 (1), and Sex "
        "category female (1). Anticoagulation is strongly recommended for males with score >= 2 and "
        "females with score >= 3.\n\n"
        "4. FIRST-LINE ANTICOAGULATION\n"
        "Direct oral anticoagulants (DOACs) are recommended in preference to warfarin due to lower rates "
        "of intracranial hemorrhage. Recommended options include Apixaban 5 mg orally twice daily, "
        "Dabigatran 150 mg orally twice daily, or Rivaroxaban 20 mg orally once daily with the evening meal."
    )
    page1.insert_textbox(col2_rect, col2_text, fontsize=9.5, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)

    # --------------------------------------------------------------------------
    # Page 2: Dosage Table and Rate Control Recommendations
    # --------------------------------------------------------------------------
    page2 = doc.new_page(width=595, height=842)

    # Section 5 Heading
    page2.insert_text((40, 60), "5. RECOMMENDED ORAL ANTICOAGULANTS IN NON-VALVULAR AF", fontsize=11, fontname="helv")

    # Draw Table
    # Table headers & rows
    table_rect = pymupdf.Rect(40, 80, 555, 230)
    # Draw table bounding box and gridlines
    page2.draw_rect(table_rect, color=(0.7, 0.7, 0.7), width=1)
    page2.draw_line((40, 110), (555, 110), color=(0.4, 0.4, 0.4), width=1)
    page2.draw_line((40, 150), (555, 150), color=(0.8, 0.8, 0.8), width=0.5)
    page2.draw_line((40, 190), (555, 190), color=(0.8, 0.8, 0.8), width=0.5)

    # Vertical column lines
    page2.draw_line((130, 80), (130, 230), color=(0.8, 0.8, 0.8), width=0.5)
    page2.draw_line((220, 80), (220, 230), color=(0.8, 0.8, 0.8), width=0.5)
    page2.draw_line((310, 80), (310, 230), color=(0.8, 0.8, 0.8), width=0.5)
    page2.draw_line((440, 80), (440, 230), color=(0.8, 0.8, 0.8), width=0.5)

    # Table Text
    page2.insert_text((45, 100), "Drug Name", fontsize=9, fontname="helv")
    page2.insert_text((135, 100), "Standard Dosage", fontsize=9, fontname="helv")
    page2.insert_text((225, 100), "Frequency", fontsize=9, fontname="helv")
    page2.insert_text((315, 100), "Dose Reduction", fontsize=9, fontname="helv")
    page2.insert_text((445, 100), "Renal Elimination", fontsize=9, fontname="helv")

    # Row 1: Apixaban
    page2.insert_text((45, 135), "Apixaban", fontsize=9, fontname="helv")
    page2.insert_text((135, 135), "5 mg oral", fontsize=9, fontname="helv")
    page2.insert_text((225, 135), "Twice daily", fontsize=9, fontname="helv")
    page2.insert_text((315, 135), "2.5 mg BID if 2+ criteria", fontsize=9, fontname="helv")
    page2.insert_text((445, 135), "27% Renal", fontsize=9, fontname="helv")

    # Row 2: Rivaroxaban
    page2.insert_text((45, 175), "Rivaroxaban", fontsize=9, fontname="helv")
    page2.insert_text((135, 175), "20 mg oral", fontsize=9, fontname="helv")
    page2.insert_text((225, 175), "Once daily", fontsize=9, fontname="helv")
    page2.insert_text((315, 175), "15 mg QD if CrCl < 50", fontsize=9, fontname="helv")
    page2.insert_text((445, 175), "66% Renal", fontsize=9, fontname="helv")

    # Row 3: Dabigatran
    page2.insert_text((45, 215), "Dabigatran", fontsize=9, fontname="helv")
    page2.insert_text((135, 215), "150 mg oral", fontsize=9, fontname="helv")
    page2.insert_text((225, 215), "Twice daily", fontsize=9, fontname="helv")
    page2.insert_text((315, 215), "75 mg BID if CrCl < 30", fontsize=9, fontname="helv")
    page2.insert_text((445, 215), "80% Renal", fontsize=9, fontname="helv")

    # Bottom columns on Page 2
    col1_p2 = pymupdf.Rect(40, 260, 285, 780)
    col1_p2_text = (
        "6. RATE CONTROL PHARMACOTHERAPY\n"
        "Beta-blockers (such as Metoprolol succinate 50-200 mg once daily or Bisoprolol 5-10 mg once daily) "
        "or non-dihydropyridine calcium channel blockers (such as Diltiazem 120-360 mg once daily) are "
        "recommended as first-line agents to control ventricular response in AF patients with preserved LVEF. "
        "Digoxin is recommended as a secondary agent when beta-blockers are insufficient or contraindicated."
    )
    page2.insert_textbox(col1_p2, col1_p2_text, fontsize=9.5, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)

    col2_p2 = pymupdf.Rect(310, 260, 555, 780)
    col2_p2_text = (
        "7. RHYTHM CONTROL AND ABLATION\n"
        "Antiarrhythmic drugs (such as Flecainide 50-150 mg twice daily in patients without structural heart "
        "disease, or Amiodarone 200 mg once daily in patients with heart failure) are effective for "
        "sinus rhythm maintenance. Catheter ablation is indicated as first-line therapy in selected young "
        "symptomatic patients or when antiarrhythmic pharmacotherapy fails."
    )
    page2.insert_textbox(col2_p2, col2_p2_text, fontsize=9.5, fontname="helv", align=pymupdf.TEXT_ALIGN_LEFT)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()
    print(f"Generated sample AFib guideline PDF at: {output_path}")

if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    generate_sample_afib_guideline(str(out_file))
